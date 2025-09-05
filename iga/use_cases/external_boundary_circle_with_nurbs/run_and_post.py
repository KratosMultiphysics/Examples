import KratosMultiphysics
import KratosMultiphysics.IgaApplication
from KratosMultiphysics.StructuralMechanicsApplication.structural_mechanics_analysis import StructuralMechanicsAnalysis

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.tri as mtri

class CustomAnalysisStage(StructuralMechanicsAnalysis):
    time_step = []
    nSTEP = 0
    
    def InitializeSolutionStep(self):
        super().InitializeSolutionStep()
        current_time = self._GetSolver().GetComputingModelPart().ProcessInfo[KratosMultiphysics.TIME]
        self.time_step.append(current_time)
        self.nSTEP += 1

# Define the analytical solution
def analytical_temperature(x, y, t):
    return -np.cos(x)*np.sinh(y)

# Main simulation function
if __name__ == "__main__":
    with open("ProjectParameters.json", 'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())

    model = KratosMultiphysics.Model()
    simulation = CustomAnalysisStage(model, parameters)
    simulation.Run()
    
    # Extract the computed solution at a specific time step
    mp = model["IgaModelPart"]

    x_coord = []
    y_coord = []
    computed_temperature = []
    weights = []

    # Loop over elements to gather computed solution
    for elem in mp.Elements:
        if (elem.Id == 1):
            continue
        geom = elem.GetGeometry()
        N = geom.ShapeFunctionsValues()
        center = geom.Center()
        weight = elem.GetValue(KratosMultiphysics.INTEGRATION_WEIGHT)
        weights.append(weight)
        # Extract Gauss point (center) coordinates
        x_coord.append(center.X)
        y_coord.append(center.Y)

        # Initialize solution values at the center
        curr_temperature = 0
        # Compute nodal contributions using shape functions
        for i, node in enumerate(geom):
            curr_temperature += N[0, i] * node.GetSolutionStepValue(KratosMultiphysics.DISPLACEMENT_X, 0)
        computed_temperature.append(curr_temperature)

    # Get the current time after simulation run
    current_time = simulation._GetSolver().GetComputingModelPart().ProcessInfo[KratosMultiphysics.TIME]
    print("Current time after simulation:", current_time)
    
    # Calculate errors and analytical solution
    temperature_error = []
    temperature_analytical_values = []

    for i in range(len(x_coord)):
        x = x_coord[i]
        y = y_coord[i]

        # Analytical solution at the point
        temperature_analytical = analytical_temperature(x, y, current_time)

        # Append analytical values for plotting
        temperature_analytical_values.append(temperature_analytical)

        # Error calculations
        temperature_error.append(abs(computed_temperature[i] - temperature_analytical))
    
    # Compute the L2 norm of the error for temperature
    temperature_l2_norm = 0
    for i in range(len(weights)):
        temperature_l2_norm += weights[i] * temperature_error[i]**2
    # Take the square root to finalize the L2 norm
    temperature_l2_norm = (temperature_l2_norm)**0.5
    
    # Compute the L2 norm of the analytical solution
    analytical_l2_norm = 0
    for i in range(len(weights)):
        analytical_l2_norm += weights[i] * temperature_analytical_values[i]**2
    analytical_l2_norm = (analytical_l2_norm)**0.5

    # Compute the normalized L2 error
    normalized_l2_error = temperature_l2_norm / analytical_l2_norm

    # Print the results
    print("L2 norm of temperature error:", temperature_l2_norm)
    # print("L2 norm of analytical solution:", analytical_l2_norm)
    print("Normalized L2 error:", normalized_l2_error)

    # Plot computed solution and analytical solution
    fig, ax = plt.subplots(1, 2, figsize=(12, 6))

    # triangulation = mtri.Triangulation(x_coord, y_coord)
    # Create a triangulation of the data points
    triangulation = mtri.Triangulation(x_coord, y_coord)
    areas = []
    for triangle in triangulation.triangles:
        x1, y1 = x_coord[triangle[0]], y_coord[triangle[0]]
        x2, y2 = x_coord[triangle[1]], y_coord[triangle[1]]
        x3, y3 = x_coord[triangle[2]], y_coord[triangle[2]]
        # Calculate the area of the triangle using the shoelace formula
        area = 0.5 * abs(x1 * (y2 - y3) + x2 * (y3 - y1) + x3 * (y1 - y2))
        areas.append(area)
    average_area = sum(areas) / len(areas)
    new_triangles = []
    for i in range(len(areas)):
        # if areas[i] <= average_area*2.09:
        # if areas[i] <= average_area*1.7:
        if areas[i] <= average_area*1.5:
            new_triangles.append(triangulation.triangles[i])
    new_triangulation = mtri.Triangulation(x_coord, y_coord, new_triangles)

    # Compute shared color limits (optional but keeps colormap consistent)
    vmin = min(np.min(computed_temperature), np.min(temperature_analytical_values))
    vmax = max(np.max(computed_temperature), np.max(temperature_analytical_values))

    # Computed solution
    tcf0 = ax[0].tricontourf(new_triangulation, computed_temperature, cmap='jet', vmin=vmin, vmax=vmax)
    ax[0].set_title("Computed Temperature")
    ax[0].set_xlabel("x")
    ax[0].set_ylabel("y")
    ax[0].set_aspect('equal')

    # Analytical solution
    tcf1 = ax[1].tricontourf(new_triangulation, temperature_analytical_values, cmap='jet', vmin=vmin, vmax=vmax)
    ax[1].set_title("Analytical Temperature")
    ax[1].set_xlabel("x")
    ax[1].set_aspect('equal')

    # Correct way to add colorbars
    plt.colorbar(tcf0, ax=ax[0], orientation='vertical')
    plt.colorbar(tcf1, ax=ax[1], orientation='vertical')

    plt.show()


    # Plot error distribution
    fig, ax = plt.subplots(1, 1, figsize=(6, 6))

    # Plot temperature error
    tcf = ax.tricontourf(new_triangulation, temperature_error, cmap='jet')
    ax.set_title("Error in Temperature")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_aspect('equal')
    # ax.plot(x_coord, y_coord, 'y*', markersize=4, label='Gauss Points')

    # Adding colorbar using the tricontourf return
    plt.colorbar(tcf, ax=ax, orientation='vertical')
    plt.show()

