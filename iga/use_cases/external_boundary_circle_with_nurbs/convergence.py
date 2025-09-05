
import KratosMultiphysics
import KratosMultiphysics.IgaApplication
from KratosMultiphysics.StructuralMechanicsApplication.structural_mechanics_analysis import StructuralMechanicsAnalysis

import matplotlib.pyplot as plt
import sympy as sp
import numpy as np
import math
import os


if __name__ == "__main__":

    # Read original parameters once
    with open('ProjectParameters.json', 'r') as f:
        parameters = KratosMultiphysics.Parameters(f.read())

    L2error_vector = []
    computational_area_vec = []
    h = []

    insertion = [4, 8, 16, 32, 64]
    degree = 2

    tot = len(insertion)
    for i in range(0,tot) :
        insertions = insertion[i]
        print("insertions: ", insertions) 

        for i in range(parameters["modelers"].size()):
            if parameters["modelers"][i]["modeler_name"].GetString() == "NurbsGeometryModelerSbm":
                modeler_number = i
                break

        parameters["modelers"][modeler_number]["Parameters"]["number_of_knot_spans"] = KratosMultiphysics.Parameters(f"[{insertions}, {insertions}]")
        parameters["modelers"][modeler_number]["Parameters"]["polynomial_order"] = KratosMultiphysics.Parameters(f"[{degree}, {degree}]")

        model = KratosMultiphysics.Model()
        simulation = StructuralMechanicsAnalysis(model,parameters)
        simulation.Run()

        # Exact solution as function handle:
        x = sp.symbols('x')
        y = sp.symbols('y')
        u_exact = -sp.cos(x)*sp.sinh(y)
        u_exact_handle = sp.lambdify((x, y), u_exact)

        # Computation of the error:
        output = []
        x_coord = []
        y_coord = []
        weight = []

        mp = model["IgaModelPart.StructuralAnalysisDomain"]
        L2_err_temp = 0.0
        L2_norm_solution = 0.0

        computational_area = 0.0
        for elem in mp.Elements:
            geom = elem.GetGeometry()

            N = geom.ShapeFunctionsValues()
            weight = elem.GetValue(KratosMultiphysics.INTEGRATION_WEIGHT)
    
            x = 0.0
            y = 0.0
            i = 0
            curr_disp_x = 0
            curr_disp_y = 0

            for n in geom:
                curr_disp_x += N[0, i] * n.GetSolutionStepValue(KratosMultiphysics.DISPLACEMENT_X)
                curr_disp_y += N[0, i] * n.GetSolutionStepValue(KratosMultiphysics.DISPLACEMENT_Y)
                x += N[0, i] * n.X
                y += N[0, i] * n.Y
                i += 1

            x_coord.append(x)
            y_coord.append(y)

            L2_err_temp += (curr_disp_x - u_exact_handle(x,y))**2 * weight
            L2_norm_solution += (u_exact_handle(x,y))**2 * weight

            computational_area += weight

        L2_err_temp = np.sqrt(L2_err_temp/L2_norm_solution)

        L2error_vector.append(L2_err_temp)
        computational_area_vec.append(computational_area)

        lower_corner_coords = parameters["modelers"][1]["Parameters"]["lower_point_xyz"].GetVector()
        upper_corner_coords = parameters["modelers"][1]["Parameters"]["upper_point_xyz"].GetVector()
        
        h_canditate = max(upper_corner_coords[0] - lower_corner_coords[0], upper_corner_coords[1] - lower_corner_coords[1]) / insertions
        h.append(h_canditate)
        
        simulation.Clear()
    
    print("\n h = ", h )
    print('\n L2 error', L2error_vector)

    plt.xscale('log')
    plt.yscale('log')
    plt.grid(True, which="both", linestyle='--')

    stored = np.zeros(6)
    stored[0] = (-(1)*(np.log(h[0])) + (np.log(L2error_vector[0])))
    stored[1] = (-(2)*(np.log(h[0])) + (np.log(L2error_vector[0])))
    stored[2] = (-(3)*(np.log(h[0])) + (np.log(L2error_vector[0])))
    stored[3] = (-(4)*(np.log(h[0])) + (np.log(L2error_vector[0])))
    stored[4] = (-(5)*(np.log(h[0])) + (np.log(L2error_vector[0])))
    stored[5] = (-(6)*(np.log(h[0])) + (np.log(L2error_vector[0])))
    degrees = np.arange(1, 7)
    yDegrees = np.zeros((degrees.size, len(h)))
    for i in range(0, degrees.size):
        for jtest in range(0, len(h)):
            yDegrees[i][jtest] = np.exp(degrees[i] * np.log(h[jtest]) + stored[i])
        plt.plot(h, yDegrees[i], "--", label='vel %d' % tuple([degrees[i]]))

    plt.plot(h, L2error_vector, 's-', markersize=1.5, linewidth=2, label='L^2 error')
    plt.ylabel('L2 err',fontsize=14, color='blue')
    plt.xlabel('h',fontsize=14, color='blue')
    plt.legend(loc='lower right')
    plt.show()

