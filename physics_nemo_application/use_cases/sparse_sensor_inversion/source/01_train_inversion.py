"""Stage 1 - a conditional diffusion model that inverts sparse sensors.

The FWI-style recipe the application test-pins (borehole inversion in
test_corrdiff_recipe.py), applied to the thermal plate: the model learns
p(full field | sensor readings, mask). Each training sample is one
stationary solve sampled on a 16x16 grid; its CONDITION is two channels -
the field values at a random set of 5..15 sensor pixels, and the binary
mask saying which pixels are sensors. Training over RANDOM sensor counts
and layouts is what makes stage 2's sensor-count sweep legitimate: the
deployed model has seen sparse and dense masks alike. Each solved field
is masked THREE independent ways - mask augmentation triples the dataset
without a single extra solve, and teaches the model that the field is
the invariant and the sensor layout is noise.

The denoiser is the same EDM-preconditioned SongUNet the CorrDiff case
uses; the EDM loss and loop come from the application's diffusion_utils.
Temperatures are scaled to O(1) for the diffusion training (the CorrDiff
case's lesson).

Run time: ~4 minutes (96 solves + 400 epochs on CPU).
"""

import json
import pathlib

import numpy
import torch
from matplotlib import pyplot

import KratosMultiphysics as Kratos
from KratosMultiphysics.PhysicsNeMoApplication.training import diffusion_utils
from KratosMultiphysics.PhysicsNeMoApplication.bridges import grid_bridge
from KratosMultiphysics.PhysicsNeMoApplication.training import training_utils
from physicsnemo.diffusion.preconditioners import EDMPrecondSuperResolution

import thermal_plate

OUTPUT = pathlib.Path("output")
DATA = pathlib.Path("..") / "data"

GRID = (16, 16, 2)
BOUNDING_BOX = (numpy.array([0.0, 0.0, -0.05]), numpy.array([1.0, 1.0, 0.05]))
SCALE = 40.0            # temperatures are O(0.025); diffusion wants O(1)
TRAIN_CASES = 96
SENSOR_RANGE = (5, 15)  # sensors per training sample, drawn uniformly


def FieldGrid(case):
    """One solve, sampled to a (16, 16) scaled temperature plane."""
    model, part = thermal_plate.Solve(divisions=16, **case)
    grid, _ = grid_bridge.SampleFieldsOnGrid(
        part, [("TEMPERATURE", "node_historical")], GRID, BOUNDING_BOX)
    return SCALE * grid.mean(axis=3)[0]


def SensorCondition(field, rng, count=None):
    """(2, 16, 16) condition: sensor readings + binary mask."""
    if count is None:
        count = int(rng.integers(SENSOR_RANGE[0], SENSOR_RANGE[1] + 1))
    flat = rng.choice(field.size, size=count, replace=False)
    mask = numpy.zeros(field.size)
    mask[flat] = 1.0
    mask = mask.reshape(field.shape)
    return numpy.stack([field * mask, mask])


def main():
    OUTPUT.mkdir(exist_ok=True)
    DATA.mkdir(exist_ok=True)
    Kratos.Logger.GetDefaultOutput().SetSeverity(Kratos.Logger.Severity.WARNING)

    rng = numpy.random.default_rng(7)
    conditions, targets = [], []
    for index, case in enumerate(thermal_plate.SampleCases(TRAIN_CASES, seed=23), start=1):
        field = FieldGrid(case)
        for _ in range(3):                       # mask augmentation
            conditions.append(SensorCondition(field, rng))
            targets.append(field[None])
        if index % 24 == 0:
            print(f"  solved and masked {index}/{TRAIN_CASES} cases")

    dataset = torch.utils.data.TensorDataset(
        torch.tensor(numpy.stack(conditions), dtype=torch.float32),
        torch.tensor(numpy.stack(targets), dtype=torch.float32))

    torch.manual_seed(0)
    denoiser = EDMPrecondSuperResolution(
        img_resolution=16, img_in_channels=2, img_out_channels=1,
        model_type="SongUNet", model_channels=16, channel_mult=[1, 2],
        num_blocks=1, attn_resolutions=[])

    history = diffusion_utils.TrainDiffusionModel(denoiser, dataset, Kratos.Parameters("""{
        "epochs"        : 700,
        "batch_size"    : 16,
        "learning_rate" : 2e-4,
        "echo_interval" : 50,
        "device"        : "cpu",
        "seed"          : 0
    }"""))
    print(f"EDM loss: {history[0]:.3e} -> best {min(history):.3e}")
    training_utils.SaveTrainedModel(denoiser, OUTPUT / "sensor_inversion.mdlus")

    figure, axis = pyplot.subplots(figsize=(6.4, 3.8))
    axis.semilogy(history)
    axis.set_xlabel("epoch")
    axis.set_ylabel("EDM loss (per-epoch mean)")
    axis.set_title("Sensor-conditioned diffusion training")
    axis.grid(True, which="both", alpha=0.3)
    figure.tight_layout()
    figure.savefig(DATA / "inversion_training.png", dpi=130)

    with open(OUTPUT / "training_summary.json", "w") as handle:
        json.dump({"cases": TRAIN_CASES, "sensor_range": list(SENSOR_RANGE),
                   "first_loss": float(history[0]), "best_loss": float(min(history))},
                  handle, indent=1)
    print(f"figure : {DATA / 'inversion_training.png'}")


if __name__ == "__main__":
    main()
