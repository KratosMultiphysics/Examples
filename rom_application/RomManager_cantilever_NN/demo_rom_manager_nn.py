import KratosMultiphysics
import KratosMultiphysics.StructuralMechanicsApplication
from KratosMultiphysics.RomApplication.rom_manager import RomManager
import json

import numpy as np
import importlib

from scipy.stats import qmc


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


def CustomizeSimulation(cls, global_model, parameters):

    class CustomSimulation(cls):

        def __init__(self, model,project_parameters, custom_param = None):
            super().__init__(model,project_parameters)
            self.custom_param  = custom_param
            """
            Customize as needed
            """

        def Initialize(self):
            super().Initialize()
            """
            Customize as needed
            """

        def FinalizeSolutionStep(self):
            super().FinalizeSolutionStep()
            """
            Customize as needed
            """

        def CustomMethod(self):
            """
            Customize as needed
            """
            return self.custom_param

    return CustomSimulation(global_model, parameters)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def UpdateProjectParameters(parameters, mu=None):
    """
    Customize ProjectParameters here for imposing different conditions to the simulations as needed
    """
    parameters["processes"]["loads_process_list"][0]["Parameters"]["modulus"].SetString(str(mu[0]/300)+"*t")
    parameters["processes"]["loads_process_list"][1]["Parameters"]["modulus"].SetString(str(mu[1]/300)+"*t")
    parameters["problem_data"]["end_time"].SetDouble(300.0)

    return parameters
    
def NonUpdateProjectParameters(parameters, mu=None):
    return parameters

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def UpdateMaterialParametersFile(material_parametrs_file_name, mu):
    pass
    # with open(material_parametrs_file_name, mode="r+") as f:
    #     data = json.load(f)
    #     #change the angles of 1st and 2nd layer
    #     data["properties"][0]["Material"]["Variables"]["EULER_ANGLES"][0] = mu[0]
    #     data["properties"][1]["Material"]["Variables"]["EULER_ANGLES"][0] = mu[1]
    #     #write to file and save file
    #     f.seek(0)
    #     json.dump(data, f, indent=4)
    #     f.truncate()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #



def GetRomManagerParameters():
    """
    This function allows to easily modify all the parameters for the ROM simulation.
    The returned KratosParameter object is seamlessly used inside the RomManager.
    """
    general_rom_manager_parameters = KratosMultiphysics.Parameters("""{
            "rom_stages_to_train" : ["ROM"],             // ["ROM","HROM"]
            "rom_stages_to_test" : [],              // ["ROM","HROM"]
	    "type_of_decoder" : "ann_enhanced",           // "linear" "ann_enhanced",  TODO: add "quadratic"
            "paralellism" : null,                        // null, TODO: add "compss"
            "projection_strategy": "galerkin",            // "lspg", "galerkin", "petrov_galerkin"
            "assembling_strategy": "global",            // "global", "elemental"
            "save_gid_output": true,                    // false, true #if true, it must exits previously in the ProjectParameters.json
            "save_vtk_output": false,                    // false, true #if true, it must exits previously in the ProjectParameters.json
            "output_name": "id",                         // "id" , "mu"
            "ROM":{
                "svd_truncation_tolerance": 1e-6,
                "model_part_name": "Structure",                            // This changes depending on the simulation: Structure, FluidModelPart, ThermalPart #TODO: Idenfity it automatically
                "nodal_unknowns": ["DISPLACEMENT_X","DISPLACEMENT_Y"],     // Main unknowns. Snapshots are taken from these
                "rom_basis_output_format": "numpy",                         
                "rom_basis_output_name": "RomParameters",
                "rom_basis_output_folder": "rom_data",
                "snapshots_control_type": "step",                          // "step", "time"
                "snapshots_interval": 1,
                "galerkin_rom_bns_settings": {
                    "monotonicity_preserving": false
                },
                "lspg_rom_bns_settings": {
                    "train_petrov_galerkin": false,             
                    "basis_strategy": "residuals",                        // 'residuals', 'jacobian'
                    "include_phi": false,
                    "svd_truncation_tolerance": 0.001,
                    "solving_technique": "normal_equations",              // 'normal_equations', 'qr_decomposition'
                    "monotonicity_preserving": false
                },
                "ann_enhanced_settings":{
                    "saved_models_root_path": "rom_data/saved_nn_models/",
                    "training":{
            	        "modes":[3,10],
		        "layers_size":[200,200],
		        "batch_size":4,
		        "epochs":10,
		        "lr_strategy": {
		            "scheduler": "sgdr",         // "const", "steps", "sgdr"
		            "base_lr": 0.001,
		            "additional_params": [1e-4, 10, 400]     // const:[], steps/sgdr:["min_lr", "reduction_factor","update_period"]
		        },
		        "database":{
		            "training_set": "rom_data/SnapshotsMatrices/fom_snapshots.npy",
		            "validation_set": "rom_data/SnapshotsMatrices/fom_snapshots_val.npy",
		            "phi_matrix": "rom_data/RightBasisMatrix.npy",
		            "sigma_vector": "rom_data/SingularValuesVector.npy"
		        },
		        "use_automatic_name": true,
		        "custom_name": "test_neural_network"
                    },
                    "online":{
                        "model_name": "NN_model_3.10_[2](200,200)_lrsgdr.0.001_batchsize4"
                    }
                }
            },
            "HROM":{
                "element_selection_type": "empirical_cubature",
                "element_selection_svd_truncation_tolerance": 0,
                "create_hrom_visualization_model_part" : true,
                "echo_level" : 0
            }
        }""")

    return general_rom_manager_parameters


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


if __name__ == "__main__":

    def get_multiple_params(n_samples, seed): 
        sampler_test = qmc.Halton(d=2, seed=seed)
        mu=sampler_test.random(n=n_samples)
        mu=qmc.scale(mu, [-3000,-3000], [3000, 3000])
        print(np.array(mu))
        return mu
        
    with open("ProjectParameters.json", 'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())
        
    print(parameters)
        
    mu_train = get_multiple_params(20, 123) # random train parameters
    mu_test = get_multiple_params(2, 383) #random test parameters

    general_rom_manager_parameters = GetRomManagerParameters()
    project_parameters_name = "ProjectParameters.json"

    rom_manager = RomManager(project_parameters_name,general_rom_manager_parameters,CustomizeSimulation,UpdateProjectParameters,UpdateMaterialParametersFile)

    """if no list "mu" is passed, the case already contained in the ProjectParametes and CustomSimulation is launched (useful for example for a single time dependent simulation)"""
    
    #option 1
    rom_manager.Fit(mu_train=mu_train,mu_validation=mu_validation)

    #option 2
    # rom_manager.StoreFomSnapshotsAndBasis(mu_train=mu_train)
    # rom_manager.StoreFomValidationSnapshots(mu_validation=mu_validation)
    # rom_manager.TrainAnnEnhancedROM()

