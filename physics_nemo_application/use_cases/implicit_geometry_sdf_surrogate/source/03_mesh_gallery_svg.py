"""Mesh gallery via meshio++'s SVG writer, rasterized to PNG.

The same six generated meshes as stage 1, rendered through meshio++'s own
SVG writer (the C++ core writes real file paths, so this is a straight
test of the vendored library, not a Python fallback path): one wireframe
panel per shape plus a field-colored render of the unseen shape from
stage 2. The SVG is kept in data/ alongside a PNG rasterization
(cairosvg) - README embeds are PNG, since a bare `fill="..."` attribute
on an SVG path has zero CSS specificity and some renderers (a plain
<img> tag included) fall back to the document-level style rule instead,
while every viewer treats a raster image the same way.

Run time: a few seconds - this script only touches artifacts stage 1
and stage 2 already produced (rerun them first).
"""

import pathlib

import cairosvg
import numpy

import KratosMultiphysics as Kratos
import meshioplusplus as mio

import thermal_hole_case

import importlib
stage1 = importlib.import_module("01_generate_and_train")
stage2 = importlib.import_module("02_predict_unseen_shape")

DATA = pathlib.Path("..") / "data"


def WriteMeshSvg(path, points, triangles, point_data=None, **kwargs):
    mesh = mio.Mesh(points, [("triangle", triangles)], point_data=point_data)
    mio.svg.write(str(path), mesh, image_width=360, **kwargs)
    cairosvg.svg2png(url=str(path), write_to=str(path.with_suffix(".png")), scale=2.0)


def main():
    DATA.mkdir(exist_ok=True)
    Kratos.Logger.GetDefaultOutput().SetSeverity(Kratos.Logger.Severity.WARNING)

    # ---- one wireframe SVG per training shape -------------------------------
    for cx, cy, radius in stage1.TRAIN_SHAPES:
        model = Kratos.Model()
        part = thermal_hole_case.GenerateAndSolve(model, (cx, cy), radius)
        points, triangles = thermal_hole_case.Triangulation(part)
        name = f"mesh_{cx:.2f}_{cy:.2f}_{radius:.2f}".replace(".", "")
        WriteMeshSvg(DATA / f"{name}.svg", points, triangles,
                    fill="#dce9f5", stroke="#1f4e79", stroke_width="0.6")
        print(f"  wrote {name}.svg ({part.NumberOfNodes()} nodes, "
              f"{part.NumberOfElements()} triangles)")

    # ---- the unseen shape, field-colored ------------------------------------
    center, radius = stage2.UNSEEN["center"], stage2.UNSEEN["radius"]
    model = Kratos.Model()
    part = thermal_hole_case.GenerateAndSolve(model, center, radius)
    points, triangles = thermal_hole_case.Triangulation(part)
    temperature = thermal_hole_case.Temperatures(part)
    WriteMeshSvg(DATA / "unseen_mesh_field.svg", points, triangles,
                point_data={"TEMPERATURE": temperature},
                color_by="TEMPERATURE", cmap="turbo", colorbar=True,
                stroke="#00000022", stroke_width="0.3")
    print("wrote unseen_mesh_field.svg")


if __name__ == "__main__":
    main()
