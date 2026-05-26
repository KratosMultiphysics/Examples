#!/usr/bin/env python3
"""Plot the 2D Turek SBM geometry.

This script visualizes:
- the background Cartesian mesh
- the skin boundary stored in `skin_model_part`
- the surrogate inner boundary

It only executes the modelers. It does not run the fluid solve.
"""

from __future__ import annotations

import importlib
import os
import shutil
from pathlib import Path

import KratosMultiphysics
import KratosMultiphysics.IgaApplication  # registers IGA modelers

try:
    import numpy as np
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Missing dependency: numpy\n"
        "Install it in the current Python environment before running this script."
    ) from exc

try:
    import matplotlib
except ModuleNotFoundError as exc:
    raise SystemExit(
        "Missing dependency: matplotlib\n"
        "Install it in the current Python environment before running this script."
    ) from exc

if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
    matplotlib.use("Agg")

try:
    import matplotlib.font_manager as font_manager
    import matplotlib.pyplot as plt
except ModuleNotFoundError as exc:
    raise SystemExit(
        "matplotlib is installed but incomplete in this environment.\n"
        "Please install a full matplotlib package."
    ) from exc


PROJECT_PARAMETERS_FILENAME = "ProjectParameters_2D_fluid.json"
OUTPUT_FILENAME = "geometry_plot.png"
SHOW_PLOT = bool(os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
MAX_SKIN_SEGMENTS_TO_PLOT = 12000


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


def _normalize_solver_settings(parameters: KratosMultiphysics.Parameters) -> None:
    if not parameters.Has("solver_settings"):
        raise RuntimeError('Project parameters must contain "solver_settings".')

    solver_settings = parameters["solver_settings"]
    if solver_settings.Has("solver_type"):
        solver_settings["solver_type"].SetString("monolithic_iga")
    else:
        solver_settings.AddEmptyValue("solver_type").SetString("monolithic_iga")

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


def _execute_modelers(parameters: KratosMultiphysics.Parameters, model: KratosMultiphysics.Model) -> None:
    if not model.HasModelPart("IgaModelPart"):
        model.CreateModelPart("IgaModelPart")

    for modeler_data in parameters["modelers"].values():
        if not modeler_data.Has("modeler_name"):
            continue

        modeler_name = modeler_data["modeler_name"].GetString()
        modeler_parameters = modeler_data["Parameters"]

        if KratosMultiphysics.HasModeler(modeler_name):
            modeler = KratosMultiphysics.CreateModeler(modeler_name, model, modeler_parameters)
        else:
            if not modeler_data.Has("kratos_module"):
                raise RuntimeError(f'Python modeler "{modeler_name}" is missing "kratos_module".')

            kratos_module_name = modeler_data["kratos_module"].GetString()
            if not kratos_module_name.startswith("KratosMultiphysics"):
                kratos_module_name = "KratosMultiphysics." + kratos_module_name
            python_modeler_name = kratos_module_name + ".modelers." + modeler_name
            python_module = importlib.import_module(python_modeler_name)
            modeler = python_module.Factory(model, modeler_parameters)

        setup_geometry = getattr(modeler, "SetupGeometryModel", None)
        if callable(setup_geometry):
            setup_geometry()

        prepare_geometry = getattr(modeler, "PrepareGeometryModel", None)
        if callable(prepare_geometry):
            prepare_geometry()

        setup_model_part = getattr(modeler, "SetupModelPart", None)
        if callable(setup_model_part):
            setup_model_part()


def _read_background_bounds(parameters: KratosMultiphysics.Parameters) -> tuple[float, float, float, float]:
    for modeler_data in parameters["modelers"].values():
        if not modeler_data.Has("modeler_name"):
            continue
        if modeler_data["modeler_name"].GetString() != "NurbsGeometryModelerSbm":
            continue

        modeler_parameters = modeler_data["Parameters"]
        lower = modeler_parameters["lower_point_xyz"]
        upper = modeler_parameters["upper_point_xyz"]
        return (
            lower[0].GetDouble(),
            upper[0].GetDouble(),
            lower[1].GetDouble(),
            upper[1].GetDouble(),
        )

    raise RuntimeError('Could not find "NurbsGeometryModelerSbm" bounds in project parameters.')


def _knot_lines(model_part) -> tuple[np.ndarray, np.ndarray]:
    if not model_part.Has(KratosMultiphysics.KratosGlobals.GetVariable("KNOT_VECTOR_U")):
        raise RuntimeError("IgaModelPart is missing KNOT_VECTOR_U.")
    if not model_part.Has(KratosMultiphysics.KratosGlobals.GetVariable("KNOT_VECTOR_V")):
        raise RuntimeError("IgaModelPart is missing KNOT_VECTOR_V.")

    knot_vector_u = np.array(model_part.GetValue(KratosMultiphysics.KratosGlobals.GetVariable("KNOT_VECTOR_U")), dtype=float)
    knot_vector_v = np.array(model_part.GetValue(KratosMultiphysics.KratosGlobals.GetVariable("KNOT_VECTOR_V")), dtype=float)
    return np.unique(np.round(knot_vector_u, decimals=12)), np.unique(np.round(knot_vector_v, decimals=12))


def _collect_surrogate_segments(model) -> list[np.ndarray]:
    candidate_names = (
        "IgaModelPart.surrogate_inner",
        "IgaModelPart.SBM_Support_inner",
    )

    segments = []
    seen = set()
    for name in candidate_names:
        if not model.HasModelPart(name):
            continue

        for condition in model[name].Conditions:
            geometry = condition.GetGeometry()
            if geometry.PointsNumber() != 2:
                continue

            segment = np.array(
                [[geometry[0].X, geometry[0].Y], [geometry[1].X, geometry[1].Y]],
                dtype=float,
            )
            key = tuple(np.round(segment.reshape(-1), 12))
            if key in seen:
                continue
            seen.add(key)
            segments.append(segment)

    return segments


def _collect_skin_boundary_segments(model) -> list[np.ndarray]:
    candidate_names = (
        "skin_model_part.inner",
        "skin_model_part.inner.Layer0",
    )

    segments = []
    seen = set()
    for name in candidate_names:
        if not model.HasModelPart(name):
            continue

        model_part = model[name]
        for condition in model_part.Conditions:
            geometry = condition.GetGeometry()
            if geometry.PointsNumber() != 2:
                continue

            segment = np.array(
                [[geometry[0].X, geometry[0].Y], [geometry[1].X, geometry[1].Y]],
                dtype=float,
            )
            p0 = tuple(np.round(segment[0], 12))
            p1 = tuple(np.round(segment[1], 12))
            key = tuple(sorted((p0, p1)))
            if key in seen:
                continue
            seen.add(key)
            segments.append(segment)

    if len(segments) > MAX_SKIN_SEGMENTS_TO_PLOT:
        stride = int(np.ceil(len(segments) / MAX_SKIN_SEGMENTS_TO_PLOT))
        segments = segments[::stride]

    return segments


def main() -> int:
    script_dir = Path(__file__).resolve().parent
    project_parameters_path = script_dir / PROJECT_PARAMETERS_FILENAME
    output_path = script_dir / OUTPUT_FILENAME

    parameters = _load_parameters(project_parameters_path)
    _normalize_solver_settings(parameters)

    model = KratosMultiphysics.Model()
    _execute_modelers(parameters, model)

    if not model.HasModelPart("IgaModelPart"):
        raise RuntimeError('Modeler execution did not create "IgaModelPart".')

    iga_model_part = model["IgaModelPart"]
    x_min, x_max, y_min, y_max = _read_background_bounds(parameters)
    knot_lines_u, knot_lines_v = _knot_lines(iga_model_part)
    skin_boundary_segments = _collect_skin_boundary_segments(model)
    surrogate_segments = _collect_surrogate_segments(model)

    fig, ax = plt.subplots(figsize=(9, 4.8))

    for x_value in knot_lines_u:
        ax.plot([x_value, x_value], [y_min, y_max], color="#d9d9d9", linewidth=0.55, zorder=1)
    for y_value in knot_lines_v:
        ax.plot([x_min, x_max], [y_value, y_value], color="#d9d9d9", linewidth=0.55, zorder=1)

    for segment in skin_boundary_segments:
        ax.plot(segment[:, 0], segment[:, 1], color="#1f77b4", linewidth=0.7, alpha=0.7, zorder=2)

    for segment in surrogate_segments:
        ax.plot(segment[:, 0], segment[:, 1], color="#d62728", linewidth=1.2, zorder=3)

    ax.set_title(r"2D Turek geometry: mesh, skin boundary, surrogate boundary")
    ax.set_xlabel(r"$x$")
    ax.set_ylabel(r"$y$")
    ax.set_aspect("equal")
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.grid(False)

    legend_handles = [
        plt.Line2D([0], [0], color="#d9d9d9", linewidth=1.0, label="Background mesh"),
        plt.Line2D([0], [0], color="#1f77b4", linewidth=0.7, alpha=0.7, label="Skin boundary"),
        plt.Line2D([0], [0], color="#d62728", linewidth=1.2, label="Surrogate boundary"),
    ]
    ax.legend(handles=legend_handles, loc="upper right", frameon=True)

    fig.tight_layout()
    fig.savefig(output_path, dpi=180)
    if SHOW_PLOT:
        plt.show()
    plt.close(fig)

    print(f"Saved {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
