
import KratosMultiphysics
import KratosMultiphysics.ShallowWaterApplication
from KratosMultiphysics.ShallowWaterApplication.shallow_water_analysis import ShallowWaterAnalysis


class ShallowWaterAnalysisCustom(ShallowWaterAnalysis):
    def __init__(self,model,project_parameters):
        super().__init__(model,project_parameters)


if __name__ == "__main__":

    with open("ProjectParameters.json",'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())

    model = KratosMultiphysics.Model()
    simulation = ShallowWaterAnalysisCustom(model,parameters)
    simulation.Run()
