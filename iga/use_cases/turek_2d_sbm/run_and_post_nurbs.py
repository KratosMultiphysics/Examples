#!/usr/bin/env python3
"""Run the 2D Turek SBM example and post-process the solution.

This example produces:
- one static image of the final step
- one GIF for velocity magnitude
- one GIF for pressure

Required third-party Python packages:
- numpy
- matplotlib
- imageio

If a LaTeX installation is available, matplotlib uses it for text rendering.
Otherwise the script falls back to Computer Modern mathtext.
"""

from __future__ import annotations

import importlib
import os
import shutil
import sys
import time
from pathlib import Path

import KratosMultiphysics
import KratosMultiphysics.IgaApplication  # registers IGA modelers and conditions

try:
    import numpy as np
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Missing dependency: numpy\n"
        "Install it in the current Python environment before running this example."
    ) from exc

try:
    import matplotlib
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Missing dependency: matplotlib\n"
        "Install it in the current Python environment before running this example."
    ) from exc

if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
    matplotlib.use("Agg")

try:
    import matplotlib.font_manager as font_manager
    import matplotlib.pyplot as plt
    from matplotlib.colors import Normalize
except ModuleNotFoundError as exc:
    raise SystemExit(
        "matplotlib is installed but incomplete in this environment.\n"
        "Please install a full matplotlib package."
    ) from exc

try:
    import imageio.v2 as imageio
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Missing dependency: imageio\n"
        "Install it in the current Python environment before running this example."
    ) from exc

PROJECT_PARAMETERS_FILENAME = "ProjectParameters_2D_fluid.json"
FINAL_SHOT_FILENAME = "final_step_fields.png"
VELOCITY_GIF_FILENAME = "velocity.gif"
PRESSURE_GIF_FILENAME = "pressure.gif"
FRAME_DATA_DIRNAME = "_frame_cache"
VELOCITY_FRAME_DIRNAME = "frames_velocity"
PRESSURE_FRAME_DIRNAME = "frames_pressure"

FRAME_EVERY = 2
GIF_DURATION = 0.05
GIF_PALETTE_SIZE = 64
VELOCITY_COLOR_MAX = 4.5
PRESSURE_COLOR_MIN = -7500.0
PRESSURE_COLOR_MAX = 9500.0
FRAME_DPI = 120
def _configure_matplotlib() -> None:
    def _font_available(font_name: str) -> bool:
        try:
            font_manager.findfont(
                font_manager.FontProperties(family=font_name),
                fallback_to_default=False,
            )
            return True
        except Exception:
            return False

    serif_candidates = [
        "Computer Modern Roman",
        "CMU Serif",
        "DejaVu Serif",
        "Times New Roman",
        "Times",
    ]
    serif_font = next((name for name in serif_candidates if _font_available(name)), None)
    use_tex = shutil.which("latex") is not None

    rc_params = {
        "text.usetex": use_tex,
        "font.family": "serif",
    }
    if serif_font:
        rc_params["font.serif"] = [serif_font]
        if not use_tex and serif_font in {"Computer Modern Roman", "CMU Serif"}:
            rc_params["mathtext.fontset"] = "cm"

    plt.rcParams.update(rc_params)


_configure_matplotlib()


def _require_file(path: Path, description: str) -> None:
    if not path.is_file():
        raise FileNotFoundError(f"Required {description} was not found: {path}")


def _load_parameters(path: Path) -> KratosMultiphysics.Parameters:
    _require_file(path, "project parameter file")
    with path.open("r", encoding="utf-8") as parameter_file:
        return KratosMultiphysics.Parameters(parameter_file.read())


def _load_analysis_stage_class(parameters: KratosMultiphysics.Parameters):
    module_name = parameters["analysis_stage"].GetString()
    class_name = "".join(part.title() for part in module_name.split(".")[-1].split("_"))
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


def _normalize_solver_settings(parameters: KratosMultiphysics.Parameters) -> None:
    if not parameters.Has("solver_settings"):
        raise RuntimeError('Project parameters must contain "solver_settings".')

    solver_settings = parameters["solver_settings"]

    if solver_settings.Has("solver_type"):
        solver_settings["solver_type"].SetString("monolithic_iga")
    else:
        solver_settings.AddEmptyValue("solver_type").SetString("monolithic_iga")

    if solver_settings.Has("time_scheme"):
        if solver_settings["time_scheme"].GetString() == "bdf2":
            solver_settings["time_scheme"].SetString("bdf2_higher_order_vms")
    else:
        solver_settings.AddEmptyValue("time_scheme").SetString("bdf2_higher_order_vms")

    if solver_settings.Has("skip_entities_replace_and_check"):
        solver_settings["skip_entities_replace_and_check"].SetBool(True)
    else:
        solver_settings.AddEmptyValue("skip_entities_replace_and_check").SetBool(True)

    if solver_settings.Has("volume_model_part_name"):
        solver_settings["volume_model_part_name"].SetString("IgaModelPart")
    else:
        solver_settings.AddEmptyValue("volume_model_part_name").SetString("IgaModelPart")

    if solver_settings.Has("skin_parts"):
        solver_settings.RemoveValue("skin_parts")
    if solver_settings.Has("no_skin_parts"):
        solver_settings.RemoveValue("no_skin_parts")


def CreateAnalysisStageWithFlushInstance(cls, global_model, parameters):
    class AnalysisStageWithFlush(cls):
        def __init__(self, model, project_parameters, flush_frequency=10.0):
            super().__init__(model, project_parameters)
            self.flush_frequency = flush_frequency
            self.last_flush = time.time()
            sys.stdout.flush()

        def Initialize(self):
            super().Initialize()
            sys.stdout.flush()

        def InitializeSolutionStep(self):
            current_time = self._GetSolver().GetComputingModelPart().ProcessInfo[
                KratosMultiphysics.TIME
            ]
            if global_model.HasModelPart("skin_model_part"):
                global_model["skin_model_part"].ProcessInfo[KratosMultiphysics.TIME] = current_time
            super().InitializeSolutionStep()

        def FinalizeSolutionStep(self):
            super().FinalizeSolutionStep()
            if self.parallel_type == "OpenMP":
                now = time.time()
                if now - self.last_flush > self.flush_frequency:
                    sys.stdout.flush()
                    self.last_flush = now

    return AnalysisStageWithFlush(global_model, parameters)


def _sample_element_fields(model_part):
    x_coord = []
    y_coord = []
    velx = []
    vely = []
    pressure = []

    for element in model_part.Elements:
        geometry = element.GetGeometry()
        center = geometry.Center()
        x_coord.append(center.X)
        y_coord.append(center.Y)

        n_nodes = len(geometry)
        if n_nodes == 0:
            velx.append(0.0)
            vely.append(0.0)
            pressure.append(0.0)
            continue

        vx = 0.0
        vy = 0.0
        p = 0.0
        for node in geometry:
            vx += node.GetSolutionStepValue(KratosMultiphysics.VELOCITY_X, 0)
            vy += node.GetSolutionStepValue(KratosMultiphysics.VELOCITY_Y, 0)
            p += node.GetSolutionStepValue(KratosMultiphysics.PRESSURE, 0)

        inv_n = 1.0 / n_nodes
        velx.append(vx * inv_n)
        vely.append(vy * inv_n)
        pressure.append(p * inv_n)

    if not x_coord:
        return (
            np.empty((0, 2), dtype=float),
            np.empty((0, 2), dtype=float),
            np.array([], dtype=float),
        )

    points = np.column_stack((x_coord, y_coord))
    velocity = np.column_stack((velx, vely))
    return points, velocity, np.array(pressure, dtype=float)


def _prepare_output_directory(path: Path) -> None:
    if path.is_dir():
        shutil.rmtree(path)
    path.mkdir(parents=True, exist_ok=True)


def _cached_frame_paths(frame_data_dir: Path) -> list[Path]:
    return sorted(frame_data_dir.glob("frame_*.npz"))


def _write_gif(frame_dir: Path, gif_path: Path) -> None:
    frames = sorted(frame_dir.glob("frame_*.png"))
    if not frames:
        raise RuntimeError(f"No PNG frames were written in {frame_dir}. Cannot create {gif_path.name}.")

    with imageio.get_writer(
        gif_path,
        mode="I",
        duration=GIF_DURATION,
        palettesize=GIF_PALETTE_SIZE,
        subrectangles=True,
    ) as writer:
        for frame_path in frames:
            writer.append_data(imageio.imread(frame_path))


def _extract_inner_boundary_outline(model) -> np.ndarray | None:
    def _is_reasonable_outline(points: np.ndarray) -> bool:
        if points.shape[0] < 16:
            return False

        center = points.mean(axis=0)
        radii = np.linalg.norm(points - center, axis=1)
        radii = radii[radii > 1e-12]
        if radii.size < 16:
            return False

        radius_p10 = float(np.percentile(radii, 10.0))
        radius_p90 = float(np.percentile(radii, 90.0))
        if radius_p10 <= 1e-12:
            return False

        # Reject point clouds that contain long connector segments or large radial outliers.
        return (radius_p90 / radius_p10) < 1.35

    candidate_names = (
        "skin_model_part.inner",
        "initial_skin_model_part_in",
        "IgaModelPart.SBM_Support_inner",
    )

    for name in candidate_names:
        if not model.HasModelPart(name):
            continue

        model_part = model[name]
        node_map = {}
        for condition in model_part.Conditions:
            for node in condition.GetGeometry():
                node_map[node.Id] = (node.X, node.Y)
        if not node_map and model_part.NumberOfNodes() > 0:
            for node in model_part.Nodes:
                node_map[node.Id] = (node.X, node.Y)
        if len(node_map) < 3:
            continue

        points = np.array(list(node_map.values()), dtype=float)
        if not _is_reasonable_outline(points):
            continue

        center = points.mean(axis=0)
        angles = np.arctan2(points[:, 1] - center[1], points[:, 0] - center[0])
        return points[np.argsort(angles)]

    return None


def _draw_inner_boundary(ax, boundary_outline: np.ndarray | None) -> None:
    if boundary_outline is None or boundary_outline.shape[0] < 3:
        return

    ax.fill(
        boundary_outline[:, 0],
        boundary_outline[:, 1],
        facecolor="white",
        edgecolor="black",
        linewidth=1.1,
        zorder=4,
    )


def _square_marker_size(ax, x_values: np.ndarray, y_values: np.ndarray) -> float:
    unique_x = np.unique(np.round(x_values, decimals=12))
    unique_y = np.unique(np.round(y_values, decimals=12))

    def _spacing(values: np.ndarray) -> float:
        if values.size <= 1:
            return 1.0
        diffs = np.diff(values)
        diffs = diffs[diffs > 1e-12]
        return float(np.min(diffs)) if diffs.size > 0 else 1.0

    dx = _spacing(unique_x)
    dy = _spacing(unique_y)

    ax.figure.canvas.draw()
    origin = ax.transData.transform((0.0, 0.0))
    dx_px = abs(ax.transData.transform((dx, 0.0))[0] - origin[0]) if dx > 0.0 else 6.0
    dy_px = abs(ax.transData.transform((0.0, dy))[1] - origin[1]) if dy > 0.0 else 6.0
    marker_size_pts = max(dx_px, dy_px) * 72.0 / ax.figure.dpi * 1.08
    return marker_size_pts ** 2


def _plot_field(ax, points, values, title, color_norm, colorbar_label, boundary_outline) -> None:
    x_values = points[:, 0]
    y_values = points[:, 1]
    marker_size = _square_marker_size(ax, x_values, y_values)

    artist = ax.scatter(
        x_values,
        y_values,
        c=values,
        cmap="jet",
        norm=color_norm,
        s=marker_size,
        marker="s",
        linewidths=0.0,
        zorder=3,
    )
    ax.set_title(title)
    ax.set_xlabel(r"$x$")
    ax.set_ylabel(r"$y$")
    ax.set_facecolor("white")
    ax.set_aspect("equal")
    ax.set_xlim(float(x_values.min()), float(x_values.max()))
    ax.set_ylim(float(y_values.min()), float(y_values.max()))
    _draw_inner_boundary(ax, boundary_outline)
    plt.colorbar(artist, ax=ax, shrink=0.92, pad=0.02, label=colorbar_label)


def _save_single_field_frame(
    frame_path: Path,
    points,
    values,
    title,
    color_norm,
    colorbar_label,
    boundary_outline,
) -> None:
    fig, ax = plt.subplots(figsize=(9, 4.8))
    _plot_field(ax, points, values, title, color_norm, colorbar_label, boundary_outline)
    fig.tight_layout()
    fig.savefig(frame_path, dpi=FRAME_DPI)
    plt.close(fig)


def _save_final_shot(
    figure_path: Path,
    points,
    velocity_magnitude,
    pressure,
    velocity_norm,
    pressure_norm,
    boundary_outline,
) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 5))
    _plot_field(
        axes[0],
        points,
        velocity_magnitude,
        r"Final velocity magnitude $|\mathbf{v}|$",
        velocity_norm,
        r"$|\mathbf{v}|$",
        boundary_outline,
    )
    _plot_field(
        axes[1],
        points,
        pressure,
        r"Final pressure $p$",
        pressure_norm,
        r"$p$",
        boundary_outline,
    )
    fig.tight_layout()
    fig.savefig(figure_path, dpi=160)
    plt.close(fig)


def _cache_frame_data(
    frame_data_dir: Path,
    frame_index: int,
    time_value: float,
    points,
    velocity_magnitude,
    pressure,
) -> None:
    cache_path = frame_data_dir / f"frame_{frame_index:06d}.npz"
    np.savez_compressed(
        cache_path,
        time=np.array([time_value], dtype=float),
        points=points,
        velocity_magnitude=velocity_magnitude,
        pressure=pressure,
    )


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    project_parameters_path = script_dir / PROJECT_PARAMETERS_FILENAME
    final_shot_path = script_dir / FINAL_SHOT_FILENAME
    velocity_frame_dir = script_dir / VELOCITY_FRAME_DIRNAME
    pressure_frame_dir = script_dir / PRESSURE_FRAME_DIRNAME
    frame_data_dir = script_dir / FRAME_DATA_DIRNAME
    velocity_gif_path = script_dir / VELOCITY_GIF_FILENAME
    pressure_gif_path = script_dir / PRESSURE_GIF_FILENAME

    parameters = _load_parameters(project_parameters_path)
    _normalize_solver_settings(parameters)

    _prepare_output_directory(frame_data_dir)
    _prepare_output_directory(velocity_frame_dir)
    _prepare_output_directory(pressure_frame_dir)

    analysis_stage_class = _load_analysis_stage_class(parameters)
    global_model = KratosMultiphysics.Model()
    simulation = CreateAnalysisStageWithFlushInstance(
        analysis_stage_class,
        global_model,
        parameters,
    )

    simulation.Initialize()
    boundary_outline = _extract_inner_boundary_outline(global_model)
    if boundary_outline is None:
        print(
            "Warning: could not reconstruct a clean immersed-boundary outline for plotting. "
            "The obstacle fill will be skipped."
        )

    final_frame_path = None
    frame_index = 0

    while simulation.KeepAdvancingSolutionLoop():
        simulation.time = simulation._AdvanceTime()
        simulation.InitializeSolutionStep()
        simulation._GetSolver().Predict()
        simulation._GetSolver().SolveSolutionStep()
        simulation.FinalizeSolutionStep()
        simulation.OutputSolutionStep()

        if not global_model.HasModelPart("IgaModelPart"):
            raise RuntimeError('Expected model part "IgaModelPart" was not created.')

        model_part = global_model["IgaModelPart"]
        points, velocity, pressure = _sample_element_fields(model_part)
        if points.size == 0:
            raise RuntimeError("No element data were found for plotting.")

        velocity_magnitude = np.linalg.norm(velocity, axis=1)

        if frame_index % FRAME_EVERY == 0:
            time_value = float(model_part.ProcessInfo[KratosMultiphysics.TIME])
            _cache_frame_data(
                frame_data_dir,
                frame_index,
                time_value,
                points,
                velocity_magnitude,
                pressure,
            )
            final_frame_path = frame_data_dir / f"frame_{frame_index:06d}.npz"

            # Write preview frames immediately so users can inspect progress while the solve runs.
            preview_velocity_norm = Normalize(vmin=0.0, vmax=VELOCITY_COLOR_MAX)
            preview_pressure_norm = Normalize(vmin=PRESSURE_COLOR_MIN, vmax=PRESSURE_COLOR_MAX)

            frame_suffix = f"frame_{frame_index:06d}.png"
            time_label = rf"$t = {time_value:.3f}$"
            _save_single_field_frame(
                velocity_frame_dir / frame_suffix,
                points,
                velocity_magnitude,
                rf"Velocity magnitude $|\mathbf{{v}}|$, {time_label}",
                preview_velocity_norm,
                r"$|\mathbf{v}|$",
                boundary_outline,
            )
            _save_single_field_frame(
                pressure_frame_dir / frame_suffix,
                points,
                pressure,
                rf"Pressure $p$, {time_label}",
                preview_pressure_norm,
                r"$p$",
                boundary_outline,
            )

        frame_index += 1

    simulation.Finalize()

    if final_frame_path is None or not final_frame_path.is_file():
        raise RuntimeError("No frame data were cached during the simulation.")

    velocity_norm = Normalize(vmin=0.0, vmax=VELOCITY_COLOR_MAX)
    pressure_norm = Normalize(vmin=PRESSURE_COLOR_MIN, vmax=PRESSURE_COLOR_MAX)

    cached_paths = _cached_frame_paths(frame_data_dir)
    if not cached_paths:
        raise RuntimeError(f"No cached frame data were found in {frame_data_dir}.")

    print(
        "Simulation finished. Rendering "
        f"{len(cached_paths)} cached frames for velocity and pressure GIFs..."
    )

    for frame_counter, cache_path in enumerate(cached_paths, start=1):
        with np.load(cache_path) as data:
            points = data["points"]
            velocity_magnitude = data["velocity_magnitude"]
            pressure = data["pressure"]
            time_value = float(data["time"][0])

        frame_suffix = cache_path.stem + ".png"
        time_label = rf"$t = {time_value:.3f}$"

        _save_single_field_frame(
            velocity_frame_dir / frame_suffix,
            points,
            velocity_magnitude,
            rf"Velocity magnitude $|\mathbf{{v}}|$, {time_label}",
            velocity_norm,
            r"$|\mathbf{v}|$",
            boundary_outline,
        )
        _save_single_field_frame(
            pressure_frame_dir / frame_suffix,
            points,
            pressure,
            rf"Pressure $p$, {time_label}",
            pressure_norm,
            r"$p$",
            boundary_outline,
        )

        if frame_counter % 25 == 0 or frame_counter == len(cached_paths):
            print(f"Rendered {frame_counter}/{len(cached_paths)} frames")

    with np.load(final_frame_path) as final_data:
        final_points = final_data["points"]
        final_velocity_magnitude = final_data["velocity_magnitude"]
        final_pressure = final_data["pressure"]

    _save_final_shot(
        final_shot_path,
        final_points,
        final_velocity_magnitude,
        final_pressure,
        velocity_norm,
        pressure_norm,
        boundary_outline,
    )
    _write_gif(velocity_frame_dir, velocity_gif_path)
    _write_gif(pressure_frame_dir, pressure_gif_path)

    print(f"Saved {final_shot_path}")
    print(f"Saved {velocity_gif_path}")
    print(f"Saved {pressure_gif_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
