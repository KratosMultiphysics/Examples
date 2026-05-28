#!/usr/bin/env python3
"""Transient Toyota post-processing example."""

import importlib
import os
import shutil

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
    from mpl_toolkits.axes_grid1 import make_axes_locatable

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

try:
    import imageio.v2 as imageio

    HAVE_IMAGEIO = True
except ModuleNotFoundError:
    HAVE_IMAGEIO = False
    imageio = None

PLOT_SWAP_Z_TO_X = True
PLOT_MODEL_PART_NAME = "IgaModelPart"
PROJECT_PARAMETERS_FILENAME = "ProjectParameters_3D_fluid.json"

WRITE_3D_CUT_GIF = True
WRITE_VELOCITY_PLANE_GIF = True
WRITE_PRESSURE_PLANE_GIF = True

CAMERA_ELEV = 20.0
CAMERA_AZIM = 322.0
COLORBAR_MAX = 4.5
FRAME_EVERY = 1
FIG_DPI = 120
GIF_DURATION = 0.05
GIF_PALETTE_SIZE = 64

CUT_FRAME_DIRNAME = "frames_time_cut_contour"
VELOCITY_PLANE_FRAME_DIRNAME = "frames_time_velocity_magnitude_x0"
PRESSURE_PLANE_FRAME_DIRNAME = "frames_time_pressure_x0"

CUT_GIF_FILENAME = "cut_contour_x_lt_0.gif"
VELOCITY_PLANE_GIF_FILENAME = "velocity_magnitude_x_eq_0_contour.gif"
PRESSURE_PLANE_GIF_FILENAME = "pressure_x_eq_0_contour.gif"

PLANE_FIGSIZE = (8.0, 6.0)
PLANE_TITLE_SIZE = 14
PLANE_LABEL_SIZE = 13
PLANE_TICK_SIZE = 11
PLANE_COLORBAR_LABEL_SIZE = 13
PLANE_COLORBAR_TICK_SIZE = 11
PLANE_COLORBAR_SIZE = "4%"
PLANE_COLORBAR_PAD = 0.08
PLANE_COLORBAR_NBINS = 6

def _map_points(points):
    if not PLOT_SWAP_Z_TO_X or points.size == 0:
        return points
    return points[:, [0, 2, 1]]


def _normalize_solver_settings(parameters):
    if not parameters.Has("solver_settings"):
        return

    solver_settings = parameters["solver_settings"]

    if solver_settings.Has("solver_type"):
        solver_settings["solver_type"].SetString("monolithic_iga")
    else:
        solver_settings.AddEmptyValue("solver_type").SetString("monolithic_iga")

    if solver_settings.Has("time_scheme"):
        time_scheme = solver_settings["time_scheme"].GetString()
        if time_scheme == "bdf2":
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


def _plot_x_plane(ax, plane_points, plane_values, color_norm, cmap="jet"):
    y = plane_points[:, 1]
    z = plane_points[:, 2]

    marker_size = _square_marker_size(ax, z, y)

    artist = ax.scatter(
        z,
        y,
        c=plane_values,
        cmap=cmap,
        norm=color_norm,
        s=marker_size,
        marker="s",
        linewidths=0.0,
        rasterized=True,
    )

    ax.set_facecolor("white")
    ax.set_xlabel(r"$Z$", fontsize=PLANE_LABEL_SIZE)
    ax.set_ylabel(r"$Y$", fontsize=PLANE_LABEL_SIZE)

    if z.size:
        ax.set_xlim(float(z.min()), float(z.max()))
    if y.size:
        ax.set_ylim(float(y.min()), float(y.max()))

    ax.margins(x=0.0, y=0.0)
    ax.xaxis.set_major_locator(MaxNLocator(nbins=5))
    ax.xaxis.set_major_formatter(StrMethodFormatter("{x:.2f}"))
    ax.yaxis.set_major_locator(MaxNLocator(nbins=5))
    ax.yaxis.set_major_formatter(StrMethodFormatter("{x:.2f}"))

    ax.tick_params(axis="both", which="major", labelsize=PLANE_TICK_SIZE)
    ax.set_aspect("equal", adjustable="box")

    return artist

def _add_2d_colorbar(fig, ax, artist, label):
    divider = make_axes_locatable(ax)
    cax = divider.append_axes(
        "right",
        size=PLANE_COLORBAR_SIZE,
        pad=PLANE_COLORBAR_PAD,
    )

    colorbar = fig.colorbar(
        artist,
        cax=cax,
    )

    colorbar.set_label(label, fontsize=PLANE_COLORBAR_LABEL_SIZE)
    colorbar.ax.tick_params(labelsize=PLANE_COLORBAR_TICK_SIZE)
    colorbar.locator = MaxNLocator(nbins=PLANE_COLORBAR_NBINS)
    colorbar.update_ticks()

    return colorbar

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


def _set_3d_axes(ax, bounds):
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

    ax.set_xlabel("")
    ax.set_ylabel("")
    ax.set_zlabel("")
    ax.set_xticks([])
    ax.view_init(elev=CAMERA_ELEV, azim=CAMERA_AZIM)


def _prepare_output_directory(path):
    if os.path.isdir(path):
        shutil.rmtree(path)
    os.makedirs(path, exist_ok=True)


def _write_gif(frame_dir, gif_path):
    if not HAVE_IMAGEIO:
        print(f"imageio not installed; skipped GIF {gif_path}")
        return

    frames = sorted(
        os.path.join(frame_dir, name)
        for name in os.listdir(frame_dir)
        if name.endswith(".png")
    )
    if not frames:
        print(f"No frames found for {gif_path}")
        return

    with imageio.get_writer(
        gif_path,
        mode="I",
        duration=GIF_DURATION,
        palettesize=GIF_PALETTE_SIZE,
        subrectangles=True,
    ) as writer:
        for frame_path in frames:
            writer.append_data(imageio.imread(frame_path))
    print(f"Saved GIF: {gif_path}")


def _save_frame(fig, output_path):
    fig.savefig(output_path, dpi=FIG_DPI)


def main():
    if not HAVE_MPL:
        print("matplotlib not installed; cannot generate plots.")
        return 1

    script_dir = os.path.dirname(os.path.abspath(__file__))
    cut_frame_dir = os.path.join(script_dir, CUT_FRAME_DIRNAME)
    velocity_plane_frame_dir = os.path.join(script_dir, VELOCITY_PLANE_FRAME_DIRNAME)
    pressure_plane_frame_dir = os.path.join(script_dir, PRESSURE_PLANE_FRAME_DIRNAME)

    cut_gif_path = os.path.join(script_dir, CUT_GIF_FILENAME)
    velocity_plane_gif_path = os.path.join(script_dir, VELOCITY_PLANE_GIF_FILENAME)
    pressure_plane_gif_path = os.path.join(script_dir, PRESSURE_PLANE_GIF_FILENAME)

    if WRITE_3D_CUT_GIF:
        _prepare_output_directory(cut_frame_dir)
    if WRITE_VELOCITY_PLANE_GIF:
        _prepare_output_directory(velocity_plane_frame_dir)
    if WRITE_PRESSURE_PLANE_GIF:
        _prepare_output_directory(pressure_plane_frame_dir)

    project_parameters_path = os.path.join(script_dir, PROJECT_PARAMETERS_FILENAME)
    with open(project_parameters_path, "r") as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())
    _normalize_solver_settings(parameters)

    analysis_stage_class = _load_analysis_stage_class(parameters)
    model = KratosMultiphysics.Model()
    simulation = analysis_stage_class(model, parameters)
    simulation.Initialize()

    velocity_norm = Normalize(vmin=0.0, vmax=COLORBAR_MAX)
    surrogate_faces = _collect_surrogate_faces(model) if WRITE_3D_CUT_GIF else []

    frame_index = 0
    while simulation.KeepAdvancingSolutionLoop():
        simulation.time = simulation._AdvanceTime()
        simulation.InitializeSolutionStep()
        simulation._GetSolver().Predict()
        simulation._GetSolver().SolveSolutionStep()
        simulation.FinalizeSolutionStep()
        simulation.OutputSolutionStep()

        if frame_index % FRAME_EVERY != 0:
            frame_index += 1
            continue

        if not model.HasModelPart(PLOT_MODEL_PART_NAME):
            print(f"ModelPart {PLOT_MODEL_PART_NAME} not found.")
            break

        model_part = model[PLOT_MODEL_PART_NAME]
        points, velocity, pressure = _sample_element_fields(model_part)
        if points.size == 0:
            print("No element data found for plotting.")
            break

        x_min, x_max = float(points[:, 0].min()), float(points[:, 0].max())
        y_min, y_max = float(points[:, 1].min()), float(points[:, 1].max())
        z_min, z_max = float(points[:, 2].min()), float(points[:, 2].max())
        bounds = (x_min, x_max, y_min, y_max, z_min, z_max)

        cut_mask = points[:, 0] < 0.0
        cut_points = points[cut_mask]
        if WRITE_3D_CUT_GIF and cut_points.size > 0:
            fig_cut = plt.figure(figsize=(9, 6))
            ax_cut = fig_cut.add_subplot(1, 1, 1, projection="3d")
            _set_3d_axes(ax_cut, bounds)
            ax_cut.set_title(rf"Cut contour $x < 0$ (t = {simulation.time:.5f})")

            if surrogate_faces:
                faces = [_map_points(np.array(face, dtype=float)).tolist() for face in surrogate_faces]
                _add_surrogate_faces(ax_cut, faces, alpha=0.18)

            mapped_cut_points = _map_points(cut_points)
            cut_values = np.abs(velocity[cut_mask, 2])
            cut_artist = ax_cut.scatter(
                mapped_cut_points[:, 0],
                mapped_cut_points[:, 1],
                mapped_cut_points[:, 2],
                c=cut_values,
                cmap="jet",
                norm=Normalize(vmin=0.0, vmax=COLORBAR_MAX),
                s=7,
                linewidths=0,
                alpha=0.9,
            )
            plt.colorbar(cut_artist, ax=ax_cut, shrink=0.8, pad=0.03, label=r"$|v_z|$")
            plt.tight_layout()
            _save_frame(fig_cut, os.path.join(cut_frame_dir, f"frame_{frame_index:06d}.png"))
            plt.close(fig_cut)

        velocity_magnitude = np.linalg.norm(velocity, axis=1)

        # ------------------------------------------------------------
        # Velocity magnitude on x ~= 0 plane
        # ------------------------------------------------------------
        plane_points, plane_values, plane_x = _extract_x_plane_layer(
            points,
            velocity_magnitude,
        )

        if WRITE_VELOCITY_PLANE_GIF and plane_points is not None and plane_points.size > 0:
            fig_plane, ax_plane = plt.subplots(figsize=PLANE_FIGSIZE)

            plane_artist = _plot_x_plane(
                ax_plane,
                plane_points,
                plane_values,
                velocity_norm,
            )

            ax_plane.set_title(
                rf"Velocity magnitude on $x \approx {plane_x:.3f}$, $t = {simulation.time:.5f}$",
                fontsize=PLANE_TITLE_SIZE,
            )

            _add_2d_colorbar(
                fig_plane,
                ax_plane,
                plane_artist,
                r"$|\mathbf{u}|$",
            )

            fig_plane.tight_layout()
            _save_frame(
                fig_plane,
                os.path.join(velocity_plane_frame_dir, f"frame_{frame_index:06d}.png"),
            )

            plt.close(fig_plane)

        # ------------------------------------------------------------
        # Pressure on x ~= 0 plane
        # ------------------------------------------------------------
        pressure_plane_points, pressure_plane_values, pressure_plane_x = _extract_x_plane_layer(
            points,
            pressure,
        )

        if WRITE_PRESSURE_PLANE_GIF and pressure_plane_points is not None and pressure_plane_points.size > 0:
            pressure_min = float(np.min(pressure_plane_values))
            pressure_max = float(np.max(pressure_plane_values))

            if abs(pressure_max - pressure_min) < 1.0e-14:
                pressure_min -= 0.5
                pressure_max += 0.5

            pressure_norm = Normalize(
                vmin=pressure_min,
                vmax=pressure_max,
            )

            fig_pressure, ax_pressure = plt.subplots(figsize=PLANE_FIGSIZE)

            pressure_artist = _plot_x_plane(
                ax_pressure,
                pressure_plane_points,
                pressure_plane_values,
                pressure_norm,
            )

            ax_pressure.set_title(
                rf"Pressure on $x \approx {pressure_plane_x:.3f}$, $t = {simulation.time:.5f}$",
                fontsize=PLANE_TITLE_SIZE,
            )

            _add_2d_colorbar(
                fig_pressure,
                ax_pressure,
                pressure_artist,
                r"$p$",
            )

            fig_pressure.tight_layout()
            _save_frame(
                fig_pressure,
                os.path.join(pressure_plane_frame_dir, f"frame_{frame_index:06d}.png"),
            )

            plt.close(fig_pressure)
        
        frame_index += 1

    simulation.Finalize()
    if WRITE_3D_CUT_GIF:
        _write_gif(cut_frame_dir, cut_gif_path)
    if WRITE_VELOCITY_PLANE_GIF:
        _write_gif(velocity_plane_frame_dir, velocity_plane_gif_path)
    if WRITE_PRESSURE_PLANE_GIF:
        _write_gif(pressure_plane_frame_dir, pressure_plane_gif_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
