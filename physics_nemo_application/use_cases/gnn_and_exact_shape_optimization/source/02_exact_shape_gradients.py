"""Stage 2 - exact shape gradients through the real FEM assembly.

The GNN of Stage 1 gives cheap predictions; this stage gives exact
*derivatives*. Three pieces, all analytic (no surrogate anywhere):

1. `ComputeShapeSensitivityField`: dJ/dX at every node of the mesh, for
   J = sum of nodal temperatures, computed from the solver's own assembled
   tangent by the adjoint method - one linear solve for the whole field.
2. `ComputeControlSensitivities`: the chain rule through a free-form
   deformation (FFD) lattice, giving dJ/d(control) for a handful of design
   variables - verified here against re-solve finite differences to
   ~1e-10 relative.
3. A gradient-descent shape optimization: drive J to 75 % of its initial
   value by moving the FFD lattice, the mesh deforming under it.

Run time: ~1 minute (the optimization re-solves the thermal case per step).

The notebook shape_optimization.ipynb tells the same story with narrative.
"""

import contextlib
import json
import os
import pathlib

import numpy
import torch
from matplotlib import pyplot, tri as mtri

import KratosMultiphysics as Kratos
from KratosMultiphysics.PhysicsNeMoApplication.physics import differentiable_residual
from KratosMultiphysics.PhysicsNeMoApplication.physics import sensitivity_utils
from KratosMultiphysics.PhysicsNeMoApplication.bridges.mesh_bridge import deformation

import thermal_case

OUTPUT = pathlib.Path("output")
DATA = pathlib.Path("..") / "data"

# FFD lattice spanning the unit square; non-degenerate z on purpose (the
# mesh's own bounding box is flat in z)
ORIGIN = [0.0, 0.0, -0.5]
EXTENT = [1.0, 1.0, 1.0]
DIVISIONS = 12


@contextlib.contextmanager
def Quiet():
    """Silences the C++ solver banner (fd-level redirect; exceptions pass)."""
    saved = os.dup(1)
    with open(os.devnull, "w") as null:
        os.dup2(null.fileno(), 1)
    try:
        yield
    finally:
        os.dup2(saved, 1)
        os.close(saved)


def Solve(control=None, reference=None):
    """Solves the thermal case, optionally on an FFD-deformed mesh."""
    model = Kratos.Model()
    with Quiet():
        analysis = thermal_case.CreateThermalAnalysis(
            model, conductivity=2.0, heat_flux=1.0, divisions=DIVISIONS)
        analysis.Initialize()
    model_part = model["ThermalModelPart"]

    if control is not None:
        points = torch.as_tensor(reference, dtype=torch.float64)
        deformed = deformation.DeformPoints(
            points, torch.as_tensor(control, dtype=torch.float64), "ffd",
            origin=ORIGIN, extent=EXTENT).numpy()
        for node, position in zip(model_part.Nodes, deformed):
            node.X0, node.Y0, node.Z0 = map(float, position)
            node.X, node.Y, node.Z = node.X0, node.Y0, node.Z0

    with Quiet():
        analysis.RunSolutionLoop()
    return model, model_part


def Objective(model_part):
    return sum(node.GetSolutionStepValue(Kratos.TEMPERATURE)
               for node in model_part.Nodes)


def ShapeField(model_part):
    """Exact dJ/dX for J = sum of temperatures, via the adjoint."""
    assembler = differentiable_residual.TangentAssembler(model_part)
    dof_map = differentiable_residual.DofFieldMap(
        assembler, [("TEMPERATURE", "node_historical")])
    dJ_du = numpy.ones(dof_map.n_equations)
    return sensitivity_utils.ComputeShapeSensitivityField(
        assembler, dof_map, dJ_du, fd_step=1e-6)


def MeshArrays(model_part):
    points = numpy.array([[node.X, node.Y] for node in model_part.Nodes])
    rows = {node.Id: index for index, node in enumerate(model_part.Nodes)}
    triangles = numpy.array([[rows[element.GetGeometry()[i].Id] for i in range(3)]
                             for element in model_part.Elements])
    temperature = numpy.array([node.GetSolutionStepValue(Kratos.TEMPERATURE)
                               for node in model_part.Nodes])
    return points, triangles, temperature


def main():
    OUTPUT.mkdir(exist_ok=True)
    DATA.mkdir(exist_ok=True)
    Kratos.Logger.GetDefaultOutput().SetSeverity(Kratos.Logger.Severity.WARNING)

    model, model_part = Solve()
    reference = numpy.array([[node.X0, node.Y0, node.Z0] for node in model_part.Nodes])
    initial_objective = Objective(model_part)
    print(f"{model_part.NumberOfNodes()} nodes; J0 = {initial_objective:.6f}")

    # ---- 1. the exact sensitivity field, rendered as arrows ---------------
    field = ShapeField(model_part)
    points, triangles, temperature = MeshArrays(model_part)
    triangulation = mtri.Triangulation(points[:, 0], points[:, 1], triangles)

    figure, axes = pyplot.subplots(1, 2, figsize=(10.6, 4.4))
    contour = axes[0].tricontourf(triangulation, temperature, levels=20, cmap="viridis")
    axes[0].triplot(triangulation, color="w", linewidth=0.3, alpha=0.5)
    axes[0].set_aspect("equal")
    axes[0].set_title("TEMPERATURE on the initial domain")
    figure.colorbar(contour, ax=axes[0], shrink=0.85)
    axes[1].triplot(triangulation, color="0.85", linewidth=0.4)
    quiver = axes[1].quiver(points[:, 0], points[:, 1], field[:, 0], field[:, 1],
                            numpy.hypot(field[:, 0], field[:, 1]),
                            cmap="viridis", scale=4.0)
    axes[1].set_aspect("equal")
    axes[1].set_title("exact dJ/dX at every node (adjoint)")
    figure.colorbar(quiver, ax=axes[1], shrink=0.85)
    figure.tight_layout()
    figure.savefig(DATA / "sensitivity_field.png", dpi=130)

    # ---- 2. FFD chain rule vs re-solve finite differences -----------------
    control = numpy.zeros((2, 2, 2, 3))
    gradient = sensitivity_utils.ComputeControlSensitivities(
        field, reference, control, "ffd", origin=ORIGIN, extent=EXTENT)

    step = 1e-5
    verification = []
    for entry in ((1, 0, 0, 0), (0, 1, 0, 1), (1, 1, 0, 0)):
        plus, minus = control.copy(), control.copy()
        plus[entry] += step
        minus[entry] -= step
        _, plus_part = Solve(plus, reference)
        _, minus_part = Solve(minus, reference)
        finite_difference = (Objective(plus_part) - Objective(minus_part)) / (2 * step)
        chain = float(gradient[entry])
        relative = abs(chain - finite_difference) / abs(finite_difference)
        verification.append({"lattice_entry": list(entry), "chain_rule": chain,
                             "finite_difference": finite_difference,
                             "relative_difference": relative})
        print(f"  lattice{entry}: chain rule {chain:+.8e}  "
              f"re-solve FD {finite_difference:+.8e}  rel {relative:.2e}")
        assert relative < 1e-6, "the exact gradient must match finite differences"

    # ---- 3. gradient-descent shape optimization ---------------------------
    target = 0.75 * initial_objective
    learning_rate = 0.1
    control = numpy.zeros((2, 2, 2, 3))
    history = []
    for iteration in range(20):
        _, part = Solve(control, reference) if iteration else (model, model_part)
        value = Objective(part)
        history.append(value)
        iteration_field = ShapeField(part)
        gradient = sensitivity_utils.ComputeControlSensitivities(
            iteration_field, reference, control, "ffd", origin=ORIGIN, extent=EXTENT)
        gradient[..., 2] = 0.0  # keep the deformation planar
        control = control - learning_rate * 2.0 * (value - target) * gradient
    _, final_part = Solve(control, reference)
    history.append(Objective(final_part))
    print(f"J: {history[0]:.6f} -> {history[-1]:.6f} (target {target:.6f}); "
          f"max control move {numpy.abs(control).max():.4f}")

    final_points, final_triangles, final_temperature = MeshArrays(final_part)
    figure, axes = pyplot.subplots(1, 3, figsize=(13.6, 4.0))
    axes[0].plot(history, "o-", markersize=4)
    axes[0].axhline(target, color="r", linestyle="--", label="target 0.75 J0")
    axes[0].set_xlabel("iteration")
    axes[0].set_ylabel("J = sum of temperatures")
    axes[0].set_title("Objective convergence")
    axes[0].legend()
    axes[0].grid(True, alpha=0.3)
    shared = {"levels": 20, "cmap": "viridis",
              "vmin": 0.0, "vmax": float(temperature.max())}
    for axis, (mesh_points, mesh_triangles, values, title) in zip(
            axes[1:],
            [(points, triangles, temperature, "initial domain"),
             (final_points, final_triangles, final_temperature, "optimized domain")]):
        local = mtri.Triangulation(mesh_points[:, 0], mesh_points[:, 1], mesh_triangles)
        mappable = axis.tricontourf(local, values, **shared)
        axis.triplot(local, color="w", linewidth=0.3, alpha=0.5)
        axis.set_aspect("equal")
        axis.set_title(title)
        figure.colorbar(mappable, ax=axis, shrink=0.85)
    figure.tight_layout()
    figure.savefig(DATA / "shape_optimization.png", dpi=130)

    with open(OUTPUT / "shape_summary.json", "w") as handle:
        json.dump({"J0": initial_objective, "J_final": history[-1],
                   "target": target, "history": history,
                   "verification": verification}, handle, indent=1)
    print(f"figures: {DATA / 'sensitivity_field.png'}, {DATA / 'shape_optimization.png'}")


if __name__ == "__main__":
    main()
