"""Stage 1 - generate the training data with the real solver.

Runs the stationary heat-conduction case over a random sweep of
(conductivity, source amplitude, source center), samples the input fields
(CONDUCTIVITY, HEAT_FLUX) and the solved TEMPERATURE onto a regular grid
with the mesh bridge, and stores everything in one .npz.

The grid is the (C, D, H, W) layout PhysicsNeMo's grid models consume,
with the thin third axis carrying the 2D plane (the same idiom
GridInferenceProcess uses at deployment, so training and inference see
identical tensors).

Run time: ~1 minute (40 stationary solves on a 32x32 mesh).
"""

import json
import pathlib

import numpy

import KratosMultiphysics as Kratos
from KratosMultiphysics.PhysicsNeMoApplication import grid_bridge

import thermal_plate
import viz

OUTPUT = pathlib.Path("output")
DATA = pathlib.Path("..") / "data"

TRAIN_CASES = 40
SEED = 2026
GRID_SHAPE = (32, 32, 2)
BOUNDING_BOX = (numpy.array([0.0, 0.0, -0.05]), numpy.array([1.0, 1.0, 0.05]))
INPUT_FIELDS = [("CONDUCTIVITY", "node_historical"), ("HEAT_FLUX", "node_historical")]
OUTPUT_FIELDS = [("TEMPERATURE", "node_historical")]


def main():
    OUTPUT.mkdir(exist_ok=True)
    DATA.mkdir(exist_ok=True)
    Kratos.Logger.GetDefaultOutput().SetSeverity(Kratos.Logger.Severity.WARNING)

    cases = thermal_plate.SampleCases(TRAIN_CASES, SEED)
    inputs, targets = [], []
    gallery = []  # a few solved cases for the documentation figure

    for index, case in enumerate(cases):
        model, model_part = thermal_plate.Solve(**case)
        input_grid, _ = grid_bridge.SampleFieldsOnGrid(
            model_part, INPUT_FIELDS, GRID_SHAPE, BOUNDING_BOX)
        target_grid, _ = grid_bridge.SampleFieldsOnGrid(
            model_part, OUTPUT_FIELDS, GRID_SHAPE, BOUNDING_BOX)
        inputs.append(input_grid.astype(numpy.float32))
        targets.append(target_grid.astype(numpy.float32))

        if index < 3:
            gallery.append((
                case,
                numpy.array([node.GetSolutionStepValue(Kratos.HEAT_FLUX)
                             for node in model_part.Nodes]),
                numpy.array([node.GetSolutionStepValue(Kratos.TEMPERATURE)
                             for node in model_part.Nodes]),
                model, model_part))
        print(f"  case {index + 1:2d}/{TRAIN_CASES}: k={case['conductivity']:.3f} "
              f"q={case['source_amplitude']:.3f} center={case['source_center']}")

    numpy.savez(
        OUTPUT / "thermal_dataset.npz",
        inputs=numpy.stack(inputs), targets=numpy.stack(targets))
    with open(OUTPUT / "training_cases.json", "w") as handle:
        json.dump(cases, handle, indent=1)

    # documentation figure: three training cases, source next to solution
    fields = []
    for case, flux, temperature, _, _ in gallery:
        label = f"k={case['conductivity']:.2f}, q={case['source_amplitude']:.2f}"
        fields.append((f"HEAT_FLUX  ({label})", flux, "inferno"))
        fields.append((f"TEMPERATURE  ({label})", temperature, "viridis"))
    viz.RenderFields(gallery[0][4], fields, DATA / "dataset_cases.png",
                     shape=(3, 2), window_size=(1150, 1450))

    print(f"dataset: {OUTPUT / 'thermal_dataset.npz'} "
          f"(inputs {numpy.stack(inputs).shape}, targets {numpy.stack(targets).shape})")
    print(f"figure : {DATA / 'dataset_cases.png'}")


if __name__ == "__main__":
    main()
