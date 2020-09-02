from __future__ import absolute_import, division #makes KratosMultiphysics backward compatible with python 2.6 and 2.7

# Importing the Kratos Library
import KratosMultiphysics

# Import applications
import KratosMultiphysics.MultilevelMonteCarloApplication as KratosMLMC
import KratosMultiphysics.FluidDynamicsApplication
from KratosMultiphysics.FluidDynamicsApplication.fluid_dynamics_analysis import FluidDynamicsAnalysis
import KratosMultiphysics.MappingApplication
import KratosMultiphysics.MeshingApplication as KratosMeshing

# Avoid printing of Kratos informations
KratosMultiphysics.Logger.GetDefaultOutput().SetSeverity(KratosMultiphysics.Logger.Severity.WARNING)

class SimulationScenario(FluidDynamicsAnalysis):
    def __init__(self,input_model,input_parameters,sample):
        self.sample = sample
        self.mapping = False
        self.interest_model_part = "MainModelPart.NoSlip2D_structure"
        super(SimulationScenario,self).__init__(input_model,input_parameters)

    """
    function introducing the stochasticity in the right hand side
    input:  self: an instance of the class
    """
    def ModifyInitialProperties(self):
        '''Introduce here the stochasticity in the inlet velocity'''
        self.project_parameters["processes"]["boundary_conditions_process_list"][0]["Parameters"]["modulus"][0].SetDouble(self.sample[1])
        self.project_parameters["processes"]["boundary_conditions_process_list"][0]["Parameters"]["modulus"][1].SetDouble(self.sample[2])
        super(SimulationScenario,self).ModifyInitialProperties()

    """
    function evaluating the QoI of the problem
    input:  self: an instance of the class
    """
    def EvaluateQuantityOfInterest(self):
        qoi_list = []
        # set reference coordinates
        self.reference_point = KratosMultiphysics.Vector(3)
        self.reference_point[0] = 21.0
        self.reference_point[1] = 0.0
        self.reference_point[2] = 0.0

        # compute drag force
        drag_force_vector = KratosMultiphysics.FluidDynamicsApplication.DragUtilities().CalculateBodyFittedDrag(self.model.GetModelPart(self.interest_model_part))
        qoi_list.append(drag_force_vector[0]) # add drag force

        if (self.mapping is not True):
            for node in self.model.GetModelPart(self.interest_model_part).Nodes:
                qoi_list.append(node.GetSolutionStepValue(KratosMultiphysics.PRESSURE)) # add pressure
        elif (self.mapping is True):
            for node in self.mapping_reference_model.GetModelPart(self.interest_model_part).Nodes:
                qoi_list.append(node.GetSolutionStepValue(KratosMultiphysics.PRESSURE)) # add pressure
        print("[SCREENING] Total number of QoI:",len(qoi_list))

        return qoi_list

    """
    function mapping the pressure field on reference model
    input:  self: an instance of the class
    """
    def MappingAndEvaluateQuantityOfInterest(self):
        print("[SCREENING] Start Mapping")
        # map from current model part of interest to reference model part
        mapping_parameters = KratosMultiphysics.Parameters("""{
            "mapper_type": "nearest_element",
            "interface_submodel_part_origin": "NoSlip2D_structure",
            "interface_submodel_part_destination": "NoSlip2D_structure",
            "echo_level" : 0
            }""")
        mapper = KratosMultiphysics.MappingApplication.MapperFactory.CreateMapper(self._GetSolver().main_model_part,self.mapping_reference_model.GetModelPart("MainModelPart"),mapping_parameters)
        mapper.Map(KratosMultiphysics.PRESSURE, \
            KratosMultiphysics.PRESSURE)
        print("[SCREENING] End Mapping")
        # evaluate qoi
        print("[SCREENING] Start evaluating QoI")
        qoi_list = self.EvaluateQuantityOfInterest()
        print("[SCREENING] End evaluating QoI")
        return qoi_list
