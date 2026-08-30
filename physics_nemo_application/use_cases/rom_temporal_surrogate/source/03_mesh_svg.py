"""The thermal plate mesh underlying the POD basis.

meshio++ rendering of the real 16x16 structured triangle mesh (289
nodes) at k = 1.2, colored by TEMPERATURE at the final transient step -
the physical mesh behind the eight numbers the rest of the example
works in. The SVG is kept in data/ alongside a PNG rasterization
(cairosvg) for the README embed.

Run time: a few seconds (one transient solve, reusing stage 1's helper).
"""

import pathlib

import cairosvg
import numpy

import KratosMultiphysics as Kratos
import meshioplusplus as mio

import importlib
stage1 = importlib.import_module("01_basis_and_dynamics")

DATA = pathlib.Path("..") / "data"


def WriteMeshSvgPng(path, mesh, **kwargs):
    mio.svg.write(str(path), mesh, **kwargs)
    cairosvg.svg2png(url=str(path), write_to=str(path.with_suffix(".png")), scale=2.0)


def Triangulation(part):
    ids = {node.Id: index for index, node in enumerate(part.Nodes)}
    points = numpy.array([[node.X, node.Y] for node in part.Nodes])
    triangles = numpy.array([[ids[node.Id] for node in element.GetGeometry()]
                             for element in part.Elements])
    return points, triangles


def main():
    DATA.mkdir(exist_ok=True)
    Kratos.Logger.GetDefaultOutput().SetSeverity(Kratos.Logger.Severity.WARNING)

    trajectory = stage1.CollectTrajectory(1.2)   # (steps, n_nodes) TEMPERATURE

    import thermal_plate
    model = Kratos.Model()
    part = thermal_plate.CreateModelPart(model, stage1.DIVISIONS)
    points, triangles = Triangulation(part)

    mesh = mio.Mesh(points, [("triangle", triangles)],
                    point_data={"TEMPERATURE": trajectory[-1]})
    WriteMeshSvgPng(DATA / "rom_plate_mesh.svg", mesh, image_width=420,
                    color_by="TEMPERATURE", cmap="turbo", colorbar=True,
                    stroke="#00000033", stroke_width="0.4")
    print(f"wrote rom_plate_mesh.svg ({part.NumberOfNodes()} nodes, "
          f"{part.NumberOfElements()} triangles)")


if __name__ == "__main__":
    main()
