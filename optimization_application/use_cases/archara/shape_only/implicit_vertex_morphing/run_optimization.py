# Import Kratos core and apps
import KratosMultiphysics as KM

# Additional imports
from KratosMultiphysics.OptimizationApplication.optimization_analysis import OptimizationAnalysis

with open("optimization_parameters.json",'r') as parameter_file:
    parameters = KM.Parameters(parameter_file.read())

# Defining the model_part
model = KM.Model()
analysis = OptimizationAnalysis(model, parameters)
analysis.Run()
