"""Stage 4 - validate against the solver, then package for serving.

Two closing steps of the lifecycle:

* **Validation**: ValidationMetricsProcess compares the deployed
  prediction against a fresh real solve on a small held-out sweep and
  writes the metrics to JSON - the numbers quoted in the README come from
  this file, not from anywhere hand-typed.

* **Serving export**: the surrogate leaves the Python world. An FNO
  cannot go directly - its spectral convolutions run on FFTs
  (`aten::fft_rfftn`), which no ONNX opset supports, and both torch
  exporters refuse it. The standard answer is distillation: a small
  ONNX-friendly convolutional *student* is trained to reproduce the FNO
  teacher's outputs, checked for parity through an ONNX Runtime session
  (the exact runtime a C++/Triton deployment uses), and laid out as a
  Triton model repository - the directory a
  `tritonserver --model-repository=...` instance serves as-is, and the
  application's TritonInferenceProcess (or any HTTP/gRPC client) calls.

Run time: under a minute.
"""

import json
import pathlib

import numpy
import torch
from matplotlib import pyplot

import KratosMultiphysics as Kratos
from KratosMultiphysics.PhysicsNeMoApplication import grid_inference_process
from KratosMultiphysics.PhysicsNeMoApplication import model_registry
from KratosMultiphysics.PhysicsNeMoApplication import onnx_bridge
from KratosMultiphysics.PhysicsNeMoApplication import triton_export
from KratosMultiphysics.PhysicsNeMoApplication import validation_metrics_process

import thermal_plate

OUTPUT = pathlib.Path("output")
DATA = pathlib.Path("..") / "data"

VALIDATION_CASES = 6
VALIDATION_SEED = 777  # disjoint from the training seed by construction


def _DeploySettings() -> Kratos.Parameters:
    return Kratos.Parameters("""{
        "Parameters": {
            "model_part_name" : "ThermalModelPart",
            "model_settings"  : {
                "checkpoint_file" : "output/thermal_fno.mdlus",
                "checkpoint_type" : "physicsnemo",
                "device"          : "auto"
            },
            "input_fields"    : [ { "variable_name" : "CONDUCTIVITY", "data_location" : "node_historical" },
                                  { "variable_name" : "HEAT_FLUX",    "data_location" : "node_historical" } ],
            "output_fields"   : [ { "variable_name" : "NODAL_PAUX",   "data_location" : "node_non_historical" } ],
            "grid_shape"      : [32, 32, 2],
            "bounding_box"    : [0.0, 0.0, -0.05, 1.0, 1.0, 0.05]
        }
    }""")


def main():
    OUTPUT.mkdir(exist_ok=True)
    DATA.mkdir(exist_ok=True)
    Kratos.Logger.GetDefaultOutput().SetSeverity(Kratos.Logger.Severity.WARNING)

    # ---- validation sweep: deploy + real solve + ValidationMetricsProcess --
    rows = []
    for case in thermal_plate.SampleCases(VALIDATION_CASES, VALIDATION_SEED):
        model, model_part = thermal_plate.Solve(**case)
        for node in model_part.Nodes:
            node.SetValue(Kratos.NODAL_PAUX, 0.0)
        process = grid_inference_process.Factory(_DeploySettings(), model)
        model_part.ProcessInfo[Kratos.STEP] = 1
        process.ExecuteFinalizeSolutionStep()

        metrics = validation_metrics_process.Factory(Kratos.Parameters("""{
            "Parameters": {
                "model_part_name"     : "ThermalModelPart",
                "list_of_comparisons" : [{
                    "predicted_variable" : "NODAL_PAUX",
                    "predicted_location" : "node_non_historical",
                    "reference_variable" : "TEMPERATURE",
                    "reference_location" : "node_historical",
                    "metrics"            : ["rmse", "max_abs_error", "relative_l2"]
                }],
                "output_file"         : "output/validation_metrics.json"
            }
        }"""), model)
        metrics.ExecuteFinalizeSolutionStep()
        metrics.ExecuteFinalize()
        comparison = metrics.history[0]["NODAL_PAUX_vs_TEMPERATURE"]
        rows.append({**case, **comparison})
        print(f"  k={case['conductivity']:.3f} q={case['source_amplitude']:.3f}: "
              f"rmse {comparison['rmse']:.2e}  rel_l2 {comparison['relative_l2']:.3f}")

    with open(OUTPUT / "validation_sweep.json", "w") as handle:
        json.dump(rows, handle, indent=1)

    figure, axis = pyplot.subplots(figsize=(6.6, 3.8))
    axis.bar(range(len(rows)), [row["relative_l2"] for row in rows],
             color="#2980b9", alpha=0.85)
    axis.set_xticks(range(len(rows)),
                    [f"k={row['conductivity']:.2f}\nq={row['source_amplitude']:.2f}"
                     for row in rows], fontsize=8)
    axis.set_ylabel("relative L2 error")
    axis.set_title(f"Held-out validation ({VALIDATION_CASES} unseen cases)")
    axis.grid(True, axis="y", alpha=0.3)
    figure.tight_layout()
    figure.savefig(DATA / "validation_sweep.png", dpi=130)

    # ---- distill the FNO into an ONNX-exportable student ------------------
    # The FNO's spectral convolutions are FFTs (aten::fft_rfftn), which no
    # ONNX opset supports - both torch exporters refuse the model. The
    # serving-format answer is distillation: a plain Conv3d student trained
    # to reproduce the teacher's outputs on the training inputs.
    fno, _ = model_registry.LoadModel(Kratos.Parameters("""{
        "checkpoint_file" : "output/thermal_fno.mdlus",
        "checkpoint_type" : "physicsnemo",
        "device"          : "cpu"
    }"""))
    fno.eval()

    grids = torch.from_numpy(numpy.load(OUTPUT / "thermal_dataset.npz")["inputs"]).float()
    with torch.no_grad():
        teacher_outputs = fno(grids)

    torch.manual_seed(0)
    student = torch.nn.Sequential(
        torch.nn.Conv3d(2, 24, kernel_size=(5, 5, 1), padding=(2, 2, 0)), torch.nn.GELU(),
        torch.nn.Conv3d(24, 24, kernel_size=(5, 5, 1), padding=(2, 2, 0)), torch.nn.GELU(),
        torch.nn.Conv3d(24, 24, kernel_size=(5, 5, 1), padding=(2, 2, 0)), torch.nn.GELU(),
        torch.nn.Conv3d(24, 1, kernel_size=1))
    optimizer = torch.optim.Adam(student.parameters(), lr=2e-3)
    for step in range(600):
        optimizer.zero_grad()
        loss = torch.nn.functional.mse_loss(student(grids), teacher_outputs)
        loss.backward()
        optimizer.step()
    student.eval()
    with torch.no_grad():
        distill_rmse = float(torch.sqrt(torch.mean(
            (student(grids) - teacher_outputs) ** 2)))
    field_scale = float(teacher_outputs.abs().max())
    print(f"distillation: student-vs-teacher rmse {distill_rmse:.2e} "
          f"(field scale {field_scale:.2e})")

    # ---- ONNX parity for the student --------------------------------------
    sample = grids[:1]
    buffer = pathlib.Path(OUTPUT / "thermal_student.onnx")
    torch.onnx.export(student, (sample,), str(buffer), dynamo=False, opset_version=17)

    session = onnx_bridge.CreateOrtSession(buffer, "cpu")
    input_name = session.get_inputs()[0].name
    onnx_out = session.run(None, {input_name: sample.numpy().astype(numpy.float32)})[0]
    with torch.no_grad():
        torch_out = student(sample).numpy()
    parity = float(numpy.abs(onnx_out - torch_out).max())
    print(f"ONNX parity: max |onnxruntime - torch| = {parity:.2e}")
    assert parity < 1e-5, f"ONNX export does not reproduce the torch forward ({parity:.2e})"

    # ---- Triton repository ------------------------------------------------
    config_file = triton_export.ExportTritonModelRepository(
        student, sample, Kratos.Parameters("""{
            "repository_path" : "output/triton_repository",
            "model_name"      : "thermal_student",
            "model_version"   : 1
        }"""))
    print(f"Triton repository: {config_file}")
    print("serve with: tritonserver --model-repository=output/triton_repository")

    with open(OUTPUT / "export_summary.json", "w") as handle:
        json.dump({"onnx_parity_max_abs": parity,
                   "distill_rmse": distill_rmse,
                   "triton_config": str(config_file),
                   "validation_mean_relative_l2":
                       float(numpy.mean([row["relative_l2"] for row in rows]))},
                  handle, indent=1)
    print(f"figure : {DATA / 'validation_sweep.png'}")


if __name__ == "__main__":
    main()
