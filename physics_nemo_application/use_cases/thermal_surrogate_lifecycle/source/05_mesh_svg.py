"""The base thermal-plate mesh, colored by TEMPERATURE.

meshio++'s SVG writer on the same 32x32 triangle mesh every stage in
this lifecycle trains and deploys against - the flagship case's ground
mesh, at a representative case. The SVG is kept in data/ alongside a
PNG rasterization (cairosvg) for the README embed.

Run time: a few seconds (one solve).
"""

import pathlib

import cairosvg
import numpy

import KratosMultiphysics as Kratos
import meshioplusplus as mio

import thermal_plate

DATA = pathlib.Path("..") / "data"


def WriteMeshSvgPng(path, mesh, **kwargs):
    mio.svg.write(str(path), mesh, **kwargs)
    cairosvg.svg2png(url=str(path), write_to=str(path.with_suffix(".png")), scale=2.0)


def main():
    DATA.mkdir(exist_ok=True)
    Kratos.Logger.GetDefaultOutput().SetSeverity(Kratos.Logger.Severity.WARNING)

    model, part = thermal_plate.Solve(
        conductivity=1.3, source_amplitude=1.25, source_center=(0.58, 0.42))
    ids = {node.Id: index for index, node in enumerate(part.Nodes)}
    points = numpy.array([[node.X, node.Y] for node in part.Nodes])
    triangles = numpy.array([[ids[node.Id] for node in element.GetGeometry()]
                             for element in part.Elements])
    temperature = numpy.array([node.GetSolutionStepValue(Kratos.TEMPERATURE)
                               for node in part.Nodes])

    mesh = mio.Mesh(points, [("triangle", triangles)],
                    point_data={"TEMPERATURE": temperature})
    WriteMeshSvgPng(DATA / "lifecycle_mesh.svg", mesh, image_width=440,
                    color_by="TEMPERATURE", cmap="turbo", colorbar=True,
                    stroke="#00000033", stroke_width="0.35")
    print(f"wrote lifecycle_mesh.svg ({part.NumberOfNodes()} nodes, "
          f"{part.NumberOfElements()} triangles)")


if __name__ == "__main__":
    main()
