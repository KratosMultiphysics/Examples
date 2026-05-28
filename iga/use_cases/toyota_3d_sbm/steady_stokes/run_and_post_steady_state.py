#!/usr/bin/env python3
"""Steady Toyota post-processing example."""

import importlib
import os

import KratosMultiphysics
import KratosMultiphysics.IgaApplication
import numpy as np

try:
    import matplotlib

    if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
        matplotlib.use("Agg")

    import matplotlib.font_manager as font_manager
    import matplotlib.pyplot as plt
    from matplotlib.colors import Normalize
    from matplotlib.ticker import MaxNLocator, StrMethodFormatter
    from mpl_toolkits.mplot3d.art3d import Poly3DCollection

    HAVE_MPL = True

    def _font_available(font_name):
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
    rc_params = {
        "text.usetex": False,
        "font.family": "serif",
    }
    if serif_font:
        rc_params["font.serif"] = [serif_font]
        if serif_font in {"Computer Modern Roman", "CMU Serif"}:
            rc_params["mathtext.fontset"] = "cm"
    plt.rcParams.update(rc_params)
except ModuleNotFoundError:
    HAVE_MPL = False
    plt = None
    Normalize = None
    Poly3DCollection = None

PLOT_SWAP_Z_TO_X = True
PLOT_MODEL_PART_NAME = "IgaModelPart"
CAMERA_ELEV = 20.0
CAMERA_AZIM = 322.0
VELOCITY_COLOR_MAX = 4.5


def _map_points(points):
    if not PLOT_SWAP_Z_TO_X or points.size == 0:
        return points
    return points[:, [0, 2, 1]]


def _axis_labels():
    return ("X", "Z", "Y") if PLOT_SWAP_Z_TO_X else ("X", "Y", "Z")


def _normalize_solver_settings(parameters):
    if not parameters.Has("solver_settings"):
        return

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


def _load_analysis_stage_class(parameters):
    module_name = parameters["analysis_stage"].GetString()
    class_name = "".join(part.title() for part in module_name.split(".")[-1].split("_"))
    module = importlib.import_module(module_name)
    return getattr(module, class_name)


def _sample_element_fields(model_part):
    x_coord = []
    y_coord = []
    z_coord = []
    velx = []
    vely = []
    velz = []
    pressure = []

    for element in model_part.Elements:
        geometry = element.GetGeometry()
        center = geometry.Center()
        x_coord.append(center.X)
        y_coord.append(center.Y)
        z_coord.append(center.Z)

        n_nodes = len(geometry)
        if n_nodes == 0:
            velx.append(0.0)
            vely.append(0.0)
            velz.append(0.0)
            pressure.append(0.0)
            continue

        vx = 0.0
        vy = 0.0
        vz = 0.0
        p = 0.0
        for node in geometry:
            vx += node.GetSolutionStepValue(KratosMultiphysics.VELOCITY_X, 0)
            vy += node.GetSolutionStepValue(KratosMultiphysics.VELOCITY_Y, 0)
            vz += node.GetSolutionStepValue(KratosMultiphysics.VELOCITY_Z, 0)
            p += node.GetSolutionStepValue(KratosMultiphysics.PRESSURE, 0)

        inv_n = 1.0 / n_nodes
        velx.append(vx * inv_n)
        vely.append(vy * inv_n)
        velz.append(vz * inv_n)
        pressure.append(p * inv_n)

    points = np.column_stack((x_coord, y_coord, z_coord))
    velocity = np.column_stack((velx, vely, velz))
    return points, velocity, np.array(pressure, dtype=float)


def _extract_x_plane_layer(points, values, x_target=0.0):
    if points.size == 0 or values.size == 0:
        return None, None, None

    rounded_x = np.round(points[:, 0], decimals=12)
    unique_x = np.unique(rounded_x)
    if unique_x.size == 0:
        return None, None, None

    plane_x = float(unique_x[np.argmin(np.abs(unique_x - x_target))])
    mask = np.isclose(rounded_x, plane_x, atol=1e-12)
    if not np.any(mask):
        return None, None, None

    return points[mask], values[mask], plane_x


def _square_marker_size(ax, coordinates_a, coordinates_b):
    unique_a = np.unique(np.round(coordinates_a, decimals=12))
    unique_b = np.unique(np.round(coordinates_b, decimals=12))

    def _spacing(values):
        if values.size <= 1:
            return 1.0
        diffs = np.diff(values)
        diffs = diffs[diffs > 1e-12]
        return float(np.min(diffs)) if diffs.size > 0 else 1.0

    da = _spacing(unique_a)
    db = _spacing(unique_b)

    ax.figure.canvas.draw()
    origin = ax.transData.transform((0.0, 0.0))
    da_px = abs(ax.transData.transform((da, 0.0))[0] - origin[0]) if da > 0.0 else 6.0
    db_px = abs(ax.transData.transform((0.0, db))[1] - origin[1]) if db > 0.0 else 6.0
    marker_size_pts = max(da_px, db_px) * 72.0 / ax.figure.dpi * 1.08
    return marker_size_pts ** 2


def _plot_x_plane(ax, plane_points, plane_values, color_norm):
    y = plane_points[:, 1]
    z = plane_points[:, 2]
    marker_size = _square_marker_size(ax, z, y)

    artist = ax.scatter(
        z,
        y,
        c=plane_values,
        cmap="jet",
        norm=color_norm,
        s=marker_size,
        marker="s",
        linewidths=0.0,
    )
    ax.set_facecolor("white")
    ax.set_xlabel(r"$Z$")
    ax.set_ylabel(r"$Y$")
    ax.xaxis.set_major_locator(MaxNLocator(nbins=5))
    ax.xaxis.set_major_formatter(StrMethodFormatter("{x:.2f}"))
    ax.yaxis.set_major_locator(MaxNLocator(nbins=5))
    ax.yaxis.set_major_formatter(StrMethodFormatter("{x:.2f}"))
    ax.set_aspect("equal")
    return artist


def _collect_surrogate_faces(model):
    names = []
    try:
        names = list(model.GetModelPartNames())
    except Exception:
        pass

    target_names = []
    for base_name in ("IgaModelPart.surrogate_inner", "IgaModelPart.surrogate_outer"):
        if model.HasModelPart(base_name):
            target_names.append(base_name)
    for name in names:
        if name.endswith(".surrogate_inner") or name.endswith(".surrogate_outer"):
            if name not in target_names:
                target_names.append(name)

    faces = []
    for name in target_names:
        if not model.HasModelPart(name):
            continue
        model_part = model[name]
        for condition in model_part.Conditions:
            geometry = condition.GetGeometry()
            face = [(node.X, node.Y, node.Z) for node in geometry]
            if len(face) >= 3:
                faces.append(face)
    return faces


def _add_surrogate_faces(ax, faces, alpha):
    for face in faces:
        if len(face) < 3:
            continue

        v1 = np.array(face[1]) - np.array(face[0])
        v2 = np.array(face[2]) - np.array(face[0])
        normal = np.cross(v1, v2)
        norm = np.linalg.norm(normal)
        if norm == 0.0:
            continue

        normal /= norm
        direction = int(np.argmax(np.abs(normal)))
        if direction == 0:
            face_color = (1.0, 0.7, 0.7)
        elif direction == 1:
            face_color = (0.7, 1.0, 0.7)
        else:
            face_color = (0.7, 0.7, 1.0)

        poly = Poly3DCollection([face], alpha=alpha, edgecolor="k", facecolor=face_color)
        poly.set_zsort("max")
        ax.add_collection3d(poly)


def _set_3d_axes(ax, bounds, axis_labels):
    x_min, x_max, y_min, y_max, z_min, z_max = bounds
    x_span = x_max - x_min
    y_span = y_max - y_min
    z_span = z_max - z_min

    if PLOT_SWAP_Z_TO_X:
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(z_min, z_max)
        ax.set_zlim(y_min, y_max)
        ax.set_box_aspect((x_span, z_span, y_span))
    else:
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        ax.set_zlim(z_min, z_max)
        ax.set_box_aspect((x_span, y_span, z_span))

    ax.set_xlabel(axis_labels[0])
    ax.set_ylabel(axis_labels[1])
    ax.set_zlabel(axis_labels[2])
    ax.xaxis.set_major_locator(MaxNLocator(nbins=3))
    ax.xaxis.set_major_formatter(StrMethodFormatter("{x:.2f}"))
    ax.view_init(elev=CAMERA_ELEV, azim=CAMERA_AZIM)


def main():
    if not HAVE_MPL:
        print("matplotlib not installed; cannot generate plots.")
        return 1

    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_parameters_path = os.path.join(script_dir, "ProjectParameters_3D_fluid_steady_state.json")
    output_3d_path = os.path.join(script_dir, "steady_3d_velocity_pressure.png")
    output_plane_velocity_path = os.path.join(script_dir, "steady_plane_x0_velocity.png")
    output_plane_pressure_path = os.path.join(script_dir, "steady_plane_x0_pressure.png")

    with open(project_parameters_path, "r") as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())
    _normalize_solver_settings(parameters)

    analysis_stage_class = _load_analysis_stage_class(parameters)
    model = KratosMultiphysics.Model()
    simulation = analysis_stage_class(model, parameters)
    simulation.Run()

    if not model.HasModelPart(PLOT_MODEL_PART_NAME):
        print(f"ModelPart {PLOT_MODEL_PART_NAME} not found.")
        return 1

    model_part = model[PLOT_MODEL_PART_NAME]
    points, velocity, pressure = _sample_element_fields(model_part)
    if points.size == 0:
        print("No element data found for plotting.")
        return 1

    x_min, x_max = float(points[:, 0].min()), float(points[:, 0].max())
    y_min, y_max = float(points[:, 1].min()), float(points[:, 1].max())
    z_min, z_max = float(points[:, 2].min()), float(points[:, 2].max())
    bounds = (x_min, x_max, y_min, y_max, z_min, z_max)
    axis_labels = _axis_labels()

    surrogate_faces = _collect_surrogate_faces(model)
    velocity_magnitude = np.linalg.norm(velocity, axis=1)
    velocity_norm = Normalize(vmin=0.0, vmax=VELOCITY_COLOR_MAX)

    mask_x = points[:, 0] < 0.0
    points_cut = points[mask_x]
    velocity_cut = velocity_magnitude[mask_x]
    pressure_cut = pressure[mask_x]
    plot_points_cut = _map_points(points_cut)

    fig_3d = plt.figure(figsize=(16, 7))
    ax_velocity = fig_3d.add_subplot(1, 2, 1, projection="3d")
    _set_3d_axes(ax_velocity, bounds, axis_labels)
    ax_velocity.set_title("Velocity Magnitude (3D Contour)")
    if surrogate_faces:
        faces = [_map_points(np.array(face, dtype=float)).tolist() for face in surrogate_faces]
        _add_surrogate_faces(ax_velocity, faces, alpha=0.18)
    velocity_artist = ax_velocity.scatter(
        plot_points_cut[:, 0],
        plot_points_cut[:, 1],
        plot_points_cut[:, 2],
        c=velocity_cut,
        cmap="jet",
        norm=velocity_norm,
        s=6,
        linewidths=0,
        alpha=0.85,
    )
    plt.colorbar(velocity_artist, ax=ax_velocity, shrink=0.8, pad=0.03, label=r"$|v|$")

    ax_pressure = fig_3d.add_subplot(1, 2, 2, projection="3d")
    _set_3d_axes(ax_pressure, bounds, axis_labels)
    ax_pressure.set_title("Pressure (3D Contour)")
    if surrogate_faces:
        faces = [_map_points(np.array(face, dtype=float)).tolist() for face in surrogate_faces]
        _add_surrogate_faces(ax_pressure, faces, alpha=0.18)
    pressure_artist = ax_pressure.scatter(
        plot_points_cut[:, 0],
        plot_points_cut[:, 1],
        plot_points_cut[:, 2],
        c=pressure_cut,
        cmap="jet",
        s=6,
        linewidths=0,
        alpha=0.85,
    )
    plt.colorbar(pressure_artist, ax=ax_pressure, shrink=0.8, pad=0.03, label=r"$p$")
    plt.tight_layout()
    plt.savefig(output_3d_path, dpi=200)
    plt.close(fig_3d)

    plane_points_velocity, plane_values_velocity, plane_x_velocity = _extract_x_plane_layer(
        points,
        velocity_magnitude,
    )
    if plane_points_velocity is not None and plane_points_velocity.size > 0:
        fig_plane_velocity, ax_plane_velocity = plt.subplots(figsize=(8, 6))
        plane_velocity_artist = _plot_x_plane(
            ax_plane_velocity,
            plane_points_velocity,
            plane_values_velocity,
            velocity_norm,
        )
        ax_plane_velocity.set_title(rf"Velocity Magnitude at $x \approx {plane_x_velocity:.3f}$")
        plt.colorbar(
            plane_velocity_artist,
            ax=ax_plane_velocity,
            shrink=0.9,
            pad=0.03,
            label=r"$|v|$",
        )
        plt.tight_layout()
        plt.savefig(output_plane_velocity_path, dpi=200, bbox_inches="tight", pad_inches=0.02)
        plt.close(fig_plane_velocity)

    plane_points_pressure, plane_values_pressure, plane_x_pressure = _extract_x_plane_layer(
        points,
        pressure,
    )
    if plane_points_pressure is not None and plane_points_pressure.size > 0:
        fig_plane_pressure, ax_plane_pressure = plt.subplots(figsize=(8, 6))
        plane_pressure_artist = _plot_x_plane(
            ax_plane_pressure,
            plane_points_pressure,
            plane_values_pressure,
            None,
        )
        ax_plane_pressure.set_title(rf"Pressure at $x \approx {plane_x_pressure:.3f}$")
        plt.colorbar(
            plane_pressure_artist,
            ax=ax_plane_pressure,
            shrink=0.9,
            pad=0.03,
            label=r"$p$",
        )
        plt.tight_layout()
        plt.savefig(output_plane_pressure_path, dpi=200, bbox_inches="tight", pad_inches=0.02)
        plt.close(fig_plane_pressure)

    print(f"Saved {output_3d_path}")
    print(f"Saved {output_plane_velocity_path}")
    print(f"Saved {output_plane_pressure_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
