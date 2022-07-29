import KratosMultiphysics
from KratosMultiphysics.FluidDynamicsApplication.fluid_dynamics_analysis import FluidDynamicsAnalysis

import sys
import time
import numpy as np

class FluidDynamicsAnalysisWithOutput(FluidDynamicsAnalysis):

    def __init__(self,model,project_parameters,flush_frequency=10.0):
        super().__init__(model,project_parameters)
        self.flush_frequency = flush_frequency
        self.last_flush = time.time()
        self.main_model_part = self.model.GetModelPart("FluidModelPart")
        # Initialize the snapshots data list
        self.snapshots_data_list = []

    def FinalizeSolutionStep(self):
        super().FinalizeSolutionStep()
        self.PrintOutput()
    
    def PrintOutput(self):
        # Save the data in the snapshots data list
        aux_data_array = []
        for node in self.main_model_part.Nodes:
            aux_data_array.append(node.GetSolutionStepValue(KratosMultiphysics.VELOCITY_X))
            aux_data_array.append(node.GetSolutionStepValue(KratosMultiphysics.VELOCITY_Y))
            aux_data_array.append(node.GetSolutionStepValue(KratosMultiphysics.PRESSURE))
        self.snapshots_data_list.append(aux_data_array)
    
    def Finalize(self):
        super().Finalize()
        # Convert to numpy array (matrix)
        self.snapshots_data_array = np.array(self.snapshots_data_list).T
        np.save("SnapshotsMatrix.npy",self.snapshots_data_array)

if __name__ == "__main__":

    with open("ProjectParameters.json",'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())

    model = KratosMultiphysics.Model()
    simulation = FluidDynamicsAnalysisWithOutput(model,parameters)
    simulation.Run()
