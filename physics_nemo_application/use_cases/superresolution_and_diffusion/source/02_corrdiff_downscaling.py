"""Stage 2 - CorrDiff two-stage diffusion downscaling of real solver fields.

The condition is a genuinely under-resolved SOLVE: the thermal plate on an
8x8 mesh, which flattens and spreads the Gaussian hot spot. The target is
the same case solved on a 32x32 mesh. Both are sampled on the same 16x16
grid, so the model's task is to put back the physics the coarse mesh lost
- classic downscaling, with real discretization error rather than a
synthetic blur.

CorrDiff's two stages: a deterministic regression UNet learns the mean
correction; a diffusion model learns the distribution of the RESIDUAL
around it. At deployment the DiffusionInferenceProcess draws an ensemble,
writes the mean to the output field and the per-node spread to an
uncertainty field - error bars for the downscaling.

Run time: ~4 minutes (64 coarse+fine solves, then two trainings).
"""

import json
import pathlib

import numpy
import torch
from matplotlib import pyplot
from physicsnemo.diffusion.preconditioners import EDMPrecondSuperResolution
from physicsnemo.models.diffusion_unets import CorrDiffRegressionUNet

import KratosMultiphysics as Kratos
from KratosMultiphysics.PhysicsNeMoApplication import diffusion_inference_process
from KratosMultiphysics.PhysicsNeMoApplication import diffusion_utils
from KratosMultiphysics.PhysicsNeMoApplication import grid_bridge
from KratosMultiphysics.PhysicsNeMoApplication import grid_dataset_export_process
from KratosMultiphysics.PhysicsNeMoApplication import training_utils
from KratosMultiphysics.PhysicsNeMoApplication.torch_dataset import CreateGridPairDataset

import thermal_plate

OUTPUT = pathlib.Path("output")
DATA = pathlib.Path("..") / "data"

COARSE_DIVISIONS, FINE_DIVISIONS = 8, 32
GRID_SHAPE = (16, 16, 2)
BOUNDING_BOX = (numpy.array([0.0, 0.0, -0.05]), numpy.array([1.0, 1.0, 0.05]))
TRAIN_CASES = 64
SCALE = 40.0   # temperatures are O(0.025); diffusion training wants O(1) targets


def ExportCase(step, case, divisions, path):
    """One solve exported as grid step files (the datapipe layout)."""
    model, model_part = thermal_plate.Solve(divisions=divisions, **case)
    for node in model_part.Nodes:  # scale to O(1) for the diffusion training
        node.SetSolutionStepValue(
            Kratos.TEMPERATURE,
            SCALE * node.GetSolutionStepValue(Kratos.TEMPERATURE))
    process = grid_dataset_export_process.Factory(Kratos.Parameters("""{
        "Parameters": {
            "model_part_name" : "ThermalModelPart",
            "list_of_fields"  : [ { "variable_name" : "TEMPERATURE", "data_location" : "node_historical" } ],
            "grid_shape"      : [16, 16, 2],
            "bounding_box"    : [0.0, 0.0, -0.05, 1.0, 1.0, 0.05],
            "output_path"     : "%s"
        }
    }""" % path), model)
    process.ExecuteInitialize()
    model_part.ProcessInfo[Kratos.STEP] = step
    model_part.ProcessInfo[Kratos.TIME] = float(step)
    process.ExecuteFinalizeSolutionStep()


def main():
    OUTPUT.mkdir(exist_ok=True)
    DATA.mkdir(exist_ok=True)
    Kratos.Logger.GetDefaultOutput().SetSeverity(Kratos.Logger.Severity.WARNING)

    # ---- dataset: coarse solve = condition, fine solve = target -----------
    for step, case in enumerate(thermal_plate.SampleCases(TRAIN_CASES, seed=11), start=1):
        ExportCase(step, case, COARSE_DIVISIONS, "output/coarse_solves")
        ExportCase(step, case, FINE_DIVISIONS, "output/fine_solves")
        if step % 16 == 0:
            print(f"  exported {step}/{TRAIN_CASES} coarse+fine solve pairs")
    pairs = CreateGridPairDataset("output/coarse_solves", "output/fine_solves",
                                  squeeze_axis=2)

    # ---- the two stages ---------------------------------------------------
    torch.manual_seed(0)
    regression = CorrDiffRegressionUNet(
        img_resolution=16, img_in_channels=1, img_out_channels=1,
        model_type="SongUNet", model_channels=16, channel_mult=[1, 2],
        num_blocks=1, attn_resolutions=[])
    torch.manual_seed(1)
    denoiser = EDMPrecondSuperResolution(
        img_resolution=16, img_in_channels=1 + 4, img_out_channels=1,
        model_type="SongUNetPosEmbd", model_channels=16, channel_mult=[1, 2],
        num_blocks=1, attn_resolutions=[])

    regression_history, diffusion_history = diffusion_utils.TrainCorrDiffPair(
        regression, denoiser, pairs, Kratos.Parameters("""{
            "epochs"                   : 500,
            "regression_epochs"        : 250,
            "batch_size"               : 8,
            "learning_rate"            : 2e-4,
            "regression_learning_rate" : 1e-3,
            "echo_interval"            : 50,
            "seed"                     : 0
        }"""))
    print(f"regression loss: {regression_history[0]:.3e} -> {regression_history[-1]:.3e}")
    print(f"residual   loss: {diffusion_history[0]:.3e} -> {diffusion_history[-1]:.3e}")
    training_utils.SaveTrainedModel(regression, OUTPUT / "corrdiff_regression.mdlus")
    training_utils.SaveTrainedModel(denoiser, OUTPUT / "corrdiff_residual.mdlus")

    # ---- deployment on an unseen case -------------------------------------
    held_out = {"conductivity": 1.3, "source_amplitude": 1.25, "source_center": (0.58, 0.42)}
    model, coarse_part = thermal_plate.Solve(divisions=COARSE_DIVISIONS, **held_out)
    for node in coarse_part.Nodes:
        node.SetSolutionStepValue(
            Kratos.TEMPERATURE, SCALE * node.GetSolutionStepValue(Kratos.TEMPERATURE))
        node.SetValue(Kratos.NODAL_PAUX, 0.0)
        node.SetValue(Kratos.NODAL_ERROR, 0.0)

    process = diffusion_inference_process.Factory(Kratos.Parameters("""{
        "Parameters": {
            "model_part_name"     : "ThermalModelPart",
            "model_settings"      : {
                "checkpoint_file" : "output/corrdiff_residual.mdlus",
                "checkpoint_type" : "physicsnemo"
            },
            "regression_settings" : {
                "checkpoint_file" : "output/corrdiff_regression.mdlus",
                "checkpoint_type" : "physicsnemo"
            },
            "input_fields"        : [ { "variable_name" : "TEMPERATURE", "data_location" : "node_historical" } ],
            "output_fields"       : [ { "variable_name" : "NODAL_PAUX",  "data_location" : "node_non_historical" } ],
            "uncertainty_fields"  : [ { "variable_name" : "NODAL_ERROR", "data_location" : "node_non_historical" } ],
            "grid_shape"          : [16, 16, 2],
            "bounding_box"        : [0.0, 0.0, -0.05, 1.0, 1.0, 0.05],
            "squeeze_axis"        : 2,
            "sampler_settings"    : { "num_samples" : 16, "num_steps" : 18, "seed" : 0 }
        }
    }"""), model)
    coarse_part.ProcessInfo[Kratos.STEP] = 1
    process.ExecuteFinalizeSolutionStep()

    # ---- comparison on the 16x16 grid -------------------------------------
    fine_model, fine_part = thermal_plate.Solve(divisions=FINE_DIVISIONS, **held_out)
    for node in fine_part.Nodes:
        node.SetSolutionStepValue(
            Kratos.TEMPERATURE, SCALE * node.GetSolutionStepValue(Kratos.TEMPERATURE))

    def GridOf(part):
        grid, _ = grid_bridge.SampleFieldsOnGrid(
            part, [("TEMPERATURE", "node_historical")], GRID_SHAPE, BOUNDING_BOX)
        return grid.mean(axis=3)[0]   # squeeze the thin axis -> (16, 16)

    truth = GridOf(fine_part)
    condition = GridOf(coarse_part)
    regression_only = diffusion_utils.RunRegressionMean(regression, condition[None])[0]

    corrdiff_mean = numpy.array(
        [node.GetValue(Kratos.NODAL_PAUX) for node in coarse_part.Nodes])
    spread = numpy.array(
        [node.GetValue(Kratos.NODAL_ERROR) for node in coarse_part.Nodes])
    # nodal truth for the per-node comparison (fine solve at coarse nodes)
    fine_lookup = {(round(node.X, 6), round(node.Y, 6)):
                   node.GetSolutionStepValue(Kratos.TEMPERATURE)
                   for node in fine_part.Nodes}
    nodal_truth = numpy.array([fine_lookup[(round(node.X, 6), round(node.Y, 6))]
                               for node in coarse_part.Nodes])
    nodal_condition = numpy.array([node.GetSolutionStepValue(Kratos.TEMPERATURE)
                                   for node in coarse_part.Nodes])

    def Rmse(a, b):
        return float(numpy.sqrt(numpy.mean((numpy.asarray(a) - numpy.asarray(b)) ** 2)))

    metrics = {
        "grid_rmse_condition": Rmse(condition, truth),
        "grid_rmse_regression": Rmse(regression_only, truth),
        "nodal_rmse_condition": Rmse(nodal_condition, nodal_truth),
        "nodal_rmse_corrdiff_mean": Rmse(corrdiff_mean, nodal_truth),
        "mean_spread": float(spread.mean()),
    }
    print(f"grid rmse: coarse condition {metrics['grid_rmse_condition']:.4f}  "
          f"regression alone {metrics['grid_rmse_regression']:.4f}")
    print(f"nodal rmse: coarse {metrics['nodal_rmse_condition']:.4f}  "
          f"CorrDiff ensemble mean {metrics['nodal_rmse_corrdiff_mean']:.4f}  "
          f"(mean spread {metrics['mean_spread']:.4f})")

    # ---- figure -----------------------------------------------------------
    figure, axes = pyplot.subplots(1, 4, figsize=(16.0, 3.7))
    limits = dict(vmin=float(truth.min()), vmax=float(truth.max()))
    panels = [(condition, "coarse-mesh solve (condition)", "viridis", limits),
              (regression_only, "regression mean", "viridis", limits),
              (truth, "fine-mesh solve (truth)", "viridis", limits)]
    for axis, (plane, title, colormap, kw) in zip(axes[:3], panels):
        image = axis.imshow(plane.T, origin="lower", cmap=colormap, **kw)
        axis.set_title(title, fontsize=10)
        figure.colorbar(image, ax=axis, shrink=0.85)
    spread_grid = spread.reshape(COARSE_DIVISIONS + 1, COARSE_DIVISIONS + 1)
    image = axes[3].imshow(spread_grid.T, origin="lower", cmap="magma")
    axes[3].set_title("ensemble spread (uncertainty)", fontsize=10)
    figure.colorbar(image, ax=axes[3], shrink=0.85)
    figure.suptitle("CorrDiff downscaling of a coarse solve, unseen case")
    figure.tight_layout()
    figure.savefig(DATA / "corrdiff_downscaling.png", dpi=130)

    with open(OUTPUT / "corrdiff_summary.json", "w") as handle:
        json.dump(metrics, handle, indent=1)
    print(f"figure : {DATA / 'corrdiff_downscaling.png'}")


if __name__ == "__main__":
    main()
