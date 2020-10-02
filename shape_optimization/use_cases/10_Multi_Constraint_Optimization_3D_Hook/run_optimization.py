# Making KratosMultiphysics backward compatible with python 2.6 and 2.7
from __future__ import print_function, absolute_import, division

# Import Kratos core and apps
import KratosMultiphysics as KM

# Additional imports
import KratosMultiphysics.ShapeOptimizationApplication as KSO
from KratosMultiphysics.ShapeOptimizationApplication import optimizer_factory, analyzer_base
from KratosMultiphysics.StructuralMechanicsApplication import structural_response_function_factory as csm_response_factory
from KratosMultiphysics.ShapeOptimizationApplication.analyzer_base import AnalyzerBaseClass

# Read parameters
with open("optimization_parameters.json", 'r') as parameter_file:
    parameters = KM.Parameters(parameter_file.read())

# Defining the model_part
model = KM.Model()


class CustomAnalyzer(AnalyzerBaseClass):

    def __init__(self):
        response_settings = parameters["optimization_settings"]["constraints"][1]["response_settings"]
        self.response = csm_response_factory.CreateResponseFunction(
            "strain_energy_tip", response_settings, model)

        self.model_part = model.GetModelPart("external")

    def InitializeBeforeOptimizationLoop(self):
        self.response.Initialize()

    def AnalyzeDesignAndReportToCommunicator(self, current_design, optimization_iteration, communicator):

        optimization_model_part = self.model_part
        response = self.response
        identifier = "strain_energy_tip"

        for d_node in current_design.GetRootModelPart().Nodes:
            node = optimization_model_part.Nodes[d_node.Id]
            node.X = d_node.X
            node.Y = d_node.Y
            node.Z = d_node.Z
            node.X0 = d_node.X0
            node.Y0 = d_node.Y0
            node.Z0 = d_node.Z0

        response.InitializeSolutionStep()

        # response values
        if communicator.isRequestingValueOf(identifier):
            response.CalculateValue()
            communicator.reportValue(identifier, response.GetValue())

        # response gradients
        if communicator.isRequestingGradientOf(identifier):
            response.CalculateGradient()
            communicator.reportGradient(
                identifier, response.GetNodalGradient(KM.SHAPE_SENSITIVITY))

        response.FinalizeSolutionStep()

        KSO.MeshControllerUtilities(
            optimization_model_part).SetMeshToReferenceMesh()
        KSO.MeshControllerUtilities(
            optimization_model_part).SetDeformationVariablesToZero()


model = KM.Model()

# Create optimizer and perform optimization
optimizer = optimizer_factory.CreateOptimizer(
    parameters["optimization_settings"], model, CustomAnalyzer())
optimizer.Optimize()
