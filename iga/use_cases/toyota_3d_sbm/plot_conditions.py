import importlib
import os

import matplotlib.pyplot as plt
import numpy as np
import KratosMultiphysics
from matplotlib.patches import Patch
from matplotlib.ticker import MaxNLocator
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

try:
    import KratosMultiphysics.IgaApplication as IGA  # noqa: F401
    IGA_IMPORT_ERROR = None
except ImportError as exc:
    IGA = None
    IGA_IMPORT_ERROR = exc


PLOT_SWAP_YZ_FOR_VISUALIZATION = True
PLOT_PROJECTIONS = False


def _read_parameters():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    parameter_path = os.path.join(script_dir, "ProjectParameters_3D_fluid.json")
    with open(parameter_path, "r") as parameter_file:
        return KratosMultiphysics.Parameters(parameter_file.read())


def _map_points(points):
    if not PLOT_SWAP_YZ_FOR_VISUALIZATION or points.size == 0:
        return points
    return points[:, [0, 2, 1]]


def _map_bounds(bounds):
    if not PLOT_SWAP_YZ_FOR_VISUALIZATION:
        return bounds
    x_min, x_max, y_min, y_max, z_min, z_max = bounds
    return (x_min, x_max, z_min, z_max, y_min, y_max)


def _axis_labels():
    if not PLOT_SWAP_YZ_FOR_VISUALIZATION:
        return ("X", "Y", "Z")
    return ("X", "Z", "Y")


def _get_plot_bounds(parameters):
    for modeler in parameters["modelers"].values():
        if not modeler.Has("modeler_name"):
            continue
        if modeler["modeler_name"].GetString() != "NurbsGeometryModelerSbm":
            continue

        modeler_params = modeler["Parameters"]
        if modeler_params.Has("lower_point_xyz") and modeler_params.Has("upper_point_xyz"):
            lower = modeler_params["lower_point_xyz"]
            upper = modeler_params["upper_point_xyz"]
        elif modeler_params.Has("lower_point_uvw") and modeler_params.Has("upper_point_uvw"):
            lower = modeler_params["lower_point_uvw"]
            upper = modeler_params["upper_point_uvw"]
        else:
            continue

        return (
            lower[0].GetDouble(), upper[0].GetDouble(),
            lower[1].GetDouble(), upper[1].GetDouble(),
            lower[2].GetDouble(), upper[2].GetDouble(),
        )
    return None


def _collect_surrogate_faces(model_part):
    faces = []

    # The plottable surrogate faces in this setup are stored directly on IgaModelPart
    # as Quadrilateral3D4 conditions. The SBM_Support_* submodelparts contain
    # quadrature-point wrapper geometries, which are not the face polygons we want here.
    for cond in model_part.Conditions:
        geom = cond.GetGeometry()
        if geom.PointsNumber() < 3 or geom.PointsNumber() > 4:
            continue
        faces.append(np.array([[node.X, node.Y, node.Z] for node in geom], dtype=float))

    return faces


def _resolve_variable(variable_name):
    try:
        if KratosMultiphysics.KratosGlobals.HasVariable(variable_name):
            return KratosMultiphysics.KratosGlobals.GetVariable(variable_name)
    except Exception:
        return None
    return None


def _as_point_array(value):
    try:
        return np.array([float(value[0]), float(value[1]), float(value[2])], dtype=float)
    except Exception:
        try:
            return np.array([float(value.X), float(value.Y), float(value.Z)], dtype=float)
        except Exception:
            return None


def _read_projection_from_entity(entity, projection_node_variable, projection_coordinates_variable):
    if projection_node_variable is not None and entity.Has(projection_node_variable):
        try:
            projection = _as_point_array(entity.GetValue(projection_node_variable))
            if projection is not None:
                return projection, "PROJECTION_NODE"
        except Exception:
            pass

    if projection_coordinates_variable is not None and entity.Has(projection_coordinates_variable):
        try:
            projection = _as_point_array(entity.GetValue(projection_coordinates_variable))
            if projection is not None:
                return projection, "PROJECTION_NODE_COORDINATES"
        except Exception:
            pass

    return None, None


def _collect_inner_skin_model_parts(model):
    candidate_names = []
    preferred_names = (
        "skin_model_part.inner",
        "SkinModelPart.inner",
        "IgaModelPart.skin_model_part.inner",
    )

    for model_part_name in preferred_names:
        if model.HasModelPart(model_part_name):
            candidate_names.append(model_part_name)

    model_part_names = model.GetModelPartNames() if hasattr(model, "GetModelPartNames") else []
    for model_part_name in model_part_names:
        if "skin_model_part.inner" not in model_part_name.lower():
            continue
        if model_part_name in candidate_names:
            continue
        candidate_names.append(model_part_name)

    model_parts = []
    for model_part_name in candidate_names:
        try:
            model_parts.append(model[model_part_name])
        except Exception:
            continue
    return model_parts


def _collect_inner_skin_points(model):
    points = []
    seen = set()

    for skin_model_part in _collect_inner_skin_model_parts(model):
        for node in skin_model_part.Nodes:
            point = (float(node.X), float(node.Y), float(node.Z))
            key = tuple(round(value, 12) for value in point)
            if key in seen:
                continue
            seen.add(key)
            points.append(point)

    if not points:
        return np.empty((0, 3), dtype=float)

    return np.array(points, dtype=float)


def _read_projection_from_node_id(entity, projection_node_id_variable, skin_model_parts):
    if projection_node_id_variable is None or not entity.Has(projection_node_id_variable):
        return None

    try:
        projection_node_id = int(entity.GetValue(projection_node_id_variable))
    except Exception:
        return None

    if projection_node_id <= 0:
        return None

    for skin_model_part in skin_model_parts:
        if not skin_model_part.HasNode(projection_node_id):
            continue
        node = skin_model_part.GetNode(projection_node_id)
        return np.array([float(node.X), float(node.Y), float(node.Z)], dtype=float)

    return None


def _closest_skin_node_projection(source, skin_points):
    if len(skin_points) == 0:
        return None

    deltas = skin_points - source
    distances = np.einsum("ij,ij->i", deltas, deltas)
    return np.array(skin_points[int(np.argmin(distances))], dtype=float)


def _execute_modelers(parameters, model):
    if not model.HasModelPart("IgaModelPart"):
        model.CreateModelPart("IgaModelPart")

    for modeler_data in parameters["modelers"].values():
        if not modeler_data.Has("modeler_name"):
            continue

        modeler_name = modeler_data["modeler_name"].GetString()
        modeler_params = modeler_data["Parameters"]
        print(f"[DEBUG] Creating modeler '{modeler_name}'")

        if KratosMultiphysics.HasModeler(modeler_name):
            modeler = KratosMultiphysics.CreateModeler(modeler_name, model, modeler_params)
        else:
            if not modeler_data.Has("kratos_module"):
                raise RuntimeError(f"Python modeler '{modeler_name}' is missing 'kratos_module'.")

            kratos_module_name = modeler_data["kratos_module"].GetString()
            if not kratos_module_name.startswith("KratosMultiphysics"):
                kratos_module_name = "KratosMultiphysics." + kratos_module_name
            python_modeler_name = kratos_module_name + ".modelers." + modeler_name
            python_module = importlib.import_module(python_modeler_name)
            modeler = python_module.Factory(model, modeler_params)

        setup_geometry = getattr(modeler, "SetupGeometryModel", None)
        if callable(setup_geometry):
            print(f"[DEBUG]  - SetupGeometryModel for '{modeler_name}'")
            setup_geometry()

        setup_model_part = getattr(modeler, "SetupModelPart", None)
        if callable(setup_model_part):
            print(f"[DEBUG]  - SetupModelPart for '{modeler_name}'")
            setup_model_part()


def _style_axis(ax, title, bounds):
    x_min, x_max, y_min, y_max, z_min, z_max = bounds
    axis_labels = _axis_labels()
    ax.set_title(title, pad=10)
    ax.set_xlim(x_min, x_max)
    ax.set_ylim(y_min, y_max)
    ax.set_zlim(z_min, z_max)
    ax.set_box_aspect((x_max - x_min, y_max - y_min, z_max - z_min))
    ax.view_init(elev=20, azim=-60)
    ax.grid(False)
    for axis in (ax.xaxis, ax.yaxis, ax.zaxis):
        axis.pane.set_edgecolor((0, 0, 0, 0.08))
        axis.pane.set_facecolor((0.98, 0.98, 0.98, 1.0))
    ax.xaxis.set_major_locator(MaxNLocator(nbins=5))
    ax.set_xlabel(axis_labels[0])
    ax.set_ylabel(axis_labels[1])
    ax.set_zlabel(axis_labels[2])


def _collect_inner_projection_segments(model_part, model):
    if not PLOT_PROJECTIONS:
        return []

    projection_node_variable = _resolve_variable("PROJECTION_NODE")
    projection_coordinates_variable = _resolve_variable("PROJECTION_NODE_COORDINATES")
    projection_node_id_variable = _resolve_variable("PROJECTION_NODE_ID")
    skin_model_parts = _collect_inner_skin_model_parts(model)
    skin_points = _collect_inner_skin_points(model)

    if not model_part.HasSubModelPart("SBM_Support_inner"):
        return []

    segments = []
    seen = set()
    condition_projection_node_count = 0
    condition_projection_coordinates_count = 0
    gauss_projection_node_count = 0
    gauss_projection_coordinates_count = 0
    gauss_projection_node_id_count = 0
    gauss_closest_skin_node_count = 0
    gauss_projection_cache = {}

    def _try_add_segment(source, projection):
        key = tuple(round(value, 12) for value in (*source, *projection))
        if key in seen:
            return False
        seen.add(key)
        segments.append((source, projection))
        return True

    for condition in model_part.GetSubModelPart("SBM_Support_inner").Conditions:
        center = condition.GetGeometry().Center()
        source = np.array([float(center.X), float(center.Y), float(center.Z)], dtype=float)
        projection, source_label = _read_projection_from_entity(
            condition,
            projection_node_variable,
            projection_coordinates_variable,
        )
        if projection is not None and _try_add_segment(source, projection):
            if source_label == "PROJECTION_NODE":
                condition_projection_node_count += 1
            elif source_label == "PROJECTION_NODE_COORDINATES":
                condition_projection_coordinates_count += 1

        for gauss_point in condition.GetGeometry():
            gauss_source = np.array([float(gauss_point.X), float(gauss_point.Y), float(gauss_point.Z)], dtype=float)
            projection, source_label = _read_projection_from_entity(
                gauss_point,
                projection_node_variable,
                projection_coordinates_variable,
            )
            if projection is None:
                projection = _read_projection_from_node_id(
                    gauss_point,
                    projection_node_id_variable,
                    skin_model_parts,
                )
                source_label = "PROJECTION_NODE_ID" if projection is not None else None
            if projection is None:
                cache_key = gauss_point.Id
                if cache_key not in gauss_projection_cache:
                    gauss_projection_cache[cache_key] = _closest_skin_node_projection(gauss_source, skin_points)
                projection = gauss_projection_cache[cache_key]
                source_label = "CLOSEST_SKIN_NODE" if projection is not None else None

            if projection is None or not _try_add_segment(gauss_source, projection):
                continue

            if source_label == "PROJECTION_NODE":
                gauss_projection_node_count += 1
            elif source_label == "PROJECTION_NODE_COORDINATES":
                gauss_projection_coordinates_count += 1
            elif source_label == "PROJECTION_NODE_ID":
                gauss_projection_node_id_count += 1
            elif source_label == "CLOSEST_SKIN_NODE":
                gauss_closest_skin_node_count += 1

    print(
        "SBM_Support_inner projections: "
        f"{condition_projection_node_count} from condition PROJECTION_NODE, "
        f"{condition_projection_coordinates_count} from condition PROJECTION_NODE_COORDINATES, "
        f"{gauss_projection_node_count} from gauss-point PROJECTION_NODE, "
        f"{gauss_projection_coordinates_count} from gauss-point PROJECTION_NODE_COORDINATES, "
        f"{gauss_projection_node_id_count} from gauss-point PROJECTION_NODE_ID, "
        f"{gauss_closest_skin_node_count} from closest inner skin nodes, "
        f"{len(segments)} total"
    )
    return segments


def _plot_surrogate_faces(ax, faces, bounds):
    axis_labels = _axis_labels()
    face_groups = {
        0: {"color": (1.0, 0.7, 0.7), "label": f"Faces normal to {axis_labels[0]}"},
        1: {"color": (0.7, 1.0, 0.7), "label": f"Faces normal to {axis_labels[1]}"},
        2: {"color": (0.7, 0.7, 1.0), "label": f"Faces normal to {axis_labels[2]}"},
    }
    face_count = 0

    for face_pts in faces:
        plot_face_pts = _map_points(face_pts)
        normal = np.cross(plot_face_pts[1] - plot_face_pts[0], plot_face_pts[2] - plot_face_pts[0])
        normal_norm = np.linalg.norm(normal)
        if normal_norm <= 1e-12:
            continue

        normal /= normal_norm
        group_id = int(np.argmax(np.abs(normal)))
        poly = Poly3DCollection(
            [plot_face_pts],
            alpha=0.75,
            edgecolor="k",
            linewidth=0.3,
            facecolor=face_groups[group_id]["color"],
        )
        ax.add_collection3d(poly)
        face_count += 1

    _style_axis(ax, "Surrogate Boundary Faces", _map_bounds(bounds))
    ax.legend(
        handles=[
            Patch(facecolor=group["color"], edgecolor="k", label=group["label"])
            for group in face_groups.values()
        ],
        loc="upper right",
    )
    return face_count


def _plot_inner_projection_segments(ax, segments):
    if not PLOT_PROJECTIONS:
        return

    if not segments:
        print("Warning: no inner projection segments found")
        return

    for source, projection in segments:
        plot_segment = _map_points(np.array([source, projection], dtype=float))
        ax.plot(
            plot_segment[:, 0],
            plot_segment[:, 1],
            plot_segment[:, 2],
            color="#111111",
            linewidth=0.7,
            alpha=0.7,
        )
        ax.scatter(
            [plot_segment[0, 0]],
            [plot_segment[0, 1]],
            [plot_segment[0, 2]],
            s=6,
            color="#111111",
            alpha=0.8,
            depthshade=False,
        )


def main():
    if IGA_IMPORT_ERROR is not None:
        raise RuntimeError(
            "KratosMultiphysics.IgaApplication failed to import. "
            "The current build appears to expose PROJECTION_NODE incorrectly in Python, "
            "so the IGA modelers/conditions cannot be created from this interpreter."
        ) from IGA_IMPORT_ERROR

    parameters = _read_parameters()
    plot_bounds = _get_plot_bounds(parameters)

    global_model = KratosMultiphysics.Model()
    _execute_modelers(parameters, global_model)

    iga_model_part = global_model["IgaModelPart"]
    surrogate_faces = _collect_surrogate_faces(iga_model_part)
    projection_segments = _collect_inner_projection_segments(iga_model_part, global_model)
    if not surrogate_faces:
        raise RuntimeError("No surrogate face conditions were found on IgaModelPart.")

    if plot_bounds is None:
        all_points = []
        for face in surrogate_faces:
            for point in face:
                all_points.append(tuple(point))
        if not all_points:
            raise RuntimeError("No surrogate faces found to plot.")
        xs, ys, zs = zip(*all_points)
        plot_bounds = (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))

    fig = plt.figure(figsize=(10, 8))
    ax = fig.add_subplot(1, 1, 1, projection="3d")
    face_count = _plot_surrogate_faces(ax, surrogate_faces, plot_bounds)
    if face_count == 0:
        plt.close(fig)
        raise RuntimeError("No surrogate conditions with 3 or more nodes were found.")
    _plot_inner_projection_segments(ax, projection_segments)

    plt.tight_layout()
    script_dir = os.path.dirname(os.path.abspath(__file__))
    output_path = os.path.join(script_dir, "surrogate_faces_plot.png")
    plt.savefig(output_path, dpi=200)
    print(f"Saved surrogate face plot to {output_path}")
    plt.show()


if __name__ == "__main__":
    main()
