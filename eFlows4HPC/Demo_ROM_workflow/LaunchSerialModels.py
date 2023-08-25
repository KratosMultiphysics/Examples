# Importing the Kratos Library
import KratosMultiphysics
from KratosMultiphysics.CoSimulationApplication.co_simulation_analysis import CoSimulationAnalysis

# Import packages
import numpy as np
import json
import os

#library for passing arguments to the script from bash
from sys import argv

class SerialRun(CoSimulationAnalysis):

    def __init__(self,cosim_parameters,sample,path,case, print_control_output):
        super().__init__(cosim_parameters)
        self.sample=sample
        self.path=path
        self.case = case
        self.print_control_output  = print_control_output

    def Initialize(self):
        self.solid_temp_stator_node = []
        self.solid_temp_rotor_node = []
        self.fluid_temp_stator_node = []
        self.fluid_temp_rotor_node = []
        for solver in self._solver.solver_wrappers.keys():
            if solver == 'solid':
                this_analysis_stage = self._solver._GetSolver(solver)._analysis_stage
                this_analysis_stage.project_parameters["processes"]["list_other_processes"][0]["Parameters"]["value"].SetDouble(self.sample[0])
                computing_model_part = this_analysis_stage._GetSolver().GetComputingModelPart()
        super().Initialize()
        velocity_field = np.load(self.path + f"/velocity_field_{self.sample[1]}.npy")
        for solver in self._solver.solver_wrappers.keys():
            if solver == 'fluid':
                this_analysis_stage = self._solver._GetSolver(solver)._analysis_stage
                computing_model_part = this_analysis_stage._GetSolver().GetComputingModelPart()
                for node in computing_model_part.Nodes:
                    global_id = (node.Id-1)*3
                    node.SetSolutionStepValue(KratosMultiphysics.VELOCITY_X, velocity_field[global_id])
                    node.SetSolutionStepValue(KratosMultiphysics.VELOCITY_Y, velocity_field[global_id+1])
                    node.SetSolutionStepValue(KratosMultiphysics.VELOCITY_Z, velocity_field[global_id+2])

    def FinalizeSolutionStep(self):
        super().FinalizeSolutionStep()
        for solver in self._solver.solver_wrappers.keys():
            if solver == 'solid':
                this_analysis_stage = self._solver._GetSolver(solver)._analysis_stage
                computing_model_part = this_analysis_stage._GetSolver().GetComputingModelPart()
                stator_node = computing_model_part.GetNode(15216)
                self.solid_temp_stator_node.append(stator_node.GetSolutionStepValue(KratosMultiphysics.TEMPERATURE))
                rotor_node = computing_model_part.GetNode(10904)
                self.solid_temp_rotor_node.append(rotor_node.GetSolutionStepValue(KratosMultiphysics.TEMPERATURE))
            elif solver == 'fluid':
                this_analysis_stage = self._solver._GetSolver(solver)._analysis_stage
                computing_model_part = this_analysis_stage._GetSolver().GetComputingModelPart()
                stator_node = computing_model_part.GetNode(45947)
                self.fluid_temp_stator_node.append(stator_node.GetSolutionStepValue(KratosMultiphysics.TEMPERATURE))
                rotor_node = computing_model_part.GetNode(35210)
                self.fluid_temp_rotor_node.append(rotor_node.GetSolutionStepValue(KratosMultiphysics.TEMPERATURE))

    def Finalize(self):
        super().Finalize()
        if print_control_output:
            # Define the directory for the results
            results_dir = "control_point_results"
            
            # Create the directory if it does not exist
            if not os.path.exists(results_dir):
                os.makedirs(results_dir)

            if self.case == "FOM":
                np.save(os.path.join(results_dir, "solid_temp_rotor_node_fom.npy"), self.solid_temp_rotor_node)
                np.save(os.path.join(results_dir, "solid_temp_stator_node_fom.npy"), self.solid_temp_stator_node)
                np.save(os.path.join(results_dir, "fluid_temp_rotor_node_fom.npy"), self.fluid_temp_rotor_node)
                np.save(os.path.join(results_dir, "fluid_temp_stator_node_fom.npy"), self.fluid_temp_stator_node)
            elif self.case == "ROM":
                np.save(os.path.join(results_dir, "solid_temp_rotor_node_rom.npy"), self.solid_temp_rotor_node)
                np.save(os.path.join(results_dir, "solid_temp_stator_node_rom.npy"), self.solid_temp_stator_node)
                np.save(os.path.join(results_dir, "fluid_temp_rotor_node_rom.npy"), self.fluid_temp_rotor_node)
                np.save(os.path.join(results_dir, "fluid_temp_stator_node_rom.npy"), self.fluid_temp_stator_node)
            elif self.case == "HROM":
                np.save(os.path.join(results_dir, "solid_temp_rotor_node_hrom.npy"), self.solid_temp_rotor_node)
                np.save(os.path.join(results_dir, "solid_temp_stator_node_hrom.npy"), self.solid_temp_stator_node)
                np.save(os.path.join(results_dir, "fluid_temp_rotor_node_hrom.npy"), self.fluid_temp_rotor_node)
                np.save(os.path.join(results_dir, "fluid_temp_stator_node_hrom.npy"), self.fluid_temp_stator_node)
            elif self.case == "HHROM":
                np.save(os.path.join(results_dir, "solid_temp_rotor_node_hhrom.npy"), self.solid_temp_rotor_node)
                np.save(os.path.join(results_dir, "solid_temp_stator_node_hhrom.npy"), self.solid_temp_stator_node)
                np.save(os.path.join(results_dir, "fluid_temp_rotor_node_hhrom.npy"), self.fluid_temp_rotor_node)
                np.save(os.path.join(results_dir, "fluid_temp_stator_node_hhrom.npy"), self.fluid_temp_stator_node)

def get_rom_output_defaults():
    defaults={
            "python_module": "calculate_rom_basis_output_process",
            "kratos_module": "KratosMultiphysics.RomApplication",
            "process_name": "rom_output",
            "Parameters": {
                "help": "A process to set the snapshots matrix and calculate the ROM basis from it.",
                "model_part_name": "",
                "rom_manager" : True,
                "snapshots_control_type": "step",
                "snapshots_interval": 1.0,
                "nodal_unknowns": [],
                "rom_basis_output_format": "numpy",
                "rom_basis_output_name": "RomParameters",
                "rom_basis_output_folder" : "rom_data",
                "svd_truncation_tolerance": 1.0e-6
            }
    }
    return defaults

def prepare_files_physical_problem(physics_project_parameters_name, solver, simulation_to_run, workflow_rom_parameters):
    """pre-pending the absolut path of the files in the Project Parameters"""
    with open(physics_project_parameters_name+'.json','r') as f:
        updated_project_parameters = json.load(f)
        materials_filename = f"ConvectionDiffusionMaterials_{solver}.json"
        working_path = argv[1]
        updated_project_parameters["output_processes"]["rom_output"] = [get_rom_output_defaults()]
        updated_project_parameters["output_processes"]["rom_output"][0]["Parameters"]["model_part_name"] = workflow_rom_parameters[solver]["ROM"]["model_part_name"].GetString()
        updated_project_parameters["output_processes"]["rom_output"][0]["Parameters"]["nodal_unknowns"] = workflow_rom_parameters[solver]["ROM"]["nodal_unknowns"].GetStringArray()
        updated_project_parameters["output_processes"]["rom_output"][0]["Parameters"]["rom_basis_output_folder"] = working_path+ '/' + solver
        if simulation_to_run=="FOM":
            updated_project_parameters["solver_settings"]["model_import_settings"]["input_filename"] = solver
            updated_project_parameters["solver_settings"]["material_import_settings"]["materials_filename"] = materials_filename
            with open(f'{physics_project_parameters_name}_workflow.json','w') as f:
                json.dump(updated_project_parameters, f, indent = 4)
        else:
            if simulation_to_run=="ROM" or simulation_to_run=="HROM":
                updated_project_parameters["solver_settings"]["model_import_settings"]["input_filename"] = solver
            updated_project_parameters["solver_settings"]["material_import_settings"]["materials_filename"] = materials_filename
            if simulation_to_run=="HHROM":
                updated_project_parameters["solver_settings"]["model_import_settings"]["input_filename"] = solver+"HROM"
            with open(f'{physics_project_parameters_name}.json','w') as f:
                json.dump(updated_project_parameters, f, indent = 4)

def prepare_files_cosim(workflow_rom_parameters, simulation_to_run):
    """pre-pending the absolut path of the files in the Project Parameters"""

    if simulation_to_run == "FOM":
        with open('ProjectParameters_CoSimulation_workflow.json','r') as f:
            working_path = argv[1]
            updated_project_parameters = json.load(f)
            solver_keys = updated_project_parameters["solver_settings"]["solvers"].keys()
            for solver in solver_keys:
                file_input_name = f"{working_path}/ProjectParameters_{solver}_workflow."
                updated_project_parameters["solver_settings"]["solvers"][solver]["solver_wrapper_settings"]["input_file"] = file_input_name
                prepare_files_physical_problem(file_input_name, solver, simulation_to_run, workflow_rom_parameters)

        with open('ProjectParameters_CoSimulation_workflow.json','w') as f:
            json.dump(updated_project_parameters, f, indent = 4)

    else:
        with open('ProjectParameters_CoSimulation_workflow.json','r') as f:
            working_path = argv[1]
            updated_project_parameters = json.load(f)
            solver_keys = updated_project_parameters["solver_settings"]["solvers"].keys()
            for solver in solver_keys:
                file_input_name = f"{working_path}/ProjectParameters_{solver}_workflow"
                updated_project_parameters["solver_settings"]["solvers"][solver]["solver_wrapper_settings"]["input_file"] = file_input_name
                prepare_files_physical_problem(file_input_name, solver, simulation_to_run, workflow_rom_parameters)
                updated_project_parameters["solver_settings"]["solvers"][solver]["type"] = 'solver_wrappers.kratos.rom_wrapper'

        with open('ProjectParameters_CoSimulation_workflow_ROM.json','w') as f:
            json.dump(updated_project_parameters, f, indent = 4)

def ChangeRomFlags(simulation_to_run = 'HROM'):
    folders = ["solid", "fluid"]
    for folder in folders:
        parameters_file_name = f'{folder}/RomParameters.json'
        with open(parameters_file_name, 'r+') as parameter_file:
            f=json.load(parameter_file)
            f['assembling_strategy'] = 'global'
            if simulation_to_run=='ROM':
                f['projection_strategy']="galerkin"
                f['train_hrom']=False
                f['run_hrom']=False
            elif simulation_to_run=='HHROM' or simulation_to_run=='HROM':
                f['projection_strategy']="galerkin"
                f['train_hrom']=False
                f['run_hrom']=True
            else:
                raise Exception(f'Unknown flag "{simulation_to_run}" change for RomParameters.json')
            parameter_file.seek(0)
            json.dump(f,parameter_file,indent=4)
            parameter_file.truncate()


def GetWorkflowROMParameters():

    workflow_rom_parameters = KratosMultiphysics.Parameters("""{
            "fluid":{
                "ROM":{
                    "svd_truncation_tolerance": 1e-6,
                    "model_part_name": "ThermalModelPart",
                    "nodal_unknowns": ["TEMPERATURE"],
                    "number_of_partitions":  10
                },
                "HROM":{
                    "number_of_partitions":  4,
                    "empirical_cubature_type": "partitioned",
                    "element_selection_svd_truncation_tolerance": 1e-8,
                    "include_conditions_model_parts_list": ["ThermalModelPart.GENERIC_Interface_fluid"],
                    "include_nodal_neighbouring_elements_model_parts_list": ["ThermalModelPart.GENERIC_Interface_fluid"],
                    "include_elements_model_parts_list": []
                }
            },
            "solid":{
                "ROM":{
                    "svd_truncation_tolerance": 1e-6,
                    "model_part_name": "ThermalModelPart",
                    "nodal_unknowns": ["TEMPERATURE"],
                    "number_of_partitions":  10
                },
                "HROM":{
                    "number_of_partitions":  4,
                    "empirical_cubature_type": "partitioned",
                    "element_selection_svd_truncation_tolerance": 1e-8,
                    "include_conditions_model_parts_list": ["ThermalModelPart.GENERIC_Interface_solid"],
                    "include_nodal_neighbouring_elements_model_parts_list": ["ThermalModelPart.GENERIC_Interface_solid"],
                    "include_elements_model_parts_list": []
                }
            }
        }""")

    return workflow_rom_parameters

def add_vtk_output_to_project_parameters(case):
    #adding vtk output to fluid
    with open('ProjectParameters_fluid_workflow.json','r') as f:
        updated_project_parameters = json.load(f)
        updated_project_parameters["output_processes"]["vtk_output"] = [
        {
            "Parameters": {
                "condition_data_value_variables": [],
                "element_data_value_variables": [],
                "file_format": "binary",
                "folder_name": case+'_fluid',
                "gauss_point_variables_extrapolated_to_nodes": [],
                "model_part_name": "ThermalModelPart",
                "nodal_data_value_variables": [],
                "nodal_solution_step_data_variables": [
                    "TEMPERATURE",
                    "VELOCITY",
                    "HEAT_FLUX",
                    "FACE_HEAT_FLUX",
                    "REACTION_FLUX",
                    "AUX_FLUX"
                ],
                "output_control_type": "step",
                "output_interval": 1,
                "output_precision": 7,
                "output_sub_model_parts": False,
                "save_output_files_in_folder": True
            },
            "help": "This process writes postprocessing files for Paraview",
            "kratos_module": "KratosMultiphysics",
            "process_name": "VtkOutputProcess",
            "python_module": "vtk_output_process"
        }
        ]
    with open('ProjectParameters_fluid_workflow.json','w') as f:
        json.dump(updated_project_parameters, f, indent = 4)
    #adding vtk output to solid
    with open('ProjectParameters_solid_workflow.json','r') as f:
        updated_project_parameters = json.load(f)
        updated_project_parameters["output_processes"]["vtk_output"] = [
            {
            "Parameters": {
                "condition_data_value_variables": [],
                "element_data_value_variables": [],
                "file_format": "binary",
                "folder_name": case+"_solid",
                "gauss_point_variables_extrapolated_to_nodes": [],
                "model_part_name": "ThermalModelPart",
                "nodal_data_value_variables": [],
                "nodal_solution_step_data_variables": [
                    "TEMPERATURE",
                    "VELOCITY",
                    "HEAT_FLUX",
                    "FACE_HEAT_FLUX",
                    "REACTION_FLUX",
                    "AUX_FLUX"
                ],
                "output_control_type": "step",
                "output_interval": 1.0,
                "output_precision": 7,
                "output_sub_model_parts": False,
                "save_output_files_in_folder": True
            },
            "help": "This process writes postprocessing files for Paraview",
            "kratos_module": "KratosMultiphysics",
            "process_name": "VtkOutputProcess",
            "python_module": "vtk_output_process"
        }
    ]
    with open('ProjectParameters_solid_workflow.json','w') as f:
        json.dump(updated_project_parameters, f, indent = 4)

def SerialTest(single_case, list_of_simulations_to_launch_in_serial, print_control_output):
    #this function is hardcoded
    workflow_rom_parameters = GetWorkflowROMParameters()
    for case in list_of_simulations_to_launch_in_serial:
        if case=="FOM":
            prepare_files_cosim(workflow_rom_parameters, simulation_to_run=case)
            parameter_file_name =  "ProjectParameters_CoSimulation_workflow.json"
            add_vtk_output_to_project_parameters(case)
        else:
            prepare_files_cosim(workflow_rom_parameters, simulation_to_run=case)
            ChangeRomFlags(simulation_to_run=case)
            parameter_file_name =  "ProjectParameters_CoSimulation_workflow_ROM.json"
            add_vtk_output_to_project_parameters(case)


        with open(parameter_file_name, 'r') as parameter_file:
            cosim_parameters = KratosMultiphysics.Parameters(parameter_file.read())
        simulation = SerialRun(cosim_parameters, single_case, argv[1], case, print_control_output)
        simulation.Run()


if __name__ == '__main__':

    mu = [[100000, 400]] # 400 RPM, 10000 W/m^3

    # Get the analysis directory path from the command line argument
    analysis_directory_path = argv[1]

    print_control_output = False

    SerialTest(mu[int(argv[2])], ["ROM"], print_control_output) #This should launch a single scenario of the parameters and store the results in vtk format for comparison
