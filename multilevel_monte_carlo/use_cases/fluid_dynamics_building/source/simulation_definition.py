# Importing the Kratos Library
import KratosMultiphysics
import KratosMultiphysics.FluidDynamicsApplication
from KratosMultiphysics.FluidDynamicsApplication.fluid_dynamics_analysis import FluidDynamicsAnalysis
import KratosMultiphysics.MappingApplication

# Avoid printing of Kratos informations
KratosMultiphysics.Logger.GetDefaultOutput().SetSeverity(KratosMultiphysics.Logger.Severity.WARNING)

class SimulationScenario(FluidDynamicsAnalysis):
    def __init__(self,input_model,input_parameters,sample):
        super().__init__(input_model,input_parameters)
        self.sample = sample
        self.mapping = False
        self.interest_model_part = "MainModelPart.NoSlip2D_structure"

    def ModifyInitialProperties(self):
        """
        function introducing the stochasticity in the right hand side
        input:  self: an instance of the class
        """
        super().ModifyInitialProperties()
        '''Introduce here the stochasticity in the inlet velocity'''
        self.project_parameters["processes"]["boundary_conditions_process_list"][0]["Parameters"]["modulus"][0].SetDouble(self.sample[1])
        self.project_parameters["processes"]["boundary_conditions_process_list"][0]["Parameters"]["modulus"][1].SetDouble(self.sample[2])

    def EvaluateQuantityOfInterest(self):
        """
        function evaluating the QoI of the problem
        input:  self: an instance of the class
        """
        qoi_list = []
        # compute drag force
        drag_force_vector = KratosMultiphysics.FluidDynamicsApplication.DragUtilities().CalculateBodyFittedDrag(self.model.GetModelPart(self.interest_model_part))
        qoi_list.append(drag_force_vector[0]) # add drag force
        # pressure
        pressure_list = []
        if (self.mapping is not True):
            for node in self.model.GetModelPart(self.interest_model_part).Nodes:
                pressure_list.append(node.GetSolutionStepValue(KratosMultiphysics.PRESSURE)) # add pressure
        elif (self.mapping is True):
            for node in self.mapping_reference_model.GetModelPart(self.interest_model_part).Nodes:
                pressure_list.append(node.GetSolutionStepValue(KratosMultiphysics.PRESSURE)) # add pressure
        qoi_list.append(pressure_list)
        print("[SCREENING] Total number of QoI:",len(qoi_list))

        return qoi_list

    def MappingAndEvaluateQuantityOfInterest(self):
        """
        function mapping the pressure field on reference model
        input:  self: an instance of the class
        """
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
