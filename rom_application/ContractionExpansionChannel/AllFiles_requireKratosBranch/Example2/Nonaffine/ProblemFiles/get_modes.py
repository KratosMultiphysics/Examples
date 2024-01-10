import KratosMultiphysics
from KratosMultiphysics.FluidDynamicsApplication.fluid_dynamics_analysis import FluidDynamicsAnalysis
import numpy as np
import pdb
import json

class ImposeDisplacement(FluidDynamicsAnalysis):

    def __init__(self, model, project_parameters, displacements):
        super().__init__(model,project_parameters)
        self.displacements = displacements
        self.tttime = 0
        self.number_of_modes = np.shape(displacements)[1]

    def Run(self):
        self.Initialize()
        while self.tttime<self.number_of_modes:
            self.time = self._GetSolver().AdvanceInTime(self.time)
            print(f'generated output for time step {self.tttime}')
            #self.InitializeSolutionStep()
            self.FinalizeSolutionStep()
            self.OutputSolutionStep()
        self.Finalize()

    def FinalizeSolutionStep(self):
        super().FinalizeSolutionStep()
        index = 0
        for node in self._GetSolver().GetComputingModelPart().Nodes:
            node.SetSolutionStepValue(KratosMultiphysics.VELOCITY_X, self.displacements[index, self.tttime])
            node.SetSolutionStepValue(KratosMultiphysics.VELOCITY_Y, self.displacements[index+1, self.tttime])
            node.SetSolutionStepValue(KratosMultiphysics.PRESSURE, self.displacements[index+2, self.tttime])
            index+=3
        self.tttime+=1



def prepare_files():
    """pre-pending the absolut path of the files in the Project Parameters"""
    with open('ProjectParameters.json','r') as f:
        updated_project_parameters = json.load(f)
        updated_project_parameters["output_processes"]["gid_output"][0]["Parameters"]["output_name"] = '../Results/MODES'
        updated_project_parameters["output_processes"]["gid_output"][0]["Parameters"]["postprocess_parameters"]["result_file_configuration"]["output_interval"] = 0.1

    with open('ProjectParameters_modified.json','w') as f:
        json.dump(updated_project_parameters, f, indent = 4)



if __name__ == "__main__":

    prepare_files()

    # Imposing the modes displacements
    #with open("ProjectParameters.json.json",'r') as parameter_file:
    with open("ProjectParameters_modified.json",'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())



    truncation_basis = 1e-3
    displacements = np.load(f"../ROM/{truncation_basis}.npy")
    print('\n\n\n','the size of the matrix is: ', np.shape(displacements))
    #pdb.set_trace()
    model = KratosMultiphysics.Model()
    simulation = ImposeDisplacement(model,parameters,displacements)
    simulation.Run()

