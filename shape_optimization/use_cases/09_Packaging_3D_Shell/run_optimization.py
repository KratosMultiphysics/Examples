# Import Kratos core and apps
import KratosMultiphysics as KM

# Additional imports
from KratosMultiphysics.ShapeOptimizationApplication import optimizer_factory
from KratosMultiphysics.ShapeOptimizationApplication.analyzers.analyzer_base import AnalyzerBaseClass

# Read parameters
with open("optimization_parameters.json",'r') as parameter_file:
    parameters = KM.Parameters(parameter_file.read())

# Defining the model_part
model = KM.Model()

class CustomAnalyzer(AnalyzerBaseClass):
    def AnalyzeDesignAndReportToCommunicator(self, current_design, optimization_iteration, communicator):

        # Constraint 1
        if communicator.isRequestingValueOf("y_squared_sum"):
            value = 0.0
            for node in current_design.Nodes:
                value += node.Y**2
            communicator.reportValue("y_squared_sum", value)

        if communicator.isRequestingGradientOf("y_squared_sum"):
            gradient = {}
            for node in current_design.Nodes:
                gradient[node.Id] = [0.0,2*node.Y,0.0]
            communicator.reportGradient("y_squared_sum", gradient)

# Create optimizer and perform optimization
optimizer = optimizer_factory.CreateOptimizer(parameters["optimization_settings"], model, CustomAnalyzer())
optimizer.Optimize()