from __future__ import absolute_import, division #makes KratosMultiphysics backward compatible with python 2.6 and 2.7

# Importing the Kratos Library
import KratosMultiphysics

# Import applications
import KratosMultiphysics.MultilevelMonteCarloApplication as KratosMLMC
import KratosMultiphysics.CompressiblePotentialFlowApplication as KratosCompressFlow
import KratosMultiphysics.MappingApplication

# Importing the problem analysis stage class
from KratosMultiphysics.CompressiblePotentialFlowApplication.potential_flow_analysis import PotentialFlowAnalysis

# Avoid printing of Kratos informations
KratosMultiphysics.Logger.GetDefaultOutput().SetSeverity(KratosMultiphysics.Logger.Severity.WARNING)

"""
SimulationScenario is inherited from the PotentialFlowAnalysis class and solves the potential flow
-lapl(u) = \varepsilon*f    u \in \Omega
                            u \in \partial(\Omega)
where
\varepsilon \sim
and
f =
the QoI is
lift coeficient
"""
class SimulationScenario(PotentialFlowAnalysis):
    def __init__(self,input_model,input_parameters,sample):
        self.sample = sample
        self.mapping = False
        super(SimulationScenario,self).__init__(input_model,input_parameters)

    """
    function introducing the stochasticity in the right hand side
    input:  self: an instance of the class
    """
    def ModifyInitialProperties(self):
        '''Introduce here the stochasticity in the Mach number and the angle of attack'''
        Mach = self.sample[1]
        alpha =  self.sample[2]
        if Mach < 0.1:
            Mach = 0.1
        elif Mach > 0.4:
            Mach = 0.4
        if alpha > 0.1:
            alpha = 0.1
        self.project_parameters["processes"]["boundary_conditions_process_list"][0]["Parameters"]["mach_infinity"].SetDouble(Mach)
        self.project_parameters["processes"]["boundary_conditions_process_list"][0]["Parameters"]["angle_of_attack"].SetDouble(alpha)
        super(SimulationScenario,self).ModifyInitialProperties()


    """
    function evaluating the QoI of the problem: lift coefficient
    input:  self: an instance of the class
    """
    def EvaluateQuantityOfInterest(self):
        qoi_list = [self._GetSolver().main_model_part.ProcessInfo.GetValue(KratosCompressFlow.LIFT_COEFFICIENT)]
        print("[SCREENING] Lift Coefficient: ",qoi_list[0])
        pressure_coefficient = []
        if (self.mapping is not True):
            for node in self._GetSolver().main_model_part.GetSubModelPart("Body2D_Body").Nodes:
                pressure_coefficient.append(node.GetValue(KratosMultiphysics.PRESSURE_COEFFICIENT))
        elif (self.mapping is True):
            for node in self.mapping_reference_model.GetModelPart("model.Body2D_Body").Nodes:
                pressure_coefficient.append(node.GetValue(KratosMultiphysics.PRESSURE_COEFFICIENT))
        qoi_list.append(pressure_coefficient)
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
            "interface_submodel_part_origin": "Body2D_Body",
            "interface_submodel_part_destination": "Body2D_Body",
            "echo_level" : 0
            }""")
        mapper = KratosMultiphysics.MappingApplication.MapperFactory.CreateMapper(self._GetSolver().main_model_part,self.mapping_reference_model.GetModelPart("model"),mapping_parameters)
        mapper.Map(KratosMultiphysics.PRESSURE_COEFFICIENT, \
            KratosMultiphysics.PRESSURE_COEFFICIENT,        \
            KratosMultiphysics.MappingApplication.Mapper.FROM_NON_HISTORICAL |     \
            KratosMultiphysics.MappingApplication.Mapper.TO_NON_HISTORICAL)
        print("[SCREENING] End Mapping")
        # evaluate qoi
        print("[SCREENING] Start evaluating QoI")
        qoi_list = self.EvaluateQuantityOfInterest()
        print("[SCREENING] End evaluating QoI")
        return qoi_list
