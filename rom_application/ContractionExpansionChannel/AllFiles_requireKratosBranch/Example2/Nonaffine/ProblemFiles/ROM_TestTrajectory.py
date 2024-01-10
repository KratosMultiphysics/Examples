import KratosMultiphysics
from Run_ROM import ROM_Class

import KratosMultiphysics.RomApplication as romapp
import json

import numpy as np


#importing PyGeM tools
from pygem import FFD, RBF

import os



#importing testing trajectory
from simulation_trajectories import second_testing_trajectory







class ROM_Class_test(ROM_Class):

    def __init__(self, model, project_parameters, correct_cluster = None, hard_impose_correct_cluster = False, bases=None, hrom=None):
        super().__init__(model, project_parameters, hrom)
        self.deformation_multiplier = 11


    def UpdateDeformationMultiplier(self):
        self.deformation_multiplier = second_testing_trajectory( self.time )


    def InitializeSolutionStep(self):
        super(ROM_Class, self).InitializeSolutionStep()

        #free all nodes
        for node in self.model.GetModelPart("FluidModelPart").Nodes:
            node.Free(KratosMultiphysics.MESH_DISPLACEMENT_X)
            node.Free(KratosMultiphysics.MESH_DISPLACEMENT_Y)

        self.UpdateDeformationMultiplier()
        self.MoveControlPoints()
        self.LockOuterWalls()









def prepare_files(working_path, svd_truncation_tolerance):
    """pre-pending the absolut path of the files in the Project Parameters"""
    with open(working_path+'/ProblemFiles/ProjectParameters.json','r') as f:
        updated_project_parameters = json.load(f)
        file_input_name = updated_project_parameters["solver_settings"]["fluid_solver_settings"]["model_import_settings"]["input_filename"]
        materials_filename = updated_project_parameters["solver_settings"]["fluid_solver_settings"]["material_import_settings"]["materials_filename"]
        gid_output_name = updated_project_parameters["output_processes"]["gid_output"][0]["Parameters"]["output_name"]

        updated_project_parameters["solver_settings"]["fluid_solver_settings"]["model_import_settings"]["input_filename"] = working_path + '/ProblemFiles/'+ file_input_name
        updated_project_parameters["solver_settings"]["fluid_solver_settings"]["material_import_settings"]["materials_filename"] = working_path +'/ProblemFiles/'+ materials_filename
        updated_project_parameters["output_processes"]["gid_output"][0]["Parameters"]["output_name"] = working_path +f'/Results/ROM_test_{svd_truncation_tolerance}'

    with open(working_path+'/ProblemFiles/ProjectParameters_modified.json','w') as f:
        json.dump(updated_project_parameters, f, indent = 4)












def ROM(svd_truncation_tolerance):


    if not os.path.exists(f'./Results/ROM_test_{svd_truncation_tolerance}.post.bin'):
        with open("ProblemFiles/ProjectParameters_modified.json", 'r') as parameter_file:
            parameters = KratosMultiphysics.Parameters(parameter_file.read())
        global_model = KratosMultiphysics.Model()
        correct_clusters = None




        #loading the bases
        bases = []
        bases = None
        simulation = ROM_Class_test(global_model, parameters)
        simulation.Run()


        np.save(f'Results/ROM_snapshots_test_{svd_truncation_tolerance}.npy',simulation.GetSnapshotsMatrix())

        vy_rom, w_rom, deformation_multiplier = simulation.GetBifuracationData()

        np.save(f'Results/y_velocity_ROM_test_{svd_truncation_tolerance}.npy', vy_rom)
        np.save(f'Results/narrowing_ROM_test_{svd_truncation_tolerance}.npy', w_rom)
        np.save(f'Results/deformation_multiplier_ROM_test_{svd_truncation_tolerance}.npy', deformation_multiplier)

















if __name__=="__main__":

    #library for passing arguments to the script from bash
    from sys import argv

    Launch_Simulation = bool(int(argv[1]))
    Number_Of_Clusters= 1
    svd_truncation_tolerance= float(argv[3])
    clustering= argv[4]
    overlapping = int(argv[5])
    working_path = argv[6]


    prepare_files(working_path, svd_truncation_tolerance)


    ROM(svd_truncation_tolerance)


