"""Stage 3 - deploy the surrogate inside Kratos, governed.

Deployment is where surrogates fail silently, so this stage exercises the
three governance layers trained in Stage 2 on a case the model has never
seen:

1. the **model card** is validated against the process configuration
   (misdeclared fields fail loudly at construction);
2. the **OOD guard** scores the sampled input grid before the model runs -
   demonstrated on a conductivity ramp that walks out of the training
   range;
3. the **ensemble** turns member disagreement into a per-node error bar,
   compared against the *actual* error (which a user without the reference
   solution cannot see).

The surrogate runs through GridInferenceProcess exactly as it would inside
a solver loop: fields are sampled from the model part, the FNO runs, the
prediction is scattered back onto the nodes.

Run time: well under a minute.
"""

import json
import pathlib

import numpy
import torch
from matplotlib import pyplot

import KratosMultiphysics as Kratos
from KratosMultiphysics.PhysicsNeMoApplication import grid_bridge
from KratosMultiphysics.PhysicsNeMoApplication import grid_inference_process
from KratosMultiphysics.PhysicsNeMoApplication import ood_guard_utils

import thermal_plate
import viz

OUTPUT = pathlib.Path("output")
DATA = pathlib.Path("..") / "data"

# unseen, but inside the training distribution (k in [0.5, 2], q in [0.5, 1.5])
TEST_CASE = {"conductivity": 1.6, "source_amplitude": 1.2, "source_center": (0.45, 0.62)}
GRID_SHAPE = (32, 32, 2)
BOUNDING_BOX = (numpy.array([0.0, 0.0, -0.05]), numpy.array([1.0, 1.0, 0.05]))
MEMBER_CHECKPOINTS = ["thermal_fno.mdlus", "thermal_fno_member1.mdlus",
                      "thermal_fno_member2.mdlus"]


def _DeploySettings(checkpoint: str, with_guard: bool) -> Kratos.Parameters:
    guard = ('"ood_guard" : { "guard_file" : "output/thermal_fno.ood_guard.pt", '
             '"policy" : "advisory" },' if with_guard else "")
    return Kratos.Parameters("""{
        "Parameters": {
            "model_part_name" : "ThermalModelPart",
            "model_settings"  : {
                "checkpoint_file" : "output/%s",
                "checkpoint_type" : "physicsnemo",
                "device"          : "auto"
            },
            %s
            "input_fields"    : [ { "variable_name" : "CONDUCTIVITY", "data_location" : "node_historical" },
                                  { "variable_name" : "HEAT_FLUX",    "data_location" : "node_historical" } ],
            "output_fields"   : [ { "variable_name" : "NODAL_PAUX",   "data_location" : "node_non_historical" } ],
            "grid_shape"      : [32, 32, 2],
            "bounding_box"    : [0.0, 0.0, -0.05, 1.0, 1.0, 0.05]
        }
    }""" % (checkpoint, guard))


def main():
    OUTPUT.mkdir(exist_ok=True)
    DATA.mkdir(exist_ok=True)
    Kratos.Logger.GetDefaultOutput().SetSeverity(Kratos.Logger.Severity.WARNING)

    # ---- the reference: one real solve of the unseen case -----------------
    model, model_part = thermal_plate.Solve(**TEST_CASE)
    reference = numpy.array([node.GetSolutionStepValue(Kratos.TEMPERATURE)
                             for node in model_part.Nodes])
    for node in model_part.Nodes:
        node.SetValue(Kratos.NODAL_PAUX, 0.0)

    # ---- ensemble deployment: every member through the real process -------
    predictions = []
    for index, checkpoint in enumerate(MEMBER_CHECKPOINTS):
        process = grid_inference_process.Factory(
            _DeploySettings(checkpoint, with_guard=(index == 0)), model)
        model_part.ProcessInfo[Kratos.STEP] = 1
        process.ExecuteFinalizeSolutionStep()
        predictions.append(numpy.array([node.GetValue(Kratos.NODAL_PAUX)
                                        for node in model_part.Nodes]))
    predictions = numpy.stack(predictions)
    mean = predictions.mean(axis=0)
    spread = predictions.std(axis=0, ddof=1)
    error = numpy.abs(mean - reference)

    rmse = float(numpy.sqrt(numpy.mean((mean - reference) ** 2)))
    print(f"unseen case k={TEST_CASE['conductivity']}, q={TEST_CASE['source_amplitude']}: "
          f"rmse {rmse:.2e}, max |error| {error.max():.2e}, "
          f"max ensemble std {spread.max():.2e}")

    viz.RenderFields(
        model_part,
        [("TEMPERATURE (solver)", reference, "viridis"),
         ("TEMPERATURE (FNO ensemble mean)", mean, "viridis"),
         ("absolute error", error, "magma"),
         ("ensemble std (predicted error bar)", spread, "magma")],
        DATA / "deployment_fields.png",
        shape=(2, 2), clim_share=(0, 1), window_size=(1500, 1500))

    # ---- OOD guard on a conductivity ramp ---------------------------------
    guard = ood_guard_utils.LoadGuard(str(OUTPUT / "thermal_fno.ood_guard.pt"))
    ramp = numpy.linspace(0.25, 5.0, 24)
    flagged = []
    for k in ramp:
        case_model = Kratos.Model()
        case_part = thermal_plate.CreateModelPart(case_model)
        thermal_plate.ApplyCase(case_part, float(k),
                                TEST_CASE["source_amplitude"], TEST_CASE["source_center"])
        grid, _ = grid_bridge.SampleFieldsOnGrid(
            case_part,
            [("CONDUCTIVITY", "node_historical"), ("HEAT_FLUX", "node_historical")],
            GRID_SHAPE, BOUNDING_BOX)
        features = torch.from_numpy(
            grid.reshape(grid.shape[0], -1).T.copy()).to(torch.float32)
        messages = ood_guard_utils.CheckFeatures(guard, features)
        flagged.append(bool(messages))
        print(f"  k = {k:5.2f}: {'FLAGGED OOD' if messages else 'in distribution'}")

    figure, axis = pyplot.subplots(figsize=(7.2, 3.6))
    colors = ["#c0392b" if f else "#27ae60" for f in flagged]
    axis.scatter(ramp, [1 if f else 0 for f in flagged], c=colors, s=48, zorder=3)
    axis.axvspan(0.5, 2.0, alpha=0.15, color="#2980b9",
                 label="training range of k")
    axis.set_yticks([0, 1], ["in distribution", "flagged OOD"])
    axis.set_xlabel("conductivity k fed to the deployed surrogate")
    axis.set_title("OOD guard verdict vs. input conductivity")
    axis.legend()
    axis.grid(True, alpha=0.3)
    figure.tight_layout()
    figure.savefig(DATA / "ood_guard_ramp.png", dpi=130)

    # ---- error bar honesty: does the ensemble spread track the error? -----
    figure, axis = pyplot.subplots(figsize=(5.4, 5.0))
    axis.loglog(spread, error, ".", markersize=3, alpha=0.4)
    limits = [min(spread[spread > 0].min(), error[error > 0].min()),
              max(spread.max(), error.max())]
    axis.loglog(limits, limits, "k--", linewidth=1, label="spread = error")
    axis.set_xlabel("ensemble std per node")
    axis.set_ylabel("actual |error| per node")
    axis.set_title("Predicted error bar vs. actual error")
    axis.legend()
    axis.grid(True, which="both", alpha=0.3)
    figure.tight_layout()
    figure.savefig(DATA / "uncertainty_vs_error.png", dpi=130)

    with open(OUTPUT / "deploy_summary.json", "w") as handle:
        json.dump({"test_case": TEST_CASE, "rmse": rmse,
                   "max_abs_error": float(error.max()),
                   "max_ensemble_std": float(spread.max()),
                   "ood_ramp": {"k": ramp.tolist(), "flagged": flagged}},
                  handle, indent=1)
    print(f"figures: {DATA / 'deployment_fields.png'}, {DATA / 'ood_guard_ramp.png'}, "
          f"{DATA / 'uncertainty_vs_error.png'}")


if __name__ == "__main__":
    main()
