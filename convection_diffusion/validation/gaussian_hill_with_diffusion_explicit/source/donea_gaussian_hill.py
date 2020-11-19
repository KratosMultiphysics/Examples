from KratosMultiphysics import *
import KratosMultiphysics.ConvectionDiffusionApplication
from KratosMultiphysics.ConvectionDiffusionApplication.convection_diffusion_analysis import ConvectionDiffusionAnalysis

from math import *

class GaussianHillWithDiffusionExplicit(ConvectionDiffusionAnalysis):
    """
    This problem is taken from [Donea, J., & Huerta, A. (2003). Finite Element Methods for Flow Problems. Retrieved from https://books.google.es/books?id=S4URqrTtSXoC],
    section 5.6.1
    """
    def __init__(self,model,parameters):
        super().__init__(model,parameters)
        self.apply_initial_condition = True

    def ApplyBoundaryConditions(self):
        super().ApplyBoundaryConditions()
        if self.apply_initial_condition:
            model_part_name = self.project_parameters["problem_data"]["model_part_name"].GetString()
            # set initial field
            for node in self.model.GetModelPart(model_part_name).Nodes:
                x = node.X
                diffusivity = 1e-3
                x0 = 2/15
                l = 7*sqrt(2)/300
                phi_analytical = 5/7*exp(-((x-x0)/l)**2)
                node.SetSolutionStepValue(KratosMultiphysics.TEMPERATURE,1,phi_analytical)
            # set boundary conditions
            for node in self.model.GetModelPart(model_part_name).Nodes:
                x = node.X
                if x == 0.0 or x == 1.0:
                    node.SetSolutionStepValue(KratosMultiphysics.TEMPERATURE,0.0)
                    node.SetSolutionStepValue(KratosMultiphysics.TEMPERATURE,1,0.0)
                    node.Fix(KratosMultiphysics.TEMPERATURE)
            self.apply_initial_condition = False

if __name__ == "__main__":
    from sys import argv

    project_parameters_file_name = "problem_settings/project_parameters_donea_gaussian_hill.json"

    with open(project_parameters_file_name,'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())

    model = KratosMultiphysics.Model()
    simulation = GaussianHillWithDiffusionExplicit(model, parameters)
    simulation.Run()