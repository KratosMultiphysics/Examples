import KratosMultiphysics as KM
import KratosMultiphysics.IgaApplication
from KratosMultiphysics.CoSimulationApplication.co_simulation_analysis import CoSimulationAnalysis

# External imports
import importlib
import matplotlib.pyplot as plt
import numpy as np
from scipy.interpolate import griddata

import sys
import time

class CustomCoSimulationAnalysis(CoSimulationAnalysis):
    def __init__(self, parameters):
        """Call the base class constructor."""
        super().__init__(parameters)
        self.time_history = []
        self.disp_x_history_A = []
        self.disp_x_history_B = []

    def OutputSolutionStep(self):
        super().OutputSolutionStep()

        solver = self._GetSolver()

        if hasattr(solver, "model") and hasattr(solver.model, "solver_wrappers"):
            structure_solver = solver.model.solver_wrappers.get("structure")  # Direct access

            if structure_solver and hasattr(structure_solver, "model"):
                sub_model = structure_solver.model
                model_part_name = "IgaModelPart"

                if hasattr(sub_model, "HasModelPart") and sub_model.HasModelPart(model_part_name):
                    model_part = sub_model.GetModelPart(model_part_name)
        
        wet_interface_sub_model_part = model_part.GetSubModelPart("Load_4")
        
        current_time = wet_interface_sub_model_part.ProcessInfo[KratosMultiphysics.TIME]

        for condition in wet_interface_sub_model_part.Conditions:
            condition_geom = condition.GetGeometry()
            x = condition_geom.Center().X
            y = condition_geom.Center().Y

            if condition.Id == 88:
                N = condition_geom.ShapeFunctionsValues()

                solution_A = 0.0
                index = 0
                for node in condition.GetNodes():
                    nodal_solution = node.GetSolutionStepValue(KratosMultiphysics.DISPLACEMENT_X)

                    solution_A += nodal_solution * N[0,index]
                    index += 1
                
                self.time_history.append(current_time)
                self.disp_x_history_A.append(solution_A)

            if condition.Id == 140:
                N = condition_geom.ShapeFunctionsValues()

                solution_B = 0.0
                index = 0
                for node in condition.GetNodes():
                    nodal_solution = node.GetSolutionStepValue(KratosMultiphysics.DISPLACEMENT_X)

                    solution_B += nodal_solution * N[0,index]
                    index += 1
                
                self.disp_x_history_B.append(solution_B)

    def Finalize(self):
        super().Finalize()

        import matplotlib.pyplot as plt

        # Enable LaTeX-style rendering
        plt.rcParams["text.usetex"] = True
        plt.rcParams["font.family"] = "serif"

        # Plot
        plt.figure()
        plt.plot(self.time_history, self.disp_x_history_A, label=r"$u_x$ at Point A")
        plt.plot(self.time_history, self.disp_x_history_B, label=r"$u_x$ at Point B")

        # Labels with LaTeX formatting
        plt.xlabel(r"\textbf{Time} [s]")
        plt.ylabel(r"\textbf{Displacement} $u_x$ [m]")
        plt.title(r"\textbf{Displacement vs Time (Nearest Neighbor Mapper)}", fontsize=14)

        # Grid and legend
        plt.grid(True)
        plt.legend(loc="best")

        # Save and show
        plt.savefig("displacement_vs_time.pdf", dpi=300, bbox_inches="tight")
        plt.show()

if __name__ == "__main__":

    with open("ProjectParametersCoSim.json", 'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())

    simulation = CustomCoSimulationAnalysis(parameters)
    simulation.Run()
