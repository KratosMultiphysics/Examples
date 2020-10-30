from KratosMultiphysics import *
import KratosMultiphysics.ConvectionDiffusionApplication
from KratosMultiphysics.ConvectionDiffusionApplication.convection_diffusion_analysis import ConvectionDiffusionAnalysis

from math import *

class GaussianHillExplicit(ConvectionDiffusionAnalysis):
    """
    This problem is taken from [Kuzmin, D. (2010). Unsteady Transport Problems. In A Guide to Numerical Methods for Transport Equations (pp. 180–184). Retrieved from http://www.mathematik.uni-dortmund.de/~kuzmin/Transport.pdf], section 4.4.6.3
    """
    def __init__(self,model,parameters):
        super().__init__(model,parameters)
        self.apply_initial_condition = True

    def ApplyBoundaryConditions(self):
        super().ApplyBoundaryConditions()
        if self.apply_initial_condition:
            model_part_name = self.project_parameters["problem_data"]["model_part_name"].GetString()
            for node in self.model.GetModelPart(model_part_name).Nodes:
                x = node.X
                y = node.Y
                diffusivity = 1e-3
                t = pi/2 + simulation.time - self.project_parameters["solver_settings"]["time_stepping"]["time_step"].GetDouble()

                (x0, y0) = (0.0, 0.5)
                x_bar = x0*cos(t) - y0*sin(t)
                y_bar = -x0*sin(t) + y0*cos(t)
                r2 = (x-x_bar)**2 + (y-y_bar)**2

                phi_analytical = 1.0 / (4*pi*diffusivity*t) * exp(-r2 / (4*diffusivity*t))
                node.SetSolutionStepValue(KratosMultiphysics.TEMPERATURE,1,phi_analytical)
            self.apply_initial_condition = False

if __name__ == "__main__":
    from sys import argv

    project_parameters_file_name = "problem_settings/project_parameters_gaussian_hill.json"

    with open(project_parameters_file_name,'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())

    model = KratosMultiphysics.Model()
    simulation = GaussianHillExplicit(model, parameters)
    simulation.Run()