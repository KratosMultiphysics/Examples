# Making KratosMultiphysics backward compatible with python 2.6 and 2.7
from __future__ import print_function, absolute_import, division

# Import Kratos core and apps
import KratosMultiphysics as KM

# Additional imports
from KratosMultiphysics.ShapeOptimizationApplication import optimizer_factory
from KratosMultiphysics.ShapeOptimizationApplication.analyzer_base import AnalyzerBaseClass

# Read parameters
with open("optimization_parameters.json",'r') as parameter_file:
    parameters = KM.Parameters(parameter_file.read())

# Defining the model_part
model = KM.Model()

class CustomAnalyzer(AnalyzerBaseClass):
    def AnalyzeDesignAndReportToCommunicator(self, current_design, optimization_iteration, communicator):
        if communicator.isRequestingValueOf("x_squared_sum"):
            value = 0.0
            for node in current_design.Nodes:
                value += node.X**2
            communicator.reportValue("x_squared_sum", value)

        if communicator.isRequestingGradientOf("x_squared_sum"):
            gradient = {}
            for node in current_design.Nodes:
                gradient[node.Id] = [2*node.X, 0.0, 0.0]
            communicator.reportGradient("x_squared_sum", gradient)

# Create optimizer and perform optimization
optimizer = optimizer_factory.CreateOptimizer(parameters["optimization_settings"], model, CustomAnalyzer())
optimizer.Optimize()