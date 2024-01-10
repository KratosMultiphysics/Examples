import KratosMultiphysics
from Run_ROM import ROM_Class


import KratosMultiphysics.RomApplication as romapp
import json


import numpy as np
import os


#importing testing trajectory
from simulation_trajectories import TestingTrajectory2



class ROM_Class_test(ROM_Class):


    def InitialMeshPosition(self):
        self.testing_trajectory = TestingTrajectory2()
        self.w = self.testing_trajectory.SetUpInitialNarrowing()
        self.MoveAllPartsAccordingToW()



    def UpdateNarrowing(self):
        self.w = self.testing_trajectory.UpdateW(self.time-10)




    def InitializeSolutionStep(self):
        super(ROM_Class, self).InitializeSolutionStep()

        if self.time>10.0: # start modifying narrowing from 10 seconds onwards   (How long does it take to close????)
            self.UpdateNarrowing()
            self.MoveAllPartsAccordingToW()


















def prepare_files(working_path,svd_truncation_tolerance):
    """pre-pending the absolut path of the files in the Project Parameters"""
    with open(working_path+'/ProblemFiles/ProjectParameters.json','r') as f:
        updated_project_parameters = json.load(f)
        file_input_name = updated_project_parameters["solver_settings"]["fluid_solver_settings"]["model_import_settings"]["input_filename"]
        materials_filename = updated_project_parameters["solver_settings"]["fluid_solver_settings"]["material_import_settings"]["materials_filename"]
        gid_output_name = updated_project_parameters["output_processes"]["gid_output"][0]["Parameters"]["output_name"]

        updated_project_parameters["solver_settings"]["fluid_solver_settings"]["model_import_settings"]["input_filename"] = working_path + '/ProblemFiles/'+ file_input_name
        updated_project_parameters["solver_settings"]["fluid_solver_settings"]["material_import_settings"]["materials_filename"] = working_path +'/ProblemFiles/'+ materials_filename
        updated_project_parameters["output_processes"]["gid_output"][0]["Parameters"]["output_name"] = working_path +f'/Results/ROM_{svd_truncation_tolerance}_test'
        updated_project_parameters["output_processes"]["vtk_output"] = []

    with open(working_path+'/ProblemFiles/ProjectParameters_modified.json','w') as f:
        json.dump(updated_project_parameters, f, indent = 4)












def ROM(hard_impose_currect_cluster = False, Number_Of_Clusters=1, svd_truncation_tolerance=1e-4):


    if not os.path.exists(f'./Results/ROM_{svd_truncation_tolerance}_test.post.bin'):

        with open("ProblemFiles/ProjectParameters_modified.json", 'r') as parameter_file:
            parameters = KratosMultiphysics.Parameters(parameter_file.read())
        global_model = KratosMultiphysics.Model()
        correct_clusters = None


        #loading the bases
        bases = []
        bases = None
        simulation = ROM_Class_test(global_model, parameters, correct_clusters, hard_impose_currect_cluster, bases)
        simulation.Run()
        np.save(f'Results/ROM_snapshots_{svd_truncation_tolerance}_test.npy',simulation.GetSnapshotsMatrix())
        vy_rom,w_rom = simulation.GetBifuracationData()

        np.save(f'Results/y_velocity_ROM_{svd_truncation_tolerance}_test.npy', vy_rom)
        np.save(f'Results/narrowing_ROM_{svd_truncation_tolerance}_test.npy', w_rom)




















if __name__=="__main__":

    #library for passing arguments to the script from bash
    from sys import argv

    Launch_Simulation = bool(int(argv[1]))
    Number_Of_Clusters= 1
    svd_truncation_tolerance= float(argv[3])
    clustering= argv[4]
    overlapping = int(argv[5])
    working_path = argv[6]


    prepare_files(working_path,svd_truncation_tolerance)


    ROM(hard_impose_currect_cluster = True, Number_Of_Clusters=Number_Of_Clusters, svd_truncation_tolerance=svd_truncation_tolerance)



