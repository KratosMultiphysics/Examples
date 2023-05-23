import KratosMultiphysics
from KratosMultiphysics.RomApplication.rom_manager import RomManager
import json




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
    parameters["processes"]["loads_process_list"][0]["Parameters"]["value"].SetString("("+ str(mu[0]) + ")")
    parameters["processes"]["loads_process_list"][1]["Parameters"]["value"].SetString("("+ str(mu[1]) + ")")
    parameters["processes"]["loads_process_list"][2]["Parameters"]["value"].SetString("("+ str(mu[2]) + ")")

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
            "paralellism" : null,                        // null, TODO: add "compss"
            "projection_strategy": "lspg",                  // "lspg", "galerkin", "petrov_galerkin"
            "save_gid_output": true,                    // false, true #if true, it must exits previously in the ProjectParameters.json
            "save_vtk_output": false,                    // false, true #if true, it must exits previously in the ProjectParameters.json
            "output_name": "id",                         // "id" , "mu"
            "ROM":{
                "svd_truncation_tolerance": 1e-6,
                "model_part_name": "Structure",                            // This changes depending on the simulation: Structure, FluidModelPart, ThermalPart #TODO: Idenfity it automatically
                "nodal_unknowns": ["DISPLACEMENT_X","DISPLACEMENT_Y"],     // Main unknowns. Snapshots are taken from these
                "rom_basis_output_format": "numpy",                         //TODO: add "numpy"
                "rom_basis_output_name": "RomParameters",
                "snapshots_control_type": "step",                          // "step", "time"
                "snapshots_interval": 1,
                "petrov_galerkin_training_parameters":{
                    "basis_strategy": "residuals",                         // 'residuals', 'jacobian'
                    "include_phi": false,
                    "svd_truncation_tolerance": 0,
                    "echo_level": 0
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


    def random_samples_from_interval(initial, final, number_of_samples):
        import numpy as np
        return initial + np.random.rand(number_of_samples)*(final-initial)

    def get_multiple_params():
        number_of_params_1 = 2
        number_of_params_2 = 2
        number_of_params_3 = 2
        param1 = random_samples_from_interval(-50,50,number_of_params_1)
        param2 = random_samples_from_interval(-3,3,number_of_params_2)
        param3 = random_samples_from_interval(-10,10,number_of_params_3)
        mu = []
        for i in range(number_of_params_1):
            for j in range(number_of_params_2):
                for k in range(number_of_params_3):
                    mu.append([param1[i],param2[j],param3[k]])
        return mu



    mu_train = get_multiple_params() # random train parameters
    mu_test = get_multiple_params() #random test parameters

    #mu_train =  [[param1, param2, ..., param_p]] #list of lists containing values of the parameters to use in POD
    general_rom_manager_parameters = GetRomManagerParameters()
    project_parameters_name = "ProjectParameters.json"

    rom_manager = RomManager(project_parameters_name,general_rom_manager_parameters,CustomizeSimulation,UpdateProjectParameters,UpdateMaterialParametersFile)

    """if no list "mu" is passed, the case already contained in the ProjectParametes and CustomSimulation is launched (useful for example for a single time dependent simulation)"""
    rom_manager.Fit(mu_train) #pass list of lists mu_train
    #rom_manager.Test(mu_test) #pass list of lists mu_test
    rom_manager.PrintErrors()


