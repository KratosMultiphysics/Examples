"""Refine the mesh where the surrogate is wrong.

The loop this example closes: a surrogate writes its prediction onto the
model part; AdaptiveRemeshProcess assembles the REAL PDE residual of that
state through the solver's own elements, turns the per-node residual into
an equidistributed target size field, and remeshes with MeshingApplication's
MMG. Elements concentrate exactly where the surrogate's physics error
lives - no reference solution needed, the residual is computable from the
surrogate state alone.

The surrogate here is a deliberately modest MLP (x, y, k) -> T trained on
six solves: good in the smooth outskirts, wrong near the peak, which is
where the refined mesh should end up densest.

Run time: ~1 minute.
"""

import json
import pathlib

import numpy
import torch
from matplotlib import pyplot, tri

import KratosMultiphysics as Kratos
from KratosMultiphysics.PhysicsNeMoApplication import adaptive_remesh_process
from KratosMultiphysics.PhysicsNeMoApplication import solver_residuals
from KratosMultiphysics.PhysicsNeMoApplication import adaptive_remeshing

import thermal_case

OUTPUT = pathlib.Path("output")
DATA = pathlib.Path("..") / "data"

TRAIN_CONDUCTIVITIES = numpy.linspace(0.5, 2.0, 6)
TEST_CONDUCTIVITY = 1.1
DIVISIONS = 15


def SolveCase(conductivity):
    model = Kratos.Model()
    analysis = thermal_case.CreateThermalAnalysis(
        model, conductivity=float(conductivity), heat_flux=1.0, divisions=DIVISIONS)
    analysis.Run()
    return model, model["ThermalModelPart"]


def MeshArrays(model_part):
    points = numpy.array([[node.X, node.Y] for node in model_part.Nodes])
    rows = {node.Id: index for index, node in enumerate(model_part.Nodes)}
    triangles = numpy.array([[rows[element.GetGeometry()[i].Id] for i in range(3)]
                             for element in model_part.Elements])
    return points, triangles


def main():
    OUTPUT.mkdir(exist_ok=True)
    DATA.mkdir(exist_ok=True)
    Kratos.Logger.GetDefaultOutput().SetSeverity(Kratos.Logger.Severity.WARNING)

    # ---- a modest surrogate: (x, y, k) -> T --------------------------------
    inputs, targets = [], []
    for conductivity in TRAIN_CONDUCTIVITIES:
        model, model_part = SolveCase(conductivity)
        for node in model_part.Nodes:
            inputs.append([node.X, node.Y, conductivity])
            targets.append([node.GetSolutionStepValue(Kratos.TEMPERATURE)])
    inputs = torch.tensor(inputs, dtype=torch.float32)
    targets = torch.tensor(targets, dtype=torch.float32)

    torch.manual_seed(0)
    surrogate = torch.nn.Sequential(
        torch.nn.Linear(3, 32), torch.nn.Tanh(),
        torch.nn.Linear(32, 32), torch.nn.Tanh(),
        torch.nn.Linear(32, 1))
    optimizer = torch.optim.Adam(surrogate.parameters(), lr=2e-3)
    for step in range(400):
        optimizer.zero_grad()
        torch.nn.functional.mse_loss(surrogate(inputs), targets).backward()
        optimizer.step()
    surrogate.eval()

    # ---- write the surrogate state onto a fresh case -----------------------
    model, model_part = SolveCase(TEST_CONDUCTIVITY)
    reference = numpy.array([node.GetSolutionStepValue(Kratos.TEMPERATURE)
                             for node in model_part.Nodes])
    with torch.no_grad():
        prediction = surrogate(torch.tensor(
            [[node.X, node.Y, TEST_CONDUCTIVITY] for node in model_part.Nodes],
            dtype=torch.float32)).numpy()[:, 0]
    for node, value in zip(model_part.Nodes, prediction):
        if not node.IsFixed(Kratos.TEMPERATURE):
            node.SetSolutionStepValue(Kratos.TEMPERATURE, float(value))
    surrogate_error = numpy.abs(prediction - reference)
    print(f"surrogate on unseen k={TEST_CONDUCTIVITY}: "
          f"max |error| {surrogate_error.max():.2e}")

    # the quantity that drives the adaptation: the REAL residual of the
    # surrogate state, from the solver's own assembled elements
    evaluator = solver_residuals.BuildResidualEvaluator(model_part)
    nodal_error = adaptive_remeshing.NodalErrorArray(
        model_part, evaluator.ComputeNodalResiduals())

    points_before, triangles_before = MeshArrays(model_part)
    nodes_before = model_part.NumberOfNodes()

    # ---- the adaptation ----------------------------------------------------
    process = adaptive_remesh_process.Factory(Kratos.Parameters("""{
        "Parameters": {
            "model_part_name" : "ThermalModelPart",
            "remesh_interval" : 1,
            "size_settings"   : { "target_error": 1e-3, "exponent": 0.5,
                                  "minimal_size": 0.015, "maximal_size": 0.15 },
            "echo_level"      : 1
        }
    }"""), model)
    model_part.ProcessInfo[Kratos.STEP] = 1
    process.ExecuteFinalizeSolutionStep()
    nodes_after = model_part.NumberOfNodes()
    points_after, triangles_after = MeshArrays(model_part)
    print(f"remesh: {nodes_before} -> {nodes_after} nodes")

    # ---- figures ----------------------------------------------------------
    figure, axes = pyplot.subplots(1, 3, figsize=(13.8, 4.1))
    triangulation = tri.Triangulation(points_before[:, 0], points_before[:, 1],
                                      triangles_before)
    mappable = axes[0].tricontourf(triangulation, surrogate_error,
                                   levels=20, cmap="magma")
    axes[0].triplot(triangulation, color="w", linewidth=0.25, alpha=0.4)
    axes[0].set_title("surrogate |error| (vs the solver)")
    figure.colorbar(mappable, ax=axes[0], shrink=0.85)
    mappable = axes[1].tricontourf(triangulation, nodal_error,
                                   levels=20, cmap="magma")
    axes[1].set_title("assembled PDE residual of the surrogate state\n(what drives the remesh - no reference needed)")
    figure.colorbar(mappable, ax=axes[1], shrink=0.85)
    adapted = tri.Triangulation(points_after[:, 0], points_after[:, 1], triangles_after)
    axes[2].triplot(adapted, color="k", linewidth=0.4)
    axes[2].set_title(f"MMG-adapted mesh ({nodes_before} -> {nodes_after} nodes)")
    for axis in axes:
        axis.set_aspect("equal")
    figure.tight_layout()
    figure.savefig(DATA / "remeshing.png", dpi=130)

    with open(OUTPUT / "remesh_summary.json", "w") as handle:
        json.dump({"nodes_before": nodes_before, "nodes_after": nodes_after,
                   "surrogate_max_error": float(surrogate_error.max()),
                   "residual_max": float(numpy.max(nodal_error))}, handle, indent=1)
    print(f"figure : {DATA / 'remeshing.png'}")


if __name__ == "__main__":
    main()
