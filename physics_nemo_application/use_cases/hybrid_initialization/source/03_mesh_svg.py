"""The nonlinear cantilever's mesh, undeformed and deformed.

meshio++'s SVG writer applied to the real TotalLagrangian mesh: the
undeformed configuration as a plain wireframe, and the converged
deformed configuration colored by displacement magnitude - the same
solve stage 2 already runs, at the trace load. The SVG is kept in
data/ alongside a PNG rasterization (cairosvg) for the README embed.

Run time: a few seconds (one solve).
"""

import pathlib

import cairosvg
import numpy

import KratosMultiphysics as Kratos
import meshioplusplus as mio

import structural_cantilever

DATA = pathlib.Path("..") / "data"
LOAD = 2.75e7


def WriteMeshSvgPng(path, mesh, **kwargs):
    mio.svg.write(str(path), mesh, **kwargs)
    cairosvg.svg2png(url=str(path), write_to=str(path.with_suffix(".png")), scale=2.0)


def Triangulation(part, deformed: bool):
    ids = {node.Id: index for index, node in enumerate(part.Nodes)}
    if deformed:
        points = numpy.array([[node.X, node.Y] for node in part.Nodes])
    else:
        points = numpy.array([[node.X0, node.Y0] for node in part.Nodes])
    triangles = numpy.array([[ids[node.Id] for node in element.GetGeometry()]
                             for element in part.Elements])
    return points, triangles


def main():
    DATA.mkdir(exist_ok=True)
    Kratos.Logger.GetDefaultOutput().SetSeverity(Kratos.Logger.Severity.WARNING)

    model = Kratos.Model()
    analysis, part = structural_cantilever.CreateAnalysis(model, LOAD, divisions=8)
    analysis.Run()

    undeformed_points, triangles = Triangulation(part, deformed=False)
    mesh = mio.Mesh(undeformed_points, [("triangle", triangles)])
    WriteMeshSvgPng(DATA / "cantilever_mesh_undeformed.svg", mesh,
                    image_width=480, fill="#dce9f5", stroke="#1f4e79",
                    stroke_width="0.5")

    deformed_points, _ = Triangulation(part, deformed=True)
    magnitude = numpy.linalg.norm(deformed_points - undeformed_points, axis=1)
    mesh = mio.Mesh(deformed_points, [("triangle", triangles)],
                    point_data={"DISPLACEMENT_MAGNITUDE": magnitude})
    WriteMeshSvgPng(DATA / "cantilever_mesh_deformed.svg", mesh,
                    image_width=480, color_by="DISPLACEMENT_MAGNITUDE",
                    cmap="turbo", colorbar=True, stroke="#00000033",
                    stroke_width="0.4")
    print(f"wrote cantilever_mesh_undeformed.svg, cantilever_mesh_deformed.svg "
          f"(max |u| {magnitude.max():.4f} m)")


if __name__ == "__main__":
    main()
