import numpy as np

from scipy.stats import qmc

import KratosMultiphysics
import KratosMultiphysics.LinearSolversApplication
import KratosMultiphysics.StructuralMechanicsApplication
import KratosMultiphysics.RomApplication
from KratosMultiphysics.RomApplication.initialize_from_snapshot_in_database_process import InitializeFromSnapshotInDatabase
from KratosMultiphysics.RomApplication.rom_manager import RomManager

# import locale
# locale.setlocale(locale.LC_ALL, 'en_US.utf8')

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


def CustomizeSimulation(cls, global_model, parameters, mu=None):

    class CustomSimulation(cls):

        def __init__(self, model,project_parameters, custom_param = None):
            super().__init__(model,project_parameters)
            self.custom_param  = custom_param
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
    steps = 400
    parameters["processes"]["loads_process_list"][0]["Parameters"]["modulus"].SetString(str(mu[0]/steps)+"*t")
    parameters["processes"]["loads_process_list"][1]["Parameters"]["modulus"].SetString(str(mu[1]/steps)+"*t")
    parameters["problem_data"]["end_time"].SetDouble(steps)

    return parameters
    
def UpdateMaterialParametersFile(parameters, mu=None):
    return parameters


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def GetRomManagerParameters():
    """
    This function allows to easily modify all the parameters for the ROM simulation.
    The returned KratosParameter object is seamlessly used inside the RomManager.
    """
    general_rom_manager_parameters = KratosMultiphysics.Parameters("""{
            "rom_stages_to_train" : ["ROM"],             // ["ROM","HROM"]
            "rom_stages_to_test" : ["ROM"],              // ["ROM","HROM"]
            "paralellism" : null,                        // null, TODO: add "compss"
            "type_of_decoder" : "ann_enhanced",               // "linear" "ann_enhanced",  TODO: add "quadratic"
            "projection_strategy": "galerkin",            // "lspg", "galerkin", "petrov_galerkin"
            "assembling_strategy": "global",            // "global", "elemental"
            "save_gid_output": true,                    // false, true #if true, it must exits previously in the ProjectParameters.json
            "save_vtk_output": false,                    // false, true #if true, it must exits previously in the ProjectParameters.json
            "output_name": "id",                         // "id" , "mu"
            "ROM":{
                "svd_truncation_tolerance": 0,
                "model_part_name": "Structure",                            // This changes depending on the simulation: Structure, FluidModelPart, ThermalPart #TODO: Idenfity it automatically
                "nodal_unknowns": ["DISPLACEMENT_X","DISPLACEMENT_Y"],     // Main unknowns. Snapshots are taken from these
                "rom_basis_output_format": "numpy",                         
                "rom_basis_output_name": "RomParameters",
                "snapshots_control_type": "time",                          // "step", "time"
                "snapshots_interval": 400,
                "snapshots_control_is_periodic": false,
                "print_singular_values": true,
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
                "ann_enhanced_settings": {
                    "modes":[14,60],
                    "layers_size":[200,200],
                    "batch_size":16,
                    "epochs":6,
                    "NN_gradient_regularisation_weight": 0.0,
                    "lr_strategy":{
                        "scheduler": "sgdr",
                        "base_lr": 0.001,
                        "additional_params": [1e-6, 10, 400]
                    },
                    "training":{
                        "retrain_if_exists" : false  // If false only one model will be trained for each the mu_train and NN hyperparameters combination
                    },
                    "online":{
                        "model_number": 0   // out of the models existing for the same parameters, this is the model that will be lauched
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
    
    def get_multiple_params(num_of_samples, seed):  
        sampler_test = qmc.Halton(d=2, seed=seed)
        mu=sampler_test.random(n=num_of_samples)
        mu=qmc.scale(mu, [-3000,-3000], [3000, 3000])
        print(mu)
        return mu.tolist()
    
    mu_train = np.array(get_multiple_params(500, 824)).tolist()
    mu_validation = np.array(get_multiple_params(100, 235)).tolist()
    mu_test = np.array(get_multiple_params(10, 539)).tolist()
    # mu_test = np.array(get_multiple_params(100, 539)).tolist()

    general_rom_manager_parameters = GetRomManagerParameters()
    project_parameters_name = "datasets_rubber_hyperelastic_cantilever_big_range/ProjectParameters_FOM.json"

    rom_manager = RomManager(project_parameters_name,general_rom_manager_parameters,CustomizeSimulation,UpdateProjectParameters, UpdateMaterialParametersFile)

    # First, train the ANN-PROM model via snapshot-based loss
    rom_manager.Fit(mu_train=mu_train, mu_validation=mu_validation)

    # Then, train the ANN-PROM model via snapshot-based loss on top of one we just trained.
    in_database, sloss_model_name = rom_manager.data_base.check_if_in_database("Neural_Network", mu_train)

    assert in_database
    print(sloss_model_name)

    # Update the ROM Manager parameters to include the recently-trained ANN's directory
    pretrained_model_path = str(rom_manager.data_base.database_root_directory)+'/saved_nn_models/' + sloss_model_name
    rom_manager.general_rom_manager_parameters["ROM"]["ann_enhanced_settings"]["online"]["custom_model_path"].SetString(pretrained_model_path)
    rom_manager.general_rom_manager_parameters["ROM"]["ann_enhanced_settings"]["lr_strategy"]["base_lr"].SetDouble(0.0001)
    print(rom_manager.general_rom_manager_parameters)

    # Finetune the NN using the residual loss
    rom_manager.FinetuneANNOnResidual(mu_train, mu_validation)

    # Test accuracy trained on snapshot
    rom_manager.general_rom_manager_parameters["ROM"]["ann_enhanced_settings"]["lr_strategy"]["base_lr"].SetDouble(0.001)
    rom_manager.Test(mu_test=mu_test, mu_train=mu_train, filter_nan=True)
    rom_manager.PrintErrors()

    # Test accuracy finetuned on residual
    in_database, rloss_model_name = rom_manager.data_base.check_if_in_database("Neural_Network_Residual", mu_train)
    assert in_database
    print(rloss_model_name)
    finetuned_model_path = str(rom_manager.data_base.database_root_directory)+'/saved_nn_models_residual/' + rloss_model_name
    rom_manager.general_rom_manager_parameters["ROM"]["ann_enhanced_settings"]["online"]["custom_model_path"].SetString(finetuned_model_path)
    rom_manager.general_rom_manager_parameters["ROM"]["ann_enhanced_settings"]["lr_strategy"]["base_lr"].SetDouble(0.0001)
    rom_manager.Test(mu_test=mu_test, mu_train=mu_train, filter_nan=True)
    rom_manager.PrintErrors()


