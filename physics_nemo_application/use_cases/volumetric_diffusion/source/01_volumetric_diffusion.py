"""Volumetric diffusion downscaling: DiffusionUNet3D on real 3D solves.

The `denoiser_interface: "unet3d"` recipe end to end, with no thin-axis
squeeze anywhere:

1. A family of 3D heat-conduction cases (random conductivity, source
   strength and 3D source position) is solved twice each - once on a coarse
   tetrahedral mesh, once on a fine one - and both solutions are sampled
   onto full 16x16x16 voxel grids by the grid bridge.
2. `physicsnemo.experimental.models.diffusion_unets.DiffusionUNet3D`
   (wrapped by `WrapDenoiser(..., "unet3d")`: conditioning goes in natively
   as the TensorDict "volume" key) is trained by `TrainDiffusionModel` -
   which detects the 5-D volumetric batches and swaps in the
   rank-generalized EDM loss, since upstream's hard-codes the 4-D image
   rank.
3. On held-out cases, `GenerateEnsemble` reverse-diffuses an ensemble
   conditioned on the coarse field: the ensemble mean is the downscaled
   prediction, the ensemble spread its uncertainty - compared against the
   fine solve the model never saw.

The reproducible claim (everything seeded): the ensemble mean is closer to
the fine solve than the coarse condition is, on every held-out case.

Run from this directory:  python3 01_volumetric_diffusion.py
Outputs: ../data/volumetric_diffusion.png, ../data/unet3d_downscaler.mdlus
"""

import pathlib
import sys
import warnings

import numpy
import torch

import KratosMultiphysics as Kratos

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import thermal_cube  # noqa: E402

from KratosMultiphysics.PhysicsNeMoApplication.bridges import grid_bridge  # noqa: E402
from KratosMultiphysics.PhysicsNeMoApplication.training import diffusion_utils  # noqa: E402
from KratosMultiphysics.PhysicsNeMoApplication.training import training_utils  # noqa: E402

HERE = pathlib.Path(__file__).parent
DATA = HERE.parent / "data"
DATA.mkdir(exist_ok=True)

GRID_SHAPE = (16, 16, 16)              # powers of 2, as the U-Net requires
BOUNDING_BOX = (numpy.zeros(3), numpy.ones(3))
COARSE_DIVISIONS, FINE_DIVISIONS = 3, 14   # 3 divisions genuinely under-resolves
TRAIN_CASES, TEST_CASES = 28, 3
SIGMA_DATA = 0.5                       # the EDM loss/sampler's data scale


def SampleGrid(model_part) -> numpy.ndarray:
    """(1, 16, 16, 16) float32 TEMPERATURE grid of one solved case."""
    grid, _ = grid_bridge.SampleFieldsOnGrid(
        model_part, [("TEMPERATURE", "node_historical")], GRID_SHAPE, BOUNDING_BOX)
    return grid.astype(numpy.float32)


def BuildDataset():
    cases = thermal_cube.SampleCases(TRAIN_CASES + TEST_CASES, seed=42)
    conditions, targets = [], []
    for index, case in enumerate(cases):
        _, coarse_part = thermal_cube.Solve(divisions=COARSE_DIVISIONS, **case)
        _, fine_part = thermal_cube.Solve(divisions=FINE_DIVISIONS, **case)
        conditions.append(SampleGrid(coarse_part))
        targets.append(SampleGrid(fine_part))
        print(f"[data] case {index + 1}/{len(cases)} solved "
              f"(coarse {COARSE_DIVISIONS}^3 cells, fine {FINE_DIVISIONS}^3 cells)")
    conditions, targets = numpy.stack(conditions), numpy.stack(targets)
    # The de-normalization lesson, in training direction: EDM's loss and
    # sampler assume the data's standard deviation is sigma_data (0.5). A
    # thermal field of std ~5e-3 fed raw would drown under the sampler's own
    # noise - so scale the fields to the EDM contract, and undo it (the
    # SAME factor) on everything reported.
    scale = SIGMA_DATA / float(targets[:TRAIN_CASES].std())
    conditions, targets = conditions * scale, targets * scale
    print(f"[data] fields scaled by {scale:.1f} so std matches sigma_data={SIGMA_DATA}")
    return (conditions[:TRAIN_CASES], targets[:TRAIN_CASES],
            conditions[TRAIN_CASES:], targets[TRAIN_CASES:], scale)


def MakeDenoiser():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")  # physicsnemo.experimental import warning
        from physicsnemo.experimental.models.diffusion_unets import DiffusionUNet3D

    torch.manual_seed(0)
    unet = DiffusionUNet3D(
        x_channels=1, vol_cond_channels=1, num_levels=2, model_channels=16,
        channel_mult=[1, 2], num_blocks=2, attention_levels=[],
        bottleneck_attention=False, dropout=0.0)
    return diffusion_utils.WrapDenoiser(unet, "unet3d")


def Train(wrapper, conditions, targets):
    dataset = torch.utils.data.TensorDataset(
        torch.tensor(conditions), torch.tensor(targets))
    history = diffusion_utils.TrainDiffusionModel(wrapper, dataset, Kratos.Parameters("""{
        "epochs"        : 400,
        "batch_size"    : 4,
        "learning_rate" : 2e-4,
        "device"        : "auto",
        "seed"          : 7,
        "echo_interval" : 50
    }"""))
    training_utils.SaveTrainedModel(wrapper.unet, DATA / "unet3d_downscaler.mdlus")
    return history


def Evaluate(wrapper, conditions, targets, scale):
    results = []
    for condition, target in zip(conditions, targets):
        ensemble = diffusion_utils.GenerateEnsemble(wrapper, condition, Kratos.Parameters("""{
            "num_samples" : 16,
            "num_steps"   : 18,
            "seed"        : 11
        }"""))
        # everything back in physical units - the model card lesson applied
        mean, spread = ensemble.mean(axis=0) / scale, ensemble.std(axis=0) / scale
        condition, target = condition / scale, target / scale
        rmse_model = float(numpy.sqrt(numpy.mean((mean - target) ** 2)))
        rmse_coarse = float(numpy.sqrt(numpy.mean((condition - target) ** 2)))
        error = numpy.abs(mean - target)
        spread_error_correlation = float(numpy.corrcoef(
            spread.ravel(), error.ravel())[0, 1])
        results.append({"mean": mean, "spread": spread, "rmse_model": rmse_model,
                        "rmse_coarse": rmse_coarse,
                        "spread_error_correlation": spread_error_correlation})
        print(f"[eval] held-out case: RMSE coarse {rmse_coarse:.4f} -> "
              f"ensemble mean {rmse_model:.4f} "
              f"(spread/error corr {spread_error_correlation:.2f})")
    return results


def Render(history, conditions, targets, results):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    mid = GRID_SHAPE[0] // 2
    columns = ("coarse condition", "ensemble mean", "fine solve (truth)",
               "|error|", "ensemble spread")
    figure, axes = plt.subplots(len(results) + 1, len(columns),
                                figsize=(3.0 * len(columns), 2.7 * (len(results) + 1)),
                                constrained_layout=True)

    axes[0][0].semilogy(history)
    axes[0][0].set_title("EDM training loss (5-D batches)")
    axes[0][0].set_xlabel("epoch")
    for axis in axes[0][1:]:
        axis.axis("off")
    summary = "\n".join(
        f"case {i}: RMSE {r['rmse_coarse']:.4f} → {r['rmse_model']:.4f}"
        for i, r in enumerate(results))
    axes[0][2].text(0.0, 0.5, "mid-plane z-slices below\n\n" + summary,
                    va="center", fontsize=11)

    for row, (condition, target, result) in enumerate(
            zip(conditions, targets, results), start=1):
        slices = (condition[0][mid], result["mean"][0][mid], target[0][mid],
                  numpy.abs(result["mean"] - target)[0][mid], result["spread"][0][mid])
        for column, (label, plane) in enumerate(zip(columns, slices)):
            axis = axes[row][column]
            image = axis.imshow(plane.T, origin="lower",
                                cmap="inferno" if column < 3 else "viridis")
            figure.colorbar(image, ax=axis, shrink=0.8)
            axis.set_xticks([]), axis.set_yticks([])
            if row == 1:
                axis.set_title(label)
    figure.suptitle("DiffusionUNet3D downscaling on full 3D grids "
                    "(denoiser_interface: \"unet3d\")")
    figure.savefig(DATA / "volumetric_diffusion.png", dpi=130)


if __name__ == "__main__":
    train_conditions, train_targets, test_conditions, test_targets, scale = BuildDataset()
    wrapper = MakeDenoiser()
    history = Train(wrapper, train_conditions, train_targets)
    results = Evaluate(wrapper, test_conditions, test_targets, scale)
    Render(history, test_conditions / scale, test_targets / scale, results)
    # the reproducible claim: downscaling beats the coarse condition on every
    # held-out case (all seeds fixed; EDM training is sigma-stochastic, so the
    # claim is about the sampled ensemble, not a loss value)
    assert all(r["rmse_model"] < r["rmse_coarse"] for r in results), results
    print("[done] figure at data/volumetric_diffusion.png")
