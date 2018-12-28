from __future__ import print_function, absolute_import, division #makes KratosMultiphysics backward compatible with python 2.6 and 2.7

import KratosMultiphysics
from KratosMultiphysics import *
import KratosMultiphysics.StructuralMechanicsApplication
import math
from structural_mechanics_analysis import StructuralMechanicsAnalysis

class StructuralMechanicsAnalysisWithCentrifugalForces(StructuralMechanicsAnalysis):
    def __init__(self,model,project_parameters):
        super(StructuralMechanicsAnalysisWithCentrifugalForces,self).__init__(model,project_parameters)

    def ApplyCentrifugalForces(self, model_part ):

        for node in model_part.Nodes:

            radius_vector = Vector(3)
            radius_vector[0] = node.X
            radius_vector[1] = node.Y
            radius_vector[2] = 0
            radius = math.sqrt(radius_vector[0]*radius_vector[0] + radius_vector[1]*radius_vector[1] + radius_vector[2]*radius_vector[2])

            normalized_radius_vector = Vector(3)
            if(radius!=0):
                normalized_radius_vector[0] = radius_vector[0]/radius
                normalized_radius_vector[1] = radius_vector[1]/radius
                normalized_radius_vector[2] = radius_vector[2]/radius
            else:
                normalized_radius_vector[0] = 0.0
                normalized_radius_vector[1] = 0.0
                normalized_radius_vector[2] = 0.0 

            omega = 5.0

            centrigual_acc = Vector(3)
            centrigual_acc = omega*omega * radius * normalized_radius_vector

            node.SetSolutionStepValue(VOLUME_ACCELERATION,0,centrigual_acc)


    def RunSolutionLoop(self):
        """This function executes the solution loop of the AnalysisStage
        It can be overridden by derived classes
        """
        main_model_part = self.model["Structure"]

        while self.time < self.end_time:
            self.time = self._GetSolver().AdvanceInTime(self.time)
            Dt = self.project_parameters["solver_settings"]["time_stepping"]["time_step"].GetDouble()            
            self.time = self._GetSolver().AdvanceInTime(self.time)            
            self.InitializeSolutionStep()
            self.ApplyCentrifugalForces(main_model_part)
            self._GetSolver().Predict()
            self._GetSolver().SolveSolutionStep()
            self.FinalizeSolutionStep()
            self.OutputSolutionStep()
  


if __name__ == "__main__":

    with open("ProjectParameters.json",'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())

    model = KratosMultiphysics.Model()
    simulation = StructuralMechanicsAnalysisWithCentrifugalForces(model,parameters)
    simulation.Run()
    
