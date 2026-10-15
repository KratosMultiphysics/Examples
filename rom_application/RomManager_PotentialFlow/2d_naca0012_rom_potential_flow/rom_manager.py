import os
import time
from pathlib import Path
import openpyxl
import numpy as np
from ClearAll import *
from parameters_manager import *  # type: ignore
from excel_utils import write_to_data_excel
import KratosMultiphysics
import KratosMultiphysics.kratos_utilities
import KratosMultiphysics.CompressiblePotentialFlowApplication as CPFApp
from KratosMultiphysics.RomApplication.rom_manager import RomManager
from KratosMultiphysics.RomApplication.rom_database import RomDatabase
from KratosMultiphysics.RomApplication.calculate_rom_basis_output_process import CalculateRomBasisOutputProcess



# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def CustomizeSimulation(cls, global_model, parameters, mu):

    class CustomSimulation(cls):

        def __init__(self, model,project_parameters):
            super().__init__(model,project_parameters)
            if len(mu) > 0:
                self.angle               = mu[0]
                self.mach                = mu[1]
                self.case_name           = f'{self.angle}, {self.mach}'
                self.simulation_name     = []
                self.exe_time = 0.0

            if parameters["output_processes"].Has("gid_output"):
                self.simulation_name = parameters["output_processes"]["gid_output"][0]["Parameters"]["output_name"].GetString().removeprefix('Results/')
            
        def GetFinalData(self):
            Cp_final_data = []
            modelpart = self.model["MainModelPart.Body"]
            for node in modelpart.Nodes:
                Cp_final_data.append([node.X, node.Y, node.Z, node.GetValue(KratosMultiphysics.PRESSURE_COEFFICIENT)])

            Full_Cp_final_data = []
            modelpart = self.model["MainModelPart"]
            for node in modelpart.Nodes:
                Full_Cp_final_data.append([node.X, node.Y, node.Z, node.GetValue(KratosMultiphysics.PRESSURE_COEFFICIENT)])
                
            return {'Cp_data': np.array(Cp_final_data),
                    'Full_Cp_data': np.array(Full_Cp_final_data),
                    'Residual_norm': self.model["MainModelPart"].ProcessInfo[KratosMultiphysics.RESIDUAL_NORM],
                    'NL_iterations': self.model["MainModelPart"].ProcessInfo[KratosMultiphysics.NL_ITERATION_NUMBER],
                    'Cl': self.model["MainModelPart"].ProcessInfo[CPFApp.LIFT_COEFFICIENT],
                    'Cd': self.model["MainModelPart"].ProcessInfo[KratosMultiphysics.DRAG_COEFFICIENT],
                    'q': np.array(self.model["MainModelPart"].GetValue(KratosMultiphysics.RomApplication.ROM_SOLUTION_INCREMENT)).reshape(-1,1),
                    'Time': self.exe_time}

        def SolveSolutionStep(self):
            start_time = time.perf_counter()
            solution = super().SolveSolutionStep()
            self.exe_time += time.perf_counter() - start_time
            return solution

        def Run(self):
            self.Initialize()
            self.RunSolutionLoop()
            self.Finalize()

            if parameters["output_processes"].Has("gid_output"):
                info_steps_list = []
                u_error = 0 
                modes   = 0

                BasisOutputProcess = None
                for process in self._GetListOfOutputProcesses():
                    if isinstance(process, CalculateRomBasisOutputProcess):
                        BasisOutputProcess = process

                if 'FOM' in self.simulation_name:
                    case = 'FOM'
                    if 'Fit' in self.simulation_name:
                        case_type = 'train_fom'
                    elif 'Test' in self.simulation_name:
                        case_type = 'test_fom'
                    elif 'Run' in self.simulation_name:
                        case_type = 'run_fom' 
                    
                elif 'ROM' in self.simulation_name:
                    if 'HROM' in self.simulation_name:
                        case = 'HROM'
                        if 'Fit' in self.simulation_name:
                            case_type = 'train_hrom'
                        elif 'Test' in self.simulation_name:
                            case_type = 'test_hrom' 
                        elif 'Run' in self.simulation_name:
                            case_type = 'run_hrom' 
                    else:
                        case = 'ROM'
                        if 'Fit' in self.simulation_name:
                            case_type = 'train_rom'
                        elif 'Test' in self.simulation_name:
                            case_type = 'test_rom' 
                        elif 'Run' in self.simulation_name:
                            case_type = 'run_rom' 

                    if BasisOutputProcess is not None:
                        u_rom = BasisOutputProcess._GetSnapshotsMatrix()
                    else:
                        # The RomManager collects the snapshots with the NumpyOutputProcess,
                        # which writes them to disk while the simulation runs
                        rom_folder = Path(general_rom_manager_parameters["ROM"]["rom_basis_output_folder"].GetString())
                        snapshots_folder = rom_folder / 'numpy_snapshots'
                        snapshot_files = sorted(snapshots_folder.glob('solution_*.npy'), key=lambda f: float(f.stem[len('solution_'):]))
                        u_rom = np.block([np.load(f) for f in snapshot_files]) if snapshot_files else None

                    data_base = RomDatabase(general_rom_manager_parameters, mu_names=['Alpha','Mach'])
                    u_fom = data_base.get_snapshots_matrix_from_database([mu], table_name=f'FOM')

                    if u_fom is not None and (u_rom is None or u_rom.shape != u_fom.shape) and os.path.exists('rom_data/RightBasisMatrix.npy'):
                        q_matrix = []
                        main_model_part = self.model["MainModelPart"]
                        q_matrix.append(np.array(main_model_part.GetValue(KratosMultiphysics.RomApplication.ROM_SOLUTION_INCREMENT)).reshape(-1,1))
                        q_matrix = np.block(q_matrix)
                        phi = np.load(f'rom_data/RightBasisMatrix.npy')
                        if (q_matrix.shape[0] == 1): q_matrix = q_matrix.T
                        u_rom = phi @ q_matrix

                    if u_fom is not None and u_rom is not None and u_rom.shape == u_fom.shape:
                        u_error = np.linalg.norm(u_fom-u_rom)/np.linalg.norm(u_fom)

                if os.path.exists('rom_data/RightBasisMatrix.npy'): 
                    modes = np.load('rom_data/RightBasisMatrix.npy').shape[1]

                info_steps_list.append([case_type,
                                        self.angle,
                                        self.mach,
                                        self.model["MainModelPart"].ProcessInfo[KratosMultiphysics.RESIDUAL_NORM],
                                        self.model["MainModelPart"].ProcessInfo[KratosMultiphysics.NL_ITERATION_NUMBER],
                                        u_error,
                                        modes,
                                        self.exe_time,
                                        self.model["MainModelPart"].NumberOfNodes(),
                                        self.model["MainModelPart"].ProcessInfo[CPFApp.LIFT_COEFFICIENT],
                                        self.model["MainModelPart"].ProcessInfo[KratosMultiphysics.DRAG_COEFFICIENT]])
                
                headers = ('Case name', 'Angle [º]', 'Mach', 'Residual norm', 
                            'NL iter','u relative error', 'Modes', 'Time [sec]', 'Nodes', 'Cl', 'Cd')
                write_to_data_excel(case, headers, info_steps_list, data_file='data.xlsx')

    return CustomSimulation(global_model, parameters)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def UpdateProjectParameters(parameters, mu=None):
    angle_of_attack = mu[0]
    mach_infinity   = mu[1]
    parameters["processes"]["boundary_conditions_process_list"][0]["Parameters"]["angle_of_attack"].SetDouble(np.double(angle_of_attack))
    parameters["processes"]["boundary_conditions_process_list"][0]["Parameters"]["mach_infinity"].SetDouble(np.double(mach_infinity))

    return parameters

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def UpdateMaterialParametersFile(material_parametrs_file_name, mu):
    pass

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def GetRomManagerParameters():
    with open("rom_manager_parameters.json", 'r') as parameter_file:
        general_rom_manager_parameters = KratosMultiphysics.Parameters(parameter_file.read())

    return general_rom_manager_parameters
    
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #



if __name__ == "__main__":

    ###########################################################
    # PARAMETERS SETTINGS
    clear_before              = True   
    update_parameters         = True
    number_of_mu_train        = [3] 
    number_of_mu_test         = 1
    mach_range                = [0.05, 0.30]
    angle_range               = [-1.00, 1.00]
    project_parameters_name   = "ProjectParameters.json"
    ###########################################################

    if clear_before:
        ClearAll()

    if update_parameters:
        KratosMultiphysics.kratos_utilities.DeleteDirectoryIfExisting('Mu_parameters')
        get_multiple_parameters(number_of_train_values = number_of_mu_train, 
                                number_of_test_values  = number_of_mu_test , 
                                angle_range            = angle_range       , 
                                mach_range             = mach_range        , 
                                method                 = 'Halton'          )

    mu_test  = load_mu_parameters('mu_test') 

    general_rom_manager_parameters = GetRomManagerParameters()
    rom_manager = RomManager(project_parameters_name,general_rom_manager_parameters,
                            CustomizeSimulation,UpdateProjectParameters,UpdateMaterialParametersFile,
                            mu_names=['Alpha','Mach'])
                        
    resume = []; modes = 0

    mu_train = load_mu_parameters(f'mu_train_0_1.0')
    mu_test  = load_mu_parameters(f'mu_test')

    rom_manager.Fit(mu_train)

    rom_manager.Test(mu_test, mu_train)

    # Run the HROM on the reduced HROM model part written during training.
    # This just save the GiD and VTK results
    rom_manager.RunHROM(mu_run=mu_test, mu_train=mu_train)

    if os.path.exists('rom_data/RightBasisMatrix.npy'): 
        modes = np.load('rom_data/RightBasisMatrix.npy').shape[1]

    resume.append(['ROMvsFOM' , modes, len(mu_train), rom_manager.ROMvsFOM['Fit'] , len(mu_test), rom_manager.ROMvsFOM['Test'] ])
    resume.append(['HROMvsFOM', modes, len(mu_train), rom_manager.FOMvsHROM['Fit'], len(mu_test), rom_manager.FOMvsHROM['Test']])
    resume.append(['ROMvsHROM', modes, len(mu_train), rom_manager.ROMvsHROM['Fit'], len(mu_test), rom_manager.ROMvsHROM['Test']])

    resume_headers = ('Case', 'Modes', 'Fit cases', 'Error', 'Test cases', 'Error')
    write_to_data_excel('resume', resume_headers, resume, data_file='data.xlsx')