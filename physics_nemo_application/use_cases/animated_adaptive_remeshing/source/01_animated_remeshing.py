"""A mesh that chases a moving heat source - animated by TransientPlotter.

The loop, per source position: an imperfect surrogate predicts the
temperature field; AdaptiveRemeshProcess assembles the REAL residual of
that prediction and remeshes with MMG (refining where the surrogate's
physics error concentrates - near the hot spot); the solver then runs on
the adapted mesh. As the Gaussian source sweeps across the plate the
refined region follows it, and the previously refined region coarsens
back.

The animation is recorded by core Kratos' new
pyvista_utilities.TransientPlotter, which explicitly supports the mesh
topology CHANGING between frames - every frame here has a different
number of nodes.

The residual detail that shapes the design (learned by probing): the
residual of a CONVERGED solve is machine-zero, so remeshing after the
solve only coarsens. The surrogate's imperfect state is what carries the
refinement signal - the same reason case surrogate_driven_remeshing
needs no reference solution.

Run time: ~2 minutes (16 solve+remesh cycles).
"""

import json
import pathlib

import numpy
import torch
from matplotlib import pyplot

import KratosMultiphysics as Kratos
from KratosMultiphysics.ConvectionDiffusionApplication.convection_diffusion_analysis import (
    ConvectionDiffusionAnalysis)
from KratosMultiphysics.PhysicsNeMoApplication import adaptive_remesh_process
import KratosMultiphysics.pyvista_utilities as pyvista_utilities

import thermal_plate

OUTPUT = pathlib.Path("output")
DATA = pathlib.Path("..") / "data"

DIVISIONS = 12
CONDUCTIVITY = 1.0
AMPLITUDE = 1.2
SWEEP = numpy.linspace(0.25, 0.75, 16)   # the source's path across the plate
TRAIN_POSITIONS = (0.2, 0.4, 0.6, 0.8)


def TrainSurrogate():
    """A modest MLP (x, y, cx) -> T on four source positions."""
    inputs, targets = [], []
    for cx in TRAIN_POSITIONS:
        model = Kratos.Model()
        part = thermal_plate.CreateModelPart(model, DIVISIONS)
        thermal_plate.ApplyCase(part, CONDUCTIVITY, AMPLITUDE, (cx, 0.5))
        ConvectionDiffusionAnalysis(model, thermal_plate._ProjectParameters()).Run()
        for node in part.Nodes:
            inputs.append([node.X, node.Y, cx])
            targets.append([node.GetSolutionStepValue(Kratos.TEMPERATURE)])
    inputs = torch.tensor(inputs, dtype=torch.float32)
    targets = torch.tensor(targets, dtype=torch.float32)
    torch.manual_seed(0)
    surrogate = torch.nn.Sequential(
        torch.nn.Linear(3, 32), torch.nn.Tanh(),
        torch.nn.Linear(32, 32), torch.nn.Tanh(), torch.nn.Linear(32, 1))
    optimizer = torch.optim.Adam(surrogate.parameters(), lr=2e-3)
    for _ in range(400):
        optimizer.zero_grad()
        torch.nn.functional.mse_loss(surrogate(inputs), targets).backward()
        optimizer.step()
    return surrogate.eval()


def main():
    OUTPUT.mkdir(exist_ok=True)
    DATA.mkdir(exist_ok=True)
    Kratos.Logger.GetDefaultOutput().SetSeverity(Kratos.Logger.Severity.WARNING)

    surrogate = TrainSurrogate()

    model = Kratos.Model()
    part = thermal_plate.CreateModelPart(model, DIVISIONS)
    # bootstrap solve: BuildResidualEvaluator needs the DOFs a solver adds,
    # so the very first remesh must be preceded by one real solve
    thermal_plate.ApplyCase(part, CONDUCTIVITY, AMPLITUDE, (float(SWEEP[0]), 0.5))
    ConvectionDiffusionAnalysis(model, thermal_plate._ProjectParameters()).Run()

    recorder = pyvista_utilities.TransientPlotter(
        str(DATA / "chasing_refinement.gif"),
        fps=4, name="TEMPERATURE", clim=(0.0, 0.032), showEdges=True,
        view="xy", windowSize=[720, 620],
        timeFormat="source position x = {:.3f}")
    node_counts = []

    for cycle, cx in enumerate(SWEEP):
        # 1. the surrogate's (imperfect) prediction of the new state
        thermal_plate.ApplyCase(part, CONDUCTIVITY, AMPLITUDE, (float(cx), 0.5))
        with torch.no_grad():
            prediction = surrogate(torch.tensor(
                [[node.X, node.Y, float(cx)] for node in part.Nodes],
                dtype=torch.float32)).numpy()[:, 0]
        for node, value in zip(part.Nodes, prediction):
            if not node.IsFixed(Kratos.TEMPERATURE):
                node.SetSolutionStepValue(Kratos.TEMPERATURE, float(value))

        # 2. remesh on the surrogate state's REAL residual
        adaptive_remesh_process.Factory(Kratos.Parameters("""{
            "Parameters": {
                "model_part_name" : "ThermalModelPart",
                "remesh_interval" : 1,
                "size_settings"   : { "target_error": 1.5e-3, "exponent": 0.5,
                                      "minimal_size": 0.015, "maximal_size": 0.12 }
            }
        }"""), model).Execute()

        # 3. the real solve on the adapted mesh
        thermal_plate.ApplyCase(part, CONDUCTIVITY, AMPLITUDE, (float(cx), 0.5))
        ConvectionDiffusionAnalysis(model, thermal_plate._ProjectParameters()).Run()

        node_counts.append(part.NumberOfNodes())
        recorder.AddFrame(part, time=float(cx))
        print(f"  cx = {cx:.3f}: {part.NumberOfNodes()} nodes after adaptation")

    frames = recorder.Close()

    figure, axis = pyplot.subplots(figsize=(6.8, 3.8))
    axis.plot(SWEEP, node_counts, "o-", markersize=4)
    axis.set_xlabel("source position x")
    axis.set_ylabel("nodes after adaptation")
    axis.set_title("The adapted mesh tracks the moving source")
    axis.grid(True, alpha=0.3)
    figure.tight_layout()
    figure.savefig(DATA / "node_counts.png", dpi=130)

    with open(OUTPUT / "remesh_summary.json", "w") as handle:
        json.dump({"frames": frames, "node_counts": node_counts,
                   "sweep": SWEEP.tolist()}, handle, indent=1)
    print(f"figures: {DATA / 'chasing_refinement.gif'} ({frames} frames), "
          f"{DATA / 'node_counts.png'}")


if __name__ == "__main__":
    main()
