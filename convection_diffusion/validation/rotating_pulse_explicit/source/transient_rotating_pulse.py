from KratosMultiphysics import *
import KratosMultiphysics.ConvectionDiffusionApplication
from KratosMultiphysics.ConvectionDiffusionApplication.convection_diffusion_analysis import ConvectionDiffusionAnalysis

from math import *

class RotatingPules(ConvectionDiffusionAnalysis):
    """
    This problem is taken from [Donea, J., & Huerta, A. (2003). Finite Element Methods for Flow Problems. Retrieved from https://books.google.es/books?id=S4URqrTtSXoC], section 5.6.2
    """
    def ApplyBoundaryConditions(self):
        super().ApplyBoundaryConditions()
        model_part_name = self.project_parameters["problem_data"]["model_part_name"].GetString()
        for node in self.model.GetModelPart(model_part_name).Nodes:
            x = node.X
            y = node.Y
            convective_velocity = [-y+0.5,x-0.5,0.0]
            node.SetSolutionStepValue(KratosMultiphysics.VELOCITY,convective_velocity)
            node.SetSolutionStepValue(KratosMultiphysics.VELOCITY,1,convective_velocity)
            if (sqrt(x**2+y**2)<=1):
                forcing = exp(-self.time**10) * cos(pi/2*sqrt(x**2+y**2))
                forcing_previous = exp(-(self.time-self.project_parameters["solver_settings"]["time_stepping"]["time_step"].GetDouble())**10) * cos(pi/2*sqrt(x**2+y**2))
            else:
                forcing = 0
            node.SetSolutionStepValue(KratosMultiphysics.HEAT_FLUX,forcing)
            node.SetSolutionStepValue(KratosMultiphysics.HEAT_FLUX,1,forcing_previous)

if __name__ == "__main__":
    from sys import argv

    project_parameters_file_name = "problem_settings/project_parameters_transient_rotating_pulse.json"

    with open(project_parameters_file_name,'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())

    model = KratosMultiphysics.Model()
    simulation = RotatingPules(model, parameters)
    simulation.Run()