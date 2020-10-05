# Import Kratos core and apps
import KratosMultiphysics as KM

# Additional imports
from KratosMultiphysics.ShapeOptimizationApplication import optimizer_factory

# Read parameters
with open("optimization_parameters.json", 'r') as parameter_file:
    parameters = KM.Parameters(parameter_file.read())

# Defining the model_part
model = KM.Model()

# Create optimizer and perform optimization
optimizer = optimizer_factory.CreateOptimizer(
    parameters["optimization_settings"], model)
optimizer.Optimize()
