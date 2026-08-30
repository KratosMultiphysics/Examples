"""Initial vs shape-optimized domain.

Reruns stage 2's gradient-descent shape optimization (the exact-adjoint
sensitivities, ~20 re-solves) and renders the initial and final meshes
through meshio++'s SVG writer, colored by TEMPERATURE - the domain the
FFD lattice actually deformed, at the resolution the solver used. The
SVG is kept in data/ alongside a PNG rasterization (cairosvg) for the
README embed.

Run time: ~30 seconds.
"""

import pathlib

import cairosvg
import numpy

import KratosMultiphysics as Kratos
import meshioplusplus as mio

import importlib
stage2 = importlib.import_module("02_exact_shape_gradients")

DATA = pathlib.Path("..") / "data"


def WriteMeshSvgPng(path, mesh, **kwargs):
    mio.svg.write(str(path), mesh, **kwargs)
    cairosvg.svg2png(url=str(path), write_to=str(path.with_suffix(".png")), scale=2.0)


def main():
    DATA.mkdir(exist_ok=True)
    Kratos.Logger.GetDefaultOutput().SetSeverity(Kratos.Logger.Severity.WARNING)

    model, model_part = stage2.Solve()
    points, triangles, temperature = stage2.MeshArrays(model_part)
    initial_objective = stage2.Objective(model_part)
    reference = numpy.array([[node.X0, node.Y0, node.Z0] for node in model_part.Nodes])

    target = 0.75 * initial_objective
    learning_rate = 0.1
    control = numpy.zeros((2, 2, 2, 3))
    from KratosMultiphysics.PhysicsNeMoApplication import sensitivity_utils
    for iteration in range(20):
        _, part = stage2.Solve(control, reference) if iteration else (model, model_part)
        value = stage2.Objective(part)
        gradient = sensitivity_utils.ComputeControlSensitivities(
            stage2.ShapeField(part), reference, control, "ffd",
            origin=stage2.ORIGIN, extent=stage2.EXTENT)
        gradient[..., 2] = 0.0
        control = control - learning_rate * 2.0 * (value - target) * gradient
    _, final_part = stage2.Solve(control, reference)
    final_points, final_triangles, final_temperature = stage2.MeshArrays(final_part)
    print(f"J: {initial_objective:.6f} -> {stage2.Objective(final_part):.6f} "
          f"(target {target:.6f})")

    vmax = float(temperature.max())
    for name, pts, tris, values in [
            ("initial", points, triangles, temperature),
            ("optimized", final_points, final_triangles, final_temperature)]:
        mesh = mio.Mesh(pts[:, :2], [("triangle", tris)],
                        point_data={"TEMPERATURE": values})
        WriteMeshSvgPng(DATA / f"shape_mesh_{name}.svg", mesh, image_width=420,
                        color_by="TEMPERATURE", cmap="turbo", vmin=0.0, vmax=vmax,
                        colorbar=True, stroke="#00000033", stroke_width="0.4")
        print(f"wrote shape_mesh_{name}.svg")


if __name__ == "__main__":
    main()
