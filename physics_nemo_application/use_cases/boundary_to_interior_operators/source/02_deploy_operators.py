"""Both operators deployed in the solution loop, through the same process.

Script 01 trained them; this one runs them where they would actually be
used - attached to a Kratos model part by `PointCloudInferenceProcess`,
writing their predictions into ordinary nodal variables that every
existing exporter and validation process already understands.

The two take different inputs and reach the process through different
settings blocks, which is the point of deploying them side by side:

* **xDeepONet** gets the case PARAMETERS through a `"branch_input"` block.
  Here they are passed as `"constants"`, which is what a worked example
  can do; in production they would come from `"process_info_variables"` or
  `"properties_variables"`, so the running solver supplies them rather
  than the script. The checkpoint is TorchScript, because an xDeepONet
  can be neither saved as `.mdlus` nor scripted - only traced.
* **GLOBE** gets the BOUNDARY through a `"globe"` block naming the
  sub-model-parts, the fields on them and the reference lengths. The
  process caches those boundary meshes per node count, since rebuilding
  them every step would cost more than the inference.

`"normalize_coordinates"` is false for both, and that is not incidental:
the process normalizes coordinates per axis against the cloud's own
bounding box when asked to, and both operators were trained on raw
coordinates. Turning it on here would feed them a unit cube and quietly
produce nonsense - the same normalization that makes the geometry
guardrail case necessary.

The reproducible claim (everything seeded): deployed through the process,
both operators reproduce the held-out interior fields better than the
node-wise mean of the training fields, on every held-out case.

Run from this directory:  python3 02_deploy_operators.py
Outputs: ../data/operators_heldout.png
"""

import json
import pathlib
import sys

import numpy

import KratosMultiphysics as Kratos
import KratosMultiphysics.PhysicsNeMoApplication  # registers the application  # noqa: F401

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import thermal_cube_dirichlet as thermal  # noqa: E402

from KratosMultiphysics.PhysicsNeMoApplication.processes.inference import (  # noqa: E402
    point_cloud_inference_process)

HERE = pathlib.Path(__file__).parent
DATA = HERE.parent / "data"
OUTPUT = HERE / "output"

DIVISIONS = 4
TRAIN_CASES, TEST_CASES = 16, 8


def DeployDeepONet(kratos_model, case, checkpoint):
    """Parameters in, field at the nodes out - no POD basis anywhere."""
    process = point_cloud_inference_process.Factory(Kratos.Parameters('''{
        "Parameters": {
            "model_part_name"       : "ThermalModelPart",
            "model_settings"        : { "checkpoint_file" : "%s",
                                        "checkpoint_type" : "torchscript",
                                        "device" : "cpu" },
            "model_interface"       : "deeponet",
            "normalize_coordinates" : false,
            "trunk_dimension"       : 3,
            "branch_input"          : { "constants" : [%.17g, %.17g, %.17g] },
            "input_fields"          : [
                { "variable_name" : "CONDUCTIVITY", "data_location" : "node_historical" } ],
            "output_fields"         : [
                { "variable_name" : "NODAL_PAUX",   "data_location" : "node_non_historical" } ]
        }
    }''' % (checkpoint, case["center"][0], case["center"][1], case["amplitude"])),
        kratos_model)
    process.ExecuteInitialize()
    process.ExecuteFinalizeSolutionStep()


def DeployGlobe(kratos_model, checkpoint):
    """Boundary data in, interior out - the structure an elliptic problem has."""
    process = point_cloud_inference_process.Factory(Kratos.Parameters('''{
        "Parameters": {
            "model_part_name"          : "ThermalModelPart",
            "model_settings"           : { "checkpoint_file" : "%s",
                                           "checkpoint_type" : "physicsnemo",
                                           "device" : "cpu" },
            "model_interface"          : "globe",
            "normalize_coordinates"    : false,
            "globe"                    : {
                "boundary_sub_model_parts" : ["%s"],
                "boundary_fields"          : [
                    { "variable_name" : "TEMPERATURE", "data_location" : "node_historical",
                      "rank" : 0 } ],
                "reference_lengths"        : { "L" : 1.0 },
                "output_names"             : ["u"],
                "source_container"         : "Conditions"
            },
            "input_fields"             : [
                { "variable_name" : "CONDUCTIVITY", "data_location" : "node_historical" } ],
            "output_fields"            : [
                { "variable_name" : "NODAL_ERROR",  "data_location" : "node_non_historical" } ]
        }
    }''' % (checkpoint, thermal.TOP_BOUNDARY_NAME)), kratos_model)
    process.ExecuteInitialize()
    process.ExecuteFinalizeSolutionStep()


def Render(results, baseline_plane):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure = plt.figure(figsize=(13.0, 6.4), constrained_layout=True)
    grid = figure.add_gridspec(2, 4)

    # One held-out case on a SINGLE horizontal plane. The slice has to be
    # taken explicitly: handing tricontourf every node's (x, y) instead
    # triangulates the whole cube's projection, stacking five different z
    # values on the same point, and the heated top boundary (~1.0) then
    # sets a colour scale that renders the entire interior flat black.
    sample = results[0]
    planes = numpy.unique(numpy.round(sample["z"], 9))
    z_plane = planes[-2]          # the interior plane nearest the heated top
    picked = numpy.abs(sample["z"] - z_plane) < 1e-9

    panels = (("truth", sample["truth"]), ("xDeepONet", sample["deeponet"]),
              ("GLOBE", sample["globe"]), ("mean predictor", baseline_plane))
    # All four panels must share one scale or the comparison is not a
    # comparison. tricontourf does NOT accept vmin/vmax as parameters -
    # they would slide through **kwargs and be ignored - so the shared
    # scale is expressed the way it actually supports: explicit levels
    # spanning every panel's range ON THIS PLANE.
    low = min(float(values[picked].min()) for _, values in panels)
    high = max(float(values[picked].max()) for _, values in panels)
    levels = numpy.linspace(low, high, 15)
    axes = []
    for column, (name, values) in enumerate(panels):
        axis = figure.add_subplot(grid[0, column])
        image = axis.tricontourf(sample["x"][picked], sample["y"][picked],
                                 values[picked], levels=levels,
                                 cmap="inferno", extend="both")
        axis.set_title(name, fontsize=10)
        axis.set_aspect("equal")
        axis.set_xticks([]), axis.set_yticks([])
        axes.append(axis)
    axes[0].set_ylabel(f"held-out case 0\nz = {z_plane:g}", fontsize=9)
    # ONE colourbar for the row - four identical ones would take half the
    # width and say nothing the first does not
    figure.colorbar(image, ax=axes, shrink=0.85, label="temperature")

    axis = figure.add_subplot(grid[1, :])
    index = numpy.arange(len(results))
    axis.bar(index - 0.26, [r["deeponet_rmse"] for r in results], width=0.26,
             label="xDeepONet")
    axis.bar(index, [r["globe_rmse"] for r in results], width=0.26, color="#c0392b",
             label="GLOBE")
    axis.bar(index + 0.26, [r["baseline_rmse"] for r in results], width=0.26,
             color="#7f8c8d", label="mean predictor")
    axis.set_xticks(index), axis.set_xticklabels([f"case {i}" for i in index], fontsize=8)
    axis.set_ylabel("field RMSE"), axis.set_yscale("log")
    axis.set_title("deployed through PointCloudInferenceProcess, on every held-out case",
                   fontsize=9)
    axis.legend(fontsize=8), axis.grid(alpha=0.3, axis="y")

    figure.suptitle("Two operators from a boundary condition to the interior, "
                    "running in the solution loop")
    figure.savefig(DATA / "operators_heldout.png", dpi=130)


if __name__ == "__main__":
    DATA.mkdir(exist_ok=True)
    OUTPUT.mkdir(exist_ok=True)
    Kratos.Logger.GetDefaultOutput().SetSeverity(Kratos.Logger.Severity.WARNING)

    deeponet_file = OUTPUT / "deeponet.pt"
    globe_file = OUTPUT / "globe.mdlus"
    for path in (deeponet_file, globe_file):
        if not path.is_file():
            raise SystemExit("run 01_train_operators.py first (it writes the checkpoints)")

    cases = thermal.SampleCases(TRAIN_CASES + TEST_CASES, seed=0)
    # the baseline is the node-wise mean of the TRAINING fields: the
    # predictor that ignores its input entirely
    kept, training_fields = [], []
    for case in cases[:TRAIN_CASES]:
        model, model_part = thermal.Solve(divisions=DIVISIONS, **case)
        kept.append(model)
        training_fields.append(numpy.array(
            [node.GetSolutionStepValue(Kratos.TEMPERATURE) for node in model_part.Nodes]))
    baseline = numpy.mean(training_fields, axis=0)
    print(f"[data] baseline from {TRAIN_CASES} training fields")

    results = []
    for index, case in enumerate(cases[TRAIN_CASES:]):
        kratos_model, model_part = thermal.Solve(divisions=DIVISIONS, **case)
        truth = numpy.array([node.GetSolutionStepValue(Kratos.TEMPERATURE)
                             for node in model_part.Nodes])

        DeployDeepONet(kratos_model, case, deeponet_file)
        DeployGlobe(kratos_model, globe_file)
        deeponet = numpy.array([node.GetValue(Kratos.NODAL_PAUX)
                                for node in model_part.Nodes])
        globe = numpy.array([node.GetValue(Kratos.NODAL_ERROR)
                             for node in model_part.Nodes])

        rmse = lambda a: float(numpy.sqrt(numpy.mean((a - truth) ** 2)))
        results.append({
            "deeponet_rmse": rmse(deeponet), "globe_rmse": rmse(globe),
            "baseline_rmse": rmse(baseline), "truth": truth,
            "deeponet": deeponet, "globe": globe,
            "x": numpy.array([node.X for node in model_part.Nodes]),
            "y": numpy.array([node.Y for node in model_part.Nodes]),
            "z": numpy.array([node.Z for node in model_part.Nodes]),
        })
        print(f"[eval] held-out case {index}: deeponet {results[-1]['deeponet_rmse']:.4e}  "
              f"globe {results[-1]['globe_rmse']:.4e}  "
              f"mean predictor {results[-1]['baseline_rmse']:.4e}")

    means = {key: float(numpy.mean([r[f"{key}_rmse"] for r in results]))
             for key in ("deeponet", "globe", "baseline")}
    print(f"[eval] means over {len(results)} held-out cases: deeponet "
          f"{means['deeponet']:.4e}, globe {means['globe']:.4e}, "
          f"mean predictor {means['baseline']:.4e}")

    Render(results, baseline)
    with open(OUTPUT / "deployment_summary.json", "w") as handle:
        json.dump({"means": means,
                   "per_case": [{k: r[k] for k in
                                 ("deeponet_rmse", "globe_rmse", "baseline_rmse")}
                                for r in results]}, handle, indent=1)

    # deployed through the process - not just in a training script - both
    # operators must beat the input-ignoring predictor on EVERY held-out
    # case, not merely on average
    for key in ("deeponet", "globe"):
        losers = [i for i, r in enumerate(results) if r[f"{key}_rmse"] >= r["baseline_rmse"]]
        assert not losers, (key, losers, means)
    print("[done] figure at data/operators_heldout.png")
