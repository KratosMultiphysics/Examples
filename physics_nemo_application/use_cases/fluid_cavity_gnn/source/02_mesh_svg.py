"""The lid-driven cavity mesh, colored by velocity magnitude.

meshio++'s SVG writer with component=None (magnitude reduction) applied
to the real VMS-solved velocity field - the recirculating flow the GNN
propagates through the mesh graph, rendered on the actual mesh. The SVG
is kept in data/ alongside a PNG rasterization (cairosvg) for the
README embed.

Run time: a few seconds (one steady solve).
"""

import pathlib

import cairosvg
import numpy

import KratosMultiphysics as Kratos
import meshioplusplus as mio

import importlib
stage1 = importlib.import_module("01_cavity_gnn")

DATA = pathlib.Path("..") / "data"


def WriteMeshSvgPng(path, mesh, **kwargs):
    mio.svg.write(str(path), mesh, **kwargs)
    cairosvg.svg2png(url=str(path), write_to=str(path.with_suffix(".png")), scale=2.0)


def main():
    DATA.mkdir(exist_ok=True)
    Kratos.Logger.GetDefaultOutput().SetSeverity(Kratos.Logger.Severity.WARNING)

    model, part = stage1.SolveCavity(stage1.TEST_LID_VELOCITY)
    points, triangles = stage1.MeshArrays(part)
    velocity = numpy.array([[node.GetSolutionStepValue(Kratos.VELOCITY_X),
                             node.GetSolutionStepValue(Kratos.VELOCITY_Y)]
                            for node in part.Nodes])

    mesh = mio.Mesh(points, [("triangle", triangles)],
                    point_data={"VELOCITY": velocity})
    WriteMeshSvgPng(DATA / "cavity_mesh_velocity.svg", mesh, image_width=440,
                    color_by="VELOCITY", cmap="turbo", colorbar=True,
                    stroke="#00000033", stroke_width="0.4")
    print(f"wrote cavity_mesh_velocity.svg ({part.NumberOfNodes()} nodes, "
          f"{part.NumberOfElements()} triangles, lid velocity "
          f"{stage1.TEST_LID_VELOCITY})")


if __name__ == "__main__":
    main()
