import KratosMultiphysics
from FOM import FOM_Class



import KratosMultiphysics.RomApplication as romapp
import json

import numpy as np

#for checking if paths exits
import os


#importing testing trajectory
from simulation_trajectories import TestingTrajectory




class FOM_Class_test(FOM_Class):

    def InitialMeshPosition(self):
        self.testing_trajectory = TestingTrajectory(self.project_parameters["solver_settings"]["fluid_solver_settings"]["time_stepping"]["time_step"].GetDouble())
        self.w = self.testing_trajectory.SetUpInitialNarrowing()
        self.MoveAllPartsAccordingToW()


    def UpdateNarrowing(self):
        self.w = self.testing_trajectory.UpdateW(self.w)


    def InitializeSolutionStep(self):
        super(FOM_Class, self).InitializeSolutionStep()

        if self.time>10.0: # start modifying narrowing from 10 seconds onwards   (How long does it take to close????)
            self.UpdateNarrowing()
            self.MoveAllPartsAccordingToW()

        print('The current Reynolds Number is: ', self.GetReynolds())






def prepare_files(working_path):
    """pre-pending the absolut path of the files in the Project Parameters"""
    with open(working_path+'/ProblemFiles/ProjectParameters.json','r') as f:
        updated_project_parameters = json.load(f)
        file_input_name = updated_project_parameters["solver_settings"]["fluid_solver_settings"]["model_import_settings"]["input_filename"]
        materials_filename = updated_project_parameters["solver_settings"]["fluid_solver_settings"]["material_import_settings"]["materials_filename"]
        gid_output_name = updated_project_parameters["output_processes"]["gid_output"][0]["Parameters"]["output_name"]

        updated_project_parameters["solver_settings"]["fluid_solver_settings"]["model_import_settings"]["input_filename"] = working_path + '/ProblemFiles/'+ file_input_name
        updated_project_parameters["solver_settings"]["fluid_solver_settings"]["material_import_settings"]["materials_filename"] = working_path +'/ProblemFiles/'+ materials_filename
        updated_project_parameters["output_processes"]["gid_output"][0]["Parameters"]["output_name"] = working_path +'/Results/FOM_test'
        updated_project_parameters["output_processes"]["vtk_output"] = []

    with open(working_path+'/ProblemFiles/ProjectParameters_modified.json','w') as f:
        json.dump(updated_project_parameters, f, indent = 4)









def convert_to_nd(SnapshotsMatrix, number_of_dimensions=2):
    for i in range(np.shape(SnapshotsMatrix)[1]):
        column_mean = np.mean( SnapshotsMatrix[:,i].reshape(-1,number_of_dimensions).reshape(-1,number_of_dimensions),0).reshape(-1,1)
        if i ==0:
            columns_means = column_mean
        else:
            columns_means = np.c_[columns_means,column_mean]

    return columns_means





















def FOM_test():

    if not os.path.exists(f'./Results/FOM_test.post.bin'):

        with open("ProblemFiles/ProjectParameters_modified.json", 'r') as parameter_file:
            parameters = KratosMultiphysics.Parameters(parameter_file.read())
        global_model = KratosMultiphysics.Model()
        simulation = FOM_Class_test(global_model, parameters)
        simulation.Run()
        SnapshotsMatrix = simulation.GetSnapshotsMatrix()
        velocity_y, narrowing = simulation.GetBifuracationData()
        reynolds = simulation.GetReynoldsData()
        np.save('Results/reynolds_test.npy', reynolds)
        np.save('Results/narrowing_test.npy', narrowing)
        np.save('Results/Velocity_y_test.npy', velocity_y)
        np.save('Results/SnapshotMatrix_test.npy', SnapshotsMatrix )

























if __name__=="__main__":
    working_path =os.getcwd()

    prepare_files(working_path)

    FOM_test()














