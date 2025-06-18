import KratosMultiphysics
import KratosMultiphysics.IgaApplication
from KratosMultiphysics.StructuralMechanicsApplication.structural_mechanics_analysis import StructuralMechanicsAnalysis
import numpy as np

import matplotlib.pyplot as plt
import matplotlib.patches as patches

from matplotlib.lines import Line2D
from matplotlib.patches import Patch

if __name__ == "__main__":

    with open("ProjectParameters.json",'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())

    model = KratosMultiphysics.Model()
    
    simulation = StructuralMechanicsAnalysis(model, parameters)
    simulation.Initialize()
    simulation.InitializeSolutionStep()

    index_param_space= 1
    
    n_knot_span_u = parameters["modelers"][index_param_space]["Parameters"]["number_of_knot_spans"][0].GetInt()
    n_knot_span_v = parameters["modelers"][index_param_space]["Parameters"]["number_of_knot_spans"][1].GetInt()
    initial_u = parameters["modelers"][index_param_space]["Parameters"]["lower_point_uvw"][0].GetDouble()
    initial_v = parameters["modelers"][index_param_space]["Parameters"]["lower_point_uvw"][1].GetDouble()
    final_u = parameters["modelers"][index_param_space]["Parameters"]["upper_point_uvw"][0].GetDouble()
    final_v = parameters["modelers"][index_param_space]["Parameters"]["upper_point_uvw"][1].GetDouble()

    knots_u_1 = [initial_u]
    knots_v_1 = [initial_v]

    for j in range(1, n_knot_span_u):
        knots_u_1.append(initial_u + (final_u-initial_u) / (n_knot_span_u) * j)
    for j in range(1, n_knot_span_v):
        knots_v_1.append(initial_v + (final_v-initial_v) / (n_knot_span_v) * j)
    knots_u_1.append(final_u)
    knots_v_1.append(final_v)

    # Create figure and axes
    fig, ax = plt.subplots()
    ax.set_aspect('equal', adjustable='box')
    ax.grid(False)  
    label_used = set()

    # === PARAMETER SPACE GRID: BODY 1 ===
    for u in knots_u_1:
        ax.plot([u, u], [knots_v_1[0], knots_v_1[-1]], linestyle=':', color='gray', linewidth=1.5, label='Parameter space' if u == knots_u_1[0] else "")
    for v in knots_v_1:
        ax.plot([knots_u_1[0], knots_u_1[-1]], [v, v], linestyle=':', color='gray', linewidth=1.5)
    
    label_used.add("Parameter space")
    
    for side in ["outer", "inner"]:
        surrogate_part_name = f"IgaModelPart.surrogate_{side}"
        if model.HasModelPart(surrogate_part_name):
            mp = model.GetModelPart(surrogate_part_name)
            if len(mp.Conditions) > 0:
                for cond in mp.Conditions:
                    x_surr, y_surr = [], []
                    geom = cond.GetGeometry()
                    x_surr.append(geom[0].X)
                    y_surr.append(geom[0].Y)
                    x_surr.append(geom[1].X)
                    y_surr.append(geom[1].Y)
                    ax.plot(x_surr, y_surr, color='darkred', linewidth=5, label="Surrogate boundary")
                label_used.add("Surrogate boundary")

        skin_part_name = f"skin_model_part.{side}"
        if model.HasModelPart(skin_part_name):
            mp = model.GetModelPart(skin_part_name)
            if len(mp.Conditions) > 0:
                x_skin, y_skin = [], []
                for i, cond in enumerate(mp.Conditions):
                    geom = cond.GetGeometry()
                    if i == 0:
                        x_skin.append(geom[0].X)
                        y_skin.append(geom[0].Y)
                    x_skin.append(geom[1].X)
                    y_skin.append(geom[1].Y)
                x_skin.append(x_skin[0])
                y_skin.append(y_skin[0])
                ax.plot(x_skin, y_skin, color='deepskyblue', linewidth=2, label="True boundary")
                label_used.add("True boundary")

        gp_part_name = f"IgaModelPart.SBM_Support_{side}"
        if model.HasModelPart(gp_part_name):
            mp = model.GetModelPart(gp_part_name)
            if len(mp.Conditions) > 0:
                for cond in mp.Conditions:
                    geom = cond.GetGeometry()
                    N = geom.ShapeFunctionsValues()
                    gp = np.zeros(2)
                    for i, node in enumerate(geom):
                        gp[0] += N[0, i] * node.X
                        gp[1] += N[0, i] * node.Y
                    # plot gp, arrows, etc...

            

    
    # === ACTIVE GAUSS POINTS: FROM ELEMENT CENTERS ===
    mp = model["IgaModelPart.StructuralAnalysisDomain"]
    active_gauss_points = []
    for elem in mp.Elements:
        center = elem.GetGeometry().Center()
        x = center.X
        y = center.Y
        active_gauss_points.append((x, y))
        ax.plot(x, y, "bo", markersize=3, label="Elemental Gauss Points" if "Elemental Gauss Points" not in label_used else "")
        label_used.add("Elemental Gauss Points")

    # === FIND ACTIVE CELLS AND COLOR THEM LIGHT YELLOW ===
    active_cells = set()
    for (x_gp, y_gp) in active_gauss_points:
        for i in range(len(knots_u_1) - 1):
            for j in range(len(knots_v_1) - 1):
                u_min, u_max = knots_u_1[i], knots_u_1[i+1]
                v_min, v_max = knots_v_1[j], knots_v_1[j+1]
                if u_min <= x_gp <= u_max and v_min <= y_gp <= v_max:
                    active_cells.add((i, j))

    for (i, j) in active_cells:
        u_min, u_max = knots_u_1[i], knots_u_1[i+1]
        v_min, v_max = knots_v_1[j], knots_v_1[j+1]
        rect = patches.Rectangle((u_min, v_min), u_max - u_min, v_max - v_min,
                                linewidth=0, edgecolor=None, facecolor="#FFFACD", zorder=0,
                                label="Active elements" if "Active elements" not in label_used else "")
        ax.add_patch(rect)
        label_used.add("Active elements")

    # Custom handles
    custom_handles = []

    if "Parameter space" in label_used:
        custom_handles.append(Line2D([0], [0], color='gray', linestyle=':', label='Parameter space'))

    if "Surrogate boundary" in label_used:
        custom_handles.append(Line2D([0], [0], color='darkred', linewidth=2, label='Surrogate boundary'))

    if "True boundary" in label_used:
        custom_handles.append(Line2D([0], [0], color='deepskyblue', linewidth=2, label='True boundary'))

    if "Elemental Gauss Points" in label_used:
        custom_handles.append(Line2D([0], [0], marker='o', color='blue', linestyle='None', markersize=5, label='Elemental Gauss Points'))

    if "Boundary Gauss Points" in label_used:
        custom_handles.append(Line2D([0], [0], marker='o', color='red', linestyle='None', markersize=5, label='Boundary Gauss Points'))

    if "Active elements" in label_used:
        custom_handles.append(Patch(facecolor='#FFFACD', edgecolor='goldenrod', linestyle=':', linewidth=1.5, label='Active elements'))

    # Clean layout for publication
    ax.set_aspect('equal')
    ax.set_xlabel("")  # or add label if meaningful
    ax.set_ylabel("")
    ax.tick_params(left=False, bottom=False, labelleft=False, labelbottom=False)  # hide ticks
    plt.tight_layout()
    plt.subplots_adjust(right=0.8)  # extra space for legend

    ax.legend(handles=custom_handles, loc='center left', bbox_to_anchor=(1, 0.5))
    plt.show()


    
