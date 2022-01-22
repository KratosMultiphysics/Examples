# Import Kratos core and apps
import KratosMultiphysics as KM

# Additional imports
from KratosMultiphysics.ShapeOptimizationApplication import optimizer_factory
from KratosMultiphysics.ShapeOptimizationApplication.analyzers.analyzer_base import AnalyzerBaseClass

# Read parameters
with open("optimization_parameters.json",'r') as parameter_file:
    parameters = KM.Parameters(parameter_file.read())

# Definition of external analyzer
class CustomAnalyzer(AnalyzerBaseClass):
    def AnalyzeDesignAndReportToCommunicator(self, current_design, optimization_iteration, communicator):

        # Constraint 1
        constraint_node_id = 733
        if communicator.isRequestingValueOf("y_position_733"):
            value = current_design.Nodes[constraint_node_id].Y
            communicator.reportValue("y_position_733", value)

        if communicator.isRequestingGradientOf("y_position_733"):
            gradient = {}
            for node in current_design.Nodes:
                if node.Id == constraint_node_id:
                    gradient[node.Id] = [0.0,1.0,0.0]
                else:
                    gradient[node.Id] = [0.0,0.0,0.0]
            communicator.reportGradient("y_position_733", gradient)

        # Constraint 2
        constraint_node_id = 1048
        if communicator.isRequestingValueOf("y_position_1048"):
            value = current_design.Nodes[constraint_node_id].Y
            communicator.reportValue("y_position_1048", value)

        if communicator.isRequestingGradientOf("y_position_1048"):
            gradient = {}
            for node in current_design.Nodes:
                if node.Id == constraint_node_id:
                    gradient[node.Id] = [0.0,1.0,0.0]
                else:
                    gradient[node.Id] = [0.0,0.0,0.0]
            communicator.reportGradient("y_position_1048", gradient)


model = KM.Model()

# Create optimizer and perform optimization
optimizer = optimizer_factory.CreateOptimizer(parameters["optimization_settings"], model, CustomAnalyzer())
optimizer.Optimize()