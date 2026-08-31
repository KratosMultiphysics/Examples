"""Before/after adapted mesh.

Reruns stage 1's surrogate-residual-driven MMG adaptation and renders
the mesh before and after through meshio++'s SVG writer, colored by the
assembled PDE residual that drives the remesh - the counterpart of the
third matplotlib panel, at full triangle resolution. The SVG is kept in
data/ alongside a PNG rasterization (cairosvg) for the README embed.

Run time: ~15 seconds (a handful of solves + one MMG remesh).
"""

import pathlib

import cairosvg
import numpy

import KratosMultiphysics as Kratos
import meshioplusplus as mio
from KratosMultiphysics.PhysicsNeMoApplication.processes import adaptive_remesh_process
from KratosMultiphysics.PhysicsNeMoApplication.bridges.mesh_bridge import adaptive_remeshing
from KratosMultiphysics.PhysicsNeMoApplication.physics import solver_residuals
import importlib
stage1 = importlib.import_module("01_surrogate_driven_remeshing")

DATA = pathlib.Path("..") / "data"


def WriteMeshSvgPng(path, mesh, **kwargs):
    mio.svg.write(str(path), mesh, **kwargs)
    cairosvg.svg2png(url=str(path), write_to=str(path.with_suffix(".png")), scale=2.0)


def main():
    DATA.mkdir(exist_ok=True)
    Kratos.Logger.GetDefaultOutput().SetSeverity(Kratos.Logger.Severity.WARNING)

    import torch
    inputs, targets = [], []
    for conductivity in stage1.TRAIN_CONDUCTIVITIES:
        model, part = stage1.SolveCase(conductivity)
        for node in part.Nodes:
            inputs.append([node.X, node.Y, conductivity])
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
    surrogate.eval()

    model, part = stage1.SolveCase(stage1.TEST_CONDUCTIVITY)
    with torch.no_grad():
        prediction = surrogate(torch.tensor(
            [[node.X, node.Y, stage1.TEST_CONDUCTIVITY] for node in part.Nodes],
            dtype=torch.float32)).numpy()[:, 0]
    for node, value in zip(part.Nodes, prediction):
        if not node.IsFixed(Kratos.TEMPERATURE):
            node.SetSolutionStepValue(Kratos.TEMPERATURE, float(value))

    evaluator = solver_residuals.BuildResidualEvaluator(part)
    nodal_error = adaptive_remeshing.NodalErrorArray(
        part, evaluator.ComputeNodalResiduals())
    points_before, triangles_before = stage1.MeshArrays(part)
    nodes_before = part.NumberOfNodes()

    mesh = mio.Mesh(points_before, [("triangle", triangles_before)],
                    point_data={"RESIDUAL": nodal_error})
    WriteMeshSvgPng(DATA / "remesh_mesh_before.svg", mesh, image_width=440,
                    color_by="RESIDUAL", cmap="turbo", colorbar=True,
                    stroke="#00000033", stroke_width="0.35")

    process = adaptive_remesh_process.Factory(Kratos.Parameters("""{
        "Parameters": {
            "model_part_name" : "ThermalModelPart",
            "remesh_interval" : 1,
            "size_settings"   : { "target_error": 1e-3, "exponent": 0.5,
                                  "minimal_size": 0.015, "maximal_size": 0.15 }
        }
    }"""), model)
    part.ProcessInfo[Kratos.STEP] = 1
    process.ExecuteFinalizeSolutionStep()
    nodes_after = part.NumberOfNodes()
    points_after, triangles_after = stage1.MeshArrays(part)

    mesh = mio.Mesh(points_after, [("triangle", triangles_after)])
    WriteMeshSvgPng(DATA / "remesh_mesh_after.svg", mesh, image_width=440,
                    fill="#dce9f5", stroke="#1f4e79", stroke_width="0.35")
    print(f"wrote remesh_mesh_before.svg, remesh_mesh_after.svg "
          f"({nodes_before} -> {nodes_after} nodes)")


if __name__ == "__main__":
    main()
