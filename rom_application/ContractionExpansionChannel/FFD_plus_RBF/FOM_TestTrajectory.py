import KratosMultiphysics
from KratosMultiphysics.FluidDynamicsApplication.fluid_dynamics_analysis import FluidDynamicsAnalysis

from FOM import FOM_Class

import KratosMultiphysics.RomApplication as romapp
import json

import numpy as np
from matplotlib import pyplot as plt

#for checking if paths exits
import os

#importing testing trajectory
from simulation_trajectories import testing_trajectory









class FOM_Class_test(FOM_Class):

    def __init__(self, model, project_parameters):
        super().__init__(model, project_parameters)
        self.deformation_multiplier = 11


    def UpdateDeformationMultiplier(self):
        self.deformation_multiplier = testing_trajectory( self.time, self.deformation_multiplier, self.delta_deformation, self.maximum, self.minimum)

    def InitializeSolutionStep(self):
        super(FluidDynamicsAnalysis, self).InitializeSolutionStep()

        #free all nodes
        for node in self.model.GetModelPart("FluidModelPart").Nodes:
            node.Free(KratosMultiphysics.MESH_DISPLACEMENT_X)
            node.Free(KratosMultiphysics.MESH_DISPLACEMENT_Y)

        self.UpdateDeformationMultiplier()
        self.MoveControlPoints()
        self.LockOuterWalls()








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




























def Train_ROM():

    if not os.path.exists(f'./Results/FOM_test.post.bin'):

        with open("ProblemFiles/ProjectParameters_modified.json", 'r') as parameter_file:
            parameters = KratosMultiphysics.Parameters(parameter_file.read())
        global_model = KratosMultiphysics.Model()
        simulation = FOM_Class_test(global_model, parameters)
        simulation.Run()
        SnapshotsMatrix = simulation.GetSnapshotsMatrix()
        velocity_y, narrowing, deformation_multiplier = simulation.GetBifuracationData()
        #reynolds = simulation.GetReynoldsData()
        #np.save('Results/reynolds.npy', reynolds)
        np.save('Results/deformation_multiplier_test.npy', deformation_multiplier)
        np.save('Results/narrowing_test.npy', narrowing)
        np.save('Results/Velocity_y_test.npy', velocity_y)
        np.save('Results/SnapshotMatrix_test.npy', SnapshotsMatrix )






















if __name__=="__main__":
    working_path =os.getcwd()

    prepare_files(working_path)


    Train_ROM()

