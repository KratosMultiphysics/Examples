"""Stage 2 - superresolution inside a RUNNING transient analysis.

This is the deployment mode the steady examples do not show: the
SuperResolutionProcess is attached to a live coarse transient - every
converged step it samples the coarse part, runs the upsampler and
scatters the result onto the fine part's nodes, exactly like an output
process. The conductivity is one the model never saw.

Truth is the same transient solved on the fine mesh; the baseline is
plain bilinear interpolation of the coarse grid. The animation shows all
three side by side as the plate heats.

Run time: ~1 minute.
"""

import json
import pathlib

import numpy
from matplotlib import pyplot
from PIL import Image

import KratosMultiphysics as Kratos
from KratosMultiphysics.PhysicsNeMoApplication import grid_bridge
from KratosMultiphysics.PhysicsNeMoApplication import superresolution_process

import thermal_plate

OUTPUT = pathlib.Path("output")
DATA = pathlib.Path("..") / "data"

TEST_CONDUCTIVITY = 1.2      # not in the training sweep
COARSE_DIVISIONS, FINE_DIVISIONS = 8, 32
COARSE_GRID, FINE_GRID = (9, 9, 2), (33, 33, 2)
BOUNDING_BOX = (numpy.array([0.0, 0.0, -0.05]), numpy.array([1.0, 1.0, 0.05]))
TIME_STEP, END_TIME = 0.005, 0.2
CASE = {"source_amplitude": 1.0, "source_center": (0.5, 0.5)}


def FineTruth():
    """The fine transient, collected per step on the fine grid."""
    model = Kratos.Model()
    analysis = thermal_plate.CreateTransientAnalysis(
        model, conductivity=TEST_CONDUCTIVITY, divisions=FINE_DIVISIONS,
        time_step=TIME_STEP, end_time=END_TIME, **CASE)
    states = []

    def PerStep(model_part):
        grid, _ = grid_bridge.SampleFieldsOnGrid(
            model_part, [("TEMPERATURE", "node_historical")], FINE_GRID, BOUNDING_BOX)
        states.append(grid.mean(axis=3)[0])

    thermal_plate.RunTransientAnalysis(analysis, per_step=PerStep)
    return numpy.stack(states)


def main():
    OUTPUT.mkdir(exist_ok=True)
    DATA.mkdir(exist_ok=True)
    Kratos.Logger.GetDefaultOutput().SetSeverity(Kratos.Logger.Severity.WARNING)

    truth = FineTruth()

    # ---- the coarse transient with the process attached -------------------
    model = Kratos.Model()
    analysis = thermal_plate.CreateTransientAnalysis(
        model, conductivity=TEST_CONDUCTIVITY, divisions=COARSE_DIVISIONS,
        time_step=TIME_STEP, end_time=END_TIME, **CASE)

    # the fine part lives in the SAME model: mesh only, no solver touches it.
    # It gets triangle ELEMENTS too, so the animation process below can
    # render the superresolved field as a surface
    fine_part = model.CreateModelPart("FineTarget")
    fine_part.AddNodalSolutionStepVariable(Kratos.TEMPERATURE)
    properties = fine_part.CreateNewProperties(1)
    n = FINE_DIVISIONS + 1
    for i in range(n):
        for j in range(n):
            fine_part.CreateNewNode(i * n + j + 1, i / FINE_DIVISIONS,
                                    j / FINE_DIVISIONS, 0.0)
    element = 0
    for i in range(FINE_DIVISIONS):
        for j in range(FINE_DIVISIONS):
            a, b = i * n + j + 1, (i + 1) * n + j + 1
            element += 1
            fine_part.CreateNewElement("Element2D3N", element, [a, b, a + 1], properties)
            element += 1
            fine_part.CreateNewElement("Element2D3N", element, [b, b + 1, a + 1], properties)

    process = superresolution_process.Factory(Kratos.Parameters("""{
        "Parameters": {
            "coarse_model_part_name" : "ThermalModelPart",
            "fine_model_part_name"   : "FineTarget",
            "model_settings"         : {
                "checkpoint_file" : "output/upsampler2d.pt",
                "device"          : "cpu"
            },
            "input_fields"           : [ { "variable_name" : "TEMPERATURE", "data_location" : "node_historical" } ],
            "output_fields"          : [ { "variable_name" : "TEMPERATURE", "data_location" : "node_historical" } ],
            "coarse_grid_shape"      : [9, 9, 2],
            "bounding_box"           : [0.0, 0.0, -0.05, 1.0, 1.0, 0.05],
            "squeeze_axis"           : 2,
            "execution_point"        : "finalize_solution_step",
            "output_interval"        : 1
        }
    }"""), model)

    # core Kratos' new animation output process records the SUPERRESOLVED
    # field live, straight from the fine part the deployment writes to
    from KratosMultiphysics.pyvista_animation_output_process import (
        PyVistaAnimationOutputProcess)
    animation = PyVistaAnimationOutputProcess(model, Kratos.Parameters("""{
        "model_part_name" : "FineTarget",
        "output_path"     : "output/animation",
        "file_name"       : "transient_sr_live.gif",
        "fps"             : 8.0,
        "variable_name"   : "TEMPERATURE",
        "clim"            : [0.0, 0.06],
        "show_edges"      : false,
        "view"            : "xy",
        "window_size"     : [640, 560],
        "time_format"     : "t = {:.3f} s"
    }"""))
    animation.ExecuteInitialize()

    coarse_frames, sr_frames = [], []

    def PerStep(model_part):
        process.ExecuteFinalizeSolutionStep()   # the in-loop deployment
        fine_part.ProcessInfo[Kratos.TIME] = model_part.ProcessInfo[Kratos.TIME]
        fine_part.ProcessInfo[Kratos.STEP] = model_part.ProcessInfo[Kratos.STEP]
        if animation.IsOutputStep():
            animation.PrintOutput()
        grid, _ = grid_bridge.SampleFieldsOnGrid(
            model_part, [("TEMPERATURE", "node_historical")], COARSE_GRID, BOUNDING_BOX)
        coarse_frames.append(grid.mean(axis=3)[0])
        values = numpy.array([node.GetSolutionStepValue(Kratos.TEMPERATURE)
                              for node in fine_part.Nodes])
        sr_frames.append(values.reshape(n, n))

    thermal_plate.RunTransientAnalysis(analysis, per_step=PerStep)
    animation.ExecuteFinalize()
    import shutil
    shutil.copy("output/animation/transient_sr_live.gif", DATA / "transient_sr_live.gif")
    coarse_frames = numpy.stack(coarse_frames)
    sr_frames = numpy.stack(sr_frames)

    # ---- baseline and error curves ----------------------------------------
    import torch
    bilinear = torch.nn.functional.interpolate(
        torch.from_numpy(coarse_frames[:, None]), size=(n, n),
        mode="bilinear", align_corners=True).numpy()[:, 0]

    sr_errors = numpy.sqrt(((sr_frames - truth) ** 2).mean(axis=(1, 2)))
    bilinear_errors = numpy.sqrt(((bilinear - truth) ** 2).mean(axis=(1, 2)))
    time = (numpy.arange(len(sr_errors)) + 1) * TIME_STEP
    print(f"unseen k={TEST_CONDUCTIVITY}: mean SR rmse {sr_errors.mean():.2e} "
          f"vs bilinear {bilinear_errors.mean():.2e} "
          f"({bilinear_errors.mean() / sr_errors.mean():.1f}x)")

    figure, axis = pyplot.subplots(figsize=(7.0, 4.0))
    axis.semilogy(time, bilinear_errors, label="bilinear interpolation", linewidth=1.8)
    axis.semilogy(time, sr_errors, label="learned upsampler (in loop)", linewidth=1.8)
    axis.set_xlabel("time [s]")
    axis.set_ylabel("RMSE vs fine-mesh solve")
    axis.set_title(f"Per-step superresolution error, unseen k = {TEST_CONDUCTIVITY}")
    axis.legend()
    axis.grid(True, which="both", alpha=0.3)
    figure.tight_layout()
    figure.savefig(DATA / "transient_sr_error.png", dpi=130)

    # ---- the animation: coarse | superresolved | fine truth ----------------
    limits = dict(vmin=0.0, vmax=float(truth.max()))
    images = []
    for step in range(truth.shape[0]):
        figure, axes = pyplot.subplots(1, 3, figsize=(10.8, 3.6))
        panels = [(coarse_frames[step], f"coarse solve 8x8 (step {step + 1})"),
                  (sr_frames[step], "superresolved in loop"),
                  (truth[step], "fine solve 32x32 (truth)")]
        for axis, (plane, title) in zip(axes, panels):
            axis.imshow(plane.T, origin="lower", cmap="inferno", **limits)
            axis.set_title(title, fontsize=10)
            axis.set_xticks([])
            axis.set_yticks([])
        figure.tight_layout()
        figure.canvas.draw()
        images.append(Image.fromarray(
            numpy.asarray(figure.canvas.buffer_rgba())[:, :, :3]))
        pyplot.close(figure)
    images[0].save(DATA / "transient_sr.gif", save_all=True,
                   append_images=images[1:], duration=125, loop=0)

    with open(OUTPUT / "deploy_summary.json", "w") as handle:
        json.dump({"mean_sr_rmse": float(sr_errors.mean()),
                   "mean_bilinear_rmse": float(bilinear_errors.mean()),
                   "steps": int(truth.shape[0])}, handle, indent=1)
    print(f"figures: {DATA / 'transient_sr.gif'}, {DATA / 'transient_sr_live.gif'}, "
          f"{DATA / 'transient_sr_error.png'}")


if __name__ == "__main__":
    main()
