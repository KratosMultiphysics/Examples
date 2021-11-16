import sys
import time

import KratosMultiphysics
from KratosMultiphysics.StructuralMechanicsApplication.structural_mechanics_analysis import StructuralMechanicsAnalysis

"""
For user-scripting it is intended that a new class is derived
from StructuralMechanicsAnalysis to do modifications
"""

class StructuralMechanicsAnalysisWithFlush(StructuralMechanicsAnalysis):

    def __init__(self, model, project_parameters, flush_frequency=10.0):
        super().__init__(model, project_parameters)
        self.flush_frequency = flush_frequency
        self.last_flush = time.time()
        sys.stdout.flush()

        ### Output options ###
        ######################

        # Printing displacements
        self.output_displacements_flag = True
        self.output_displacement_model_part_names = ["Structure.PointLoad3D_End"]

    def Initialize(self):
        super().Initialize()
        sys.stdout.flush()
        KratosMultiphysics.Logger.Flush()

    def FinalizeSolutionStep(self):
        super().FinalizeSolutionStep()

        if self.parallel_type == "OpenMP":
            now = time.time()
            if now - self.last_flush > self.flush_frequency:
                sys.stdout.flush()
                self.last_flush = now
    
    def Finalize(self):
        super().Finalize()
        
        # Printing nodal displacements
        if self.output_displacements_flag:
            print('')
            print('*********************')
            for sub_model_part_name in self.output_displacement_model_part_names:
                print("MODEL PART: {0}".format(sub_model_part_name))
                print('NODAL DISPLACEMENTS')
                for node in self.model[sub_model_part_name].Nodes:
                    displacement = node.GetSolutionStepValue(KratosMultiphysics.DISPLACEMENT)
                    DX = displacement[0]
                    DY = displacement[1]
                    DZ = displacement[2]
                    print ("Node {0}:    DX = {1:.4f}    DY = {2:.4f}    DZ = {3:.4f}".format(node.Id, DX, DY, DZ))
            print('*********************')
        else:
            pass


if __name__ == "__main__":

    with open("ProjectParameters.json", 'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())

    global_model = KratosMultiphysics.Model()
    simulation = StructuralMechanicsAnalysisWithFlush(global_model, parameters)
    simulation.Run()
