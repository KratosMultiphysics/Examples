import KratosMultiphysics
from Run_ROM import ROM_Class


import KratosMultiphysics.RomApplication as romapp
import json
import numpy as np




import os.path


class TrainHROMClass(ROM_Class):

    def __init__(self, model, project_parameters,svd_truncation_tolerance):
        super().__init__(model, project_parameters, hrom="EmpiricalCubature")
        self.svd_truncation_tolerance = svd_truncation_tolerance







def Train_HROM(svd_truncation_tolerance):

    projected_residuals = f'HROM/Sr_{svd_truncation_tolerance}.npy'


    if not os.path.exists(projected_residuals):
        with open("ProblemFiles/ProjectParameters_modified.json", 'r') as parameter_file:
            parameters = KratosMultiphysics.Parameters(parameter_file.read())
        global_model = KratosMultiphysics.Model()
        correct_clusters = None


        #loading the bases
        bases = []
        bases = None
        simulation = TrainHROMClass(global_model, parameters, svd_truncation_tolerance)
        simulation.Run()










def prepare_files(working_path):
    """pre-pending the absolut path of the files in the Project Parameters"""
    with open(working_path+'/ProblemFiles/ProjectParameters.json','r') as f:
        updated_project_parameters = json.load(f)
        file_input_name = updated_project_parameters["solver_settings"]["fluid_solver_settings"]["model_import_settings"]["input_filename"]
        materials_filename = updated_project_parameters["solver_settings"]["fluid_solver_settings"]["material_import_settings"]["materials_filename"]
        gid_output_name = updated_project_parameters["output_processes"]["gid_output"][0]["Parameters"]["output_name"]

        updated_project_parameters["solver_settings"]["fluid_solver_settings"]["model_import_settings"]["input_filename"] = working_path + '/ProblemFiles/'+ file_input_name
        updated_project_parameters["solver_settings"]["fluid_solver_settings"]["material_import_settings"]["materials_filename"] = working_path +'/ProblemFiles/'+ materials_filename
        updated_project_parameters["output_processes"]["gid_output"] = []
        updated_project_parameters["output_processes"]["vtk_output"] = []

    with open(working_path+'/ProblemFiles/ProjectParameters_modified.json','w') as f:
        json.dump(updated_project_parameters, f, indent = 4)





if __name__=="__main__":

    #library for passing arguments to the script from bash
    from sys import argv

    Launch_Simulation = bool(int(argv[1]))
    Number_Of_Clusters= int(argv[2])
    svd_truncation_tolerance= float(argv[3])
    clustering= argv[4]
    overlapping = int(argv[5])
    working_path = argv[6]


    prepare_files(working_path)

    Train_HROM(svd_truncation_tolerance)

