"""Stage 2 - roll the surrogate forward and watch the body shrink.

Seeds the BPTT-trained surrogate with the first four solver states of the
held-out cooling schedule and lets it feed itself for the remaining 36
steps - no solver in the loop. The animation compares the solver's
deformed, cooling body against the surrogate's rollout frame by frame;
the shrinkage curve reduces the same comparison to one engineering
quantity (the body's width over time).

Run time: under a minute (one transient solve for the reference frames).
"""

import json
import pathlib

import numpy
import pyvista
import torch
from matplotlib import pyplot

import KratosMultiphysics as Kratos
from KratosMultiphysics.PhysicsNeMoApplication.training import temporal_training
import sintering_case
import surrogate_model

pyvista.OFF_SCREEN = True

OUTPUT = pathlib.Path("output")
DATA = pathlib.Path("..") / "data"

DIVISIONS = 10
HISTORY = surrogate_model.HISTORY
EXAGGERATION = 3.0  # displacement magnification in the animation


def ReferenceMesh():
    """Points and triangle faces of the undeformed body."""
    model = Kratos.Model()
    model_part = sintering_case.CreateSinteringModelPart(model, DIVISIONS)
    points = numpy.array([[node.X0, node.Y0, node.Z0] for node in model_part.Nodes])
    row = {node.Id: index for index, node in enumerate(model_part.Nodes)}
    faces = []
    for element in model_part.Elements:
        faces.append([3, *[row[node.Id] for node in element.GetGeometry()]])
    return points, numpy.asarray(faces, dtype=numpy.int64)


def RecordGroundTruthAnimation():
    """The coupled solve recorded live by core Kratos' new animation process.

    PyVistaAnimationOutputProcess (kratos/python_scripts) renders one frame
    per output step straight from the model part - temperature-colored,
    displacement-warped - and encodes the GIF at finalize. No hand-rolled
    frame loop; this is the recommended way to animate any transient.
    """
    from KratosMultiphysics.pyvista_animation_output_process import (
        PyVistaAnimationOutputProcess)

    model = Kratos.Model()
    analysis = sintering_case.CreateSinteringAnalysis(
        model, divisions=DIVISIONS, cooling_rate=1400.0,
        time_step=0.0125, end_time=0.5)
    analysis.Initialize()
    animation = PyVistaAnimationOutputProcess(model, Kratos.Parameters("""{
        "model_part_name" : "Structure",
        "output_path"     : "output/animation",
        "file_name"       : "sintering_solve.gif",
        "fps"             : 8.0,
        "variable_name"   : "TEMPERATURE",
        "warp_by_vector"  : "DISPLACEMENT",
        "warp_factor"     : 3.0,
        "show_undeformed" : false,
        "clim"            : [300.0, 1000.0],
        "view"            : "xy",
        "window_size"     : [640, 560],
        "time_format"     : "t = {:.3f} s"
    }"""), )
    animation.ExecuteInitialize()
    while analysis.KeepAdvancingSolutionLoop():
        analysis.time = analysis._AdvanceTime()
        analysis.InitializeSolutionStep()
        analysis.SolveSolutionStep()
        analysis.FinalizeSolutionStep()
        if animation.IsOutputStep():
            animation.PrintOutput()
    analysis.Finalize()
    animation.ExecuteFinalize()
    import shutil
    shutil.copy("output/animation/sintering_solve.gif", DATA / "sintering_solve.gif")
    print(f"figure : {DATA / 'sintering_solve.gif'} (PyVistaAnimationOutputProcess)")


def main():
    DATA.mkdir(exist_ok=True)
    Kratos.Logger.GetDefaultOutput().SetSeverity(Kratos.Logger.Severity.WARNING)

    data = numpy.load(OUTPUT / "trajectories.npz")
    scale = data["scale"]                               # per-channel (3,)
    solver_states = data["held_out"]                    # (T, N, 3) physical
    scaled = solver_states / scale

    model = surrogate_model.Create(0)
    model.load_state_dict(torch.load(OUTPUT / "bptt.pt", weights_only=True))
    model.eval()
    initial = [torch.from_numpy(scaled[step]).float() for step in range(HISTORY)]
    with torch.no_grad():
        predicted = temporal_training.RolloutPredictions(
            model, initial, steps=scaled.shape[0] - HISTORY)
    surrogate_states = numpy.concatenate(
        [scaled[:HISTORY], predicted.numpy()]) * scale

    # ---- the animation ----------------------------------------------------
    points, faces = ReferenceMesh()
    surface = pyvista.PolyData(points, faces)
    temperature_range = (float(solver_states[:, :, 2].min()),
                         float(solver_states[:, :, 2].max()))

    # frames are collected as arrays and assembled with Pillow: pyvista's
    # own open_gif needs imageio, which this environment does not have.
    # The two meshes are created ONCE and their point/scalar arrays mutated
    # per frame - recreating actors resets cameras and scalar bars
    frames = []
    plotter = pyvista.Plotter(shape=(1, 2), off_screen=True,
                              window_size=(1200, 640), border=False)
    panels = []
    for panel, (states, title) in enumerate(
            [(solver_states, "coupled solver"),
             (surrogate_states, "surrogate rollout (no solver)")]):
        plotter.subplot(0, panel)
        plotter.set_background("white")
        frame = surface.copy()
        frame["TEMPERATURE"] = states[0, :, 2]
        plotter.add_mesh(frame, scalars="TEMPERATURE", cmap="inferno",
                         clim=temperature_range, show_edges=True,
                         edge_color="gray", line_width=0.5,
                         scalar_bar_args={"title": "TEMPERATURE",
                                          "vertical": False,
                                          "position_x": 0.15, "position_y": 0.03,
                                          "width": 0.7, "height": 0.08,
                                          "title_font_size": 13,
                                          "label_font_size": 11,
                                          "color": "black", "fmt": "%.0f"})
        plotter.add_text(title, position="upper_edge", font_size=11, color="black")
        plotter.view_xy()
        plotter.camera.zoom(1.25)
        panels.append((frame, states))

    for step in range(solver_states.shape[0]):
        for frame, states in panels:
            displacement = numpy.zeros_like(points)
            displacement[:, :2] = states[step, :, :2]
            # IN-PLACE writes plus Modified(): rebinding frame.points leaves
            # the rendered picture frozen on this pyvista/VTK version
            frame.points[:] = points + EXAGGERATION * displacement
            frame["TEMPERATURE"][:] = states[step, :, 2]
            frame.Modified()
        plotter.render()
        frames.append(plotter.screenshot(return_img=True))
    plotter.close()

    from PIL import Image
    images = [Image.fromarray(frame) for frame in frames]
    images[0].save(DATA / "rollout.gif", save_all=True, append_images=images[1:],
                   duration=125, loop=0)

    # ---- the shrinkage curve ----------------------------------------------
    def Width(states):
        deformed_x = points[None, :, 0] + states[:, :, 0]
        return deformed_x.max(axis=1) - deformed_x.min(axis=1)

    time = numpy.arange(solver_states.shape[0]) * 0.0125
    solver_width = Width(solver_states)
    surrogate_width = Width(surrogate_states)

    figure, axis = pyplot.subplots(figsize=(7.0, 4.0))
    axis.plot(time, solver_width, "k-", linewidth=2, label="coupled solver")
    axis.plot(time, surrogate_width, "r--", linewidth=2,
              label="surrogate rollout (seeded with 4 states)")
    axis.axvline(time[HISTORY - 1], color="gray", linestyle=":",
                 label="last solver state seen")
    axis.set_xlabel("time [s]")
    axis.set_ylabel("body width [m]")
    axis.set_title("Cooling-driven shrinkage, held-out schedule")
    axis.legend()
    axis.grid(True, alpha=0.3)
    figure.tight_layout()
    figure.savefig(DATA / "shrinkage_curve.png", dpi=130)

    width_error = float(numpy.abs(surrogate_width - solver_width).max())
    print(f"max width error over the rollout: {width_error:.2e} m "
          f"(total shrinkage {solver_width[0] - solver_width[-1]:.2e} m)")
    with open(OUTPUT / "rollout_summary.json", "w") as handle:
        json.dump({"max_width_error": width_error,
                   "total_shrinkage": float(solver_width[0] - solver_width[-1])},
                  handle, indent=1)
    print(f"figures: {DATA / 'rollout.gif'}, {DATA / 'shrinkage_curve.png'}")
    RecordGroundTruthAnimation()


if __name__ == "__main__":
    main()
