import os
import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')
import pickle
import numpy as np
from scipy.stats import qmc
import KratosMultiphysics
import KratosMultiphysics.kratos_utilities
from KratosMultiphysics.RomApplication.rom_manager import RomManager

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def CustomizeSimulation(cls, global_model, parameters):

    class CustomSimulation(cls):

        def __init__(self, model,project_parameters, custom_param = None):
            super().__init__(model,project_parameters)
            self.custom_param  = custom_param

        def ModifyInitialProperties(self):
            if self._GetSimulationName() == "::[ROM Simulation]:: ":
                parameters["solver_settings"]["solving_strategy_settings"]["type"].SetString("newton_raphson")
                parameters["solver_settings"]["maximum_iterations"].SetInt(50)
        
        def Initialize(self):
            super().Initialize()

        def InitializeSolutionStep(self):
            super().InitializeSolutionStep()

        def FinalizeSolutionStep(self):
            super().FinalizeSolutionStep()

            if parameters["output_processes"].Has("gid_output"):
                nametype = parameters["output_processes"]["gid_output"][0]["Parameters"]["output_name"].GetString()
                simulation_name = nametype.split('/')[1]
            
                # guardar aqui datos directamente de la skin
                fout = open("Data/" + simulation_name + ".dat",'w')
                modelpart = self.model["MainModelPart.Body2D_Body"]
                for node in modelpart.Nodes:
                    x = node.X ; y = node.Y ; z = node.Z
                    cp = node.GetValue(KratosMultiphysics.PRESSURE_COEFFICIENT)
                    fout.write("%s %s %s %s\n" %(x,y,z,cp))
                fout.close()

                plot_Cps(simulation_name)            

        def CustomMethod(self):
            return self.custom_param

    return CustomSimulation(global_model, parameters)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def UpdateProjectParameters(parameters, mu=None):

    angle_of_attack        = mu[0]
    mach_infinity          = mu[1]

    parameters["processes"]["boundary_conditions_process_list"][0]["Parameters"]["angle_of_attack"].SetDouble(angle_of_attack)
    parameters["processes"]["boundary_conditions_process_list"][0]["Parameters"]["mach_infinity"].SetDouble(mach_infinity)

    return parameters

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def UpdateMaterialParametersFile(material_parametrs_file_name, mu):
    pass

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# get multiple parameters
#
def get_multiple_params_by_Halton_sequence(number_of_values,angle,mach,fix_corners_of_parametric_space):
    if fix_corners_of_parametric_space and number_of_values < 4:
        print("Setting number of values to 4.")
        number_of_values = 4
    sampler = qmc.Halton(d=2)
    # sampler = qmc.LatinHypercube(d=2)
    mu = []
    if number_of_values > 0:
        sample = sampler.random(number_of_values)
        values = qmc.scale(sample, [angle[0],mach[0]], [angle[1],mach[1]])
        if fix_corners_of_parametric_space and number_of_values >= 4:
            values[0,0] = angle[0]
            values[0,1] = mach[0]
            values[1,0] = angle[0]
            values[1,1] = mach[1]
            values[number_of_values-1,0] = angle[1]
            values[number_of_values-1,1] = mach[1]
            values[number_of_values-2,0] = angle[1]
            values[number_of_values-2,1] = mach[0]
        for i in range(number_of_values):
            #Angle of attack , Mach infinit
            mu.append([np.round(values[i,0],2), np.round(values[i,1],3)])
    return mu

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def plot_mu_values(mu_train,mu_test):
    mu_train_a = np.zeros(len(mu_train))
    mu_train_m = np.zeros(len(mu_train))
    mu_test_a  = np.zeros(len(mu_test))
    mu_test_m  = np.zeros(len(mu_test))
    for i in range(len(mu_train)):
        mu_train_a[i] = mu_train[i][0]
        mu_train_m[i] = mu_train[i][1]
    for i in range(len(mu_test)):
        mu_test_a[i] = mu_test[i][0]
        mu_test_m[i] = mu_test[i][1]
    plt.plot(mu_train_m, mu_train_a, 'bs', label="Train Values")
    plt.plot(mu_test_m, mu_test_a, 'ro', label="Test Values")
    plt.title('Mu Values')
    plt.ylabel('Alpha')
    plt.xlabel('Mach')
    plt.grid(True)
    plt.legend(bbox_to_anchor=(.85, 1.03, 1., .102), loc='upper left', borderaxespad=0.)
    plt.savefig("MuValues.png")

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# plot
#
def plot_Cps(name):
    simulation = name.split('_')[1]
    case_names = ["FOM","ROM","HROM"]
    markercolor = ["ob","xr","+g"]
    if os.path.exists("Data/" + name + ".dat"):
        cp_min = 0
        cp_max = 0
        fig = plt.figure()
        fig.set_figwidth(12.0)
        fig.set_figheight(8.0)
        for n, name in enumerate(case_names):
            if os.path.exists("Data/" + name + "_" + simulation + ".dat"):
                x  = np.loadtxt("Data/" + name + "_" + simulation + ".dat",usecols=(0,))
                cp = np.loadtxt("Data/" + name + "_" + simulation + ".dat",usecols=(3,))
                fig = plt.plot(x, cp, markercolor[n], markersize = 3.0, label = name)
                if np.min(cp) < cp_min:
                    cp_min = np.min(cp)
                if np.max(cp) > cp_max:
                    cp_max = np.max(cp)
        fig = plt.title('Cp vs x - ' + simulation)
        fig = plt.axis([-0.05,1.35,cp_max+0.1,cp_min-0.1])
        fig = plt.ylabel('Cp')
        fig = plt.xlabel('x')
        fig = plt.grid()
        fig = plt.legend()
        fig = plt.tight_layout()
        fig = plt.savefig("Captures/" + simulation + ".png")
        fig = plt.close('all')

def plot_all_Cps():
    mu_train, mu_test = load_mu_parameters()
    case_names = ["FOM","ROM","HROM"]
    markercolor = ["ob","xr","+g"]
    for j in range(len(mu_train)):
        if os.path.exists("Data/FOM_Train" + str(j) + ".dat"):
            cp_min = 0
            cp_max = 0
            fig = plt.figure()
            fig.set_figwidth(12.0)
            fig.set_figheight(8.0)
            for n, name in enumerate(case_names):
                casename = "Test" + str(j)
                # case_name = mu_train[j][0]) + ", " + str(mu_train[j][1])
                if os.path.exists("Data/" + name + "_" + casename + ".dat"):
                    x  = np.loadtxt("Data/" + name + "_" + casename + ".dat",usecols=(0,))
                    cp = np.loadtxt("Data/" + name + "_" + casename + ".dat",usecols=(3,))
                    fig = plt.plot(x, cp, markercolor[n], markersize = 3.0, label = name)
                    if np.min(cp) < cp_min:
                        cp_min = np.min(cp)
                    if np.max(cp) > cp_max:
                        cp_max = np.max(cp)
            fig = plt.title('Cp vs x - ' + casename)
            fig = plt.axis([-0.05,1.35,cp_max+0.1,cp_min-0.1])
            fig = plt.ylabel('Cp')
            fig = plt.xlabel('x')
            fig = plt.grid()
            fig = plt.legend()
            fig = plt.tight_layout()
            fig = plt.savefig("Captures/" + casename + ".png")
            fig = plt.close('all')

    for j in range(len(mu_test)):
        if os.path.exists("Data/FOM_Test" + str(j) + ".dat"):
            cp_min = 0
            cp_max = 0
            fig = plt.figure()
            fig.set_figwidth(12.0)
            fig.set_figheight(8.0)
            for n, name in enumerate(case_names):
                casename = "Test" + str(j)
                # case_name = mu_test[j][0]) + ", " + str(mu_test[j][1])
                if os.path.exists("Data/" + name + "_" + casename + ".dat"):
                    x  = np.loadtxt("Data/" + name + "_" + casename + ".dat",usecols=(0,))
                    cp = np.loadtxt("Data/" + name + "_" + casename + ".dat",usecols=(3,))
                    fig = plt.plot(x, cp, markercolor[n], markersize = 3.0, label = name)
                    if np.min(cp) < cp_min:
                        cp_min = np.min(cp)
                    if np.max(cp) > cp_max:
                        cp_max = np.max(cp)
            fig = plt.title('Cp vs x - ' + casename)
            fig = plt.axis([-0.05,1.35,cp_max+0.1,cp_min-0.1])
            fig = plt.ylabel('Cp')
            fig = plt.xlabel('x')
            fig = plt.grid()
            fig = plt.legend()
            fig = plt.tight_layout()
            fig = plt.savefig("Captures/" + casename + ".png")
            fig = plt.close('all')

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# save / load parameters
#
def save_mu_parameters(mu_train, mu_test):
    if len(mu_train) > 0:
        archivo = open('Data/mu_train.dat', 'wb')
        pickle.dump(mu_train, archivo)
        archivo.close()
    if len(mu_test) > 0:
        archivo = open('Data/mu_test.dat', 'wb')
        pickle.dump(mu_test, archivo)
        archivo.close()

def load_mu_parameters():
    if os.path.exists("Data/mu_train.dat") and os.path.exists("Data/mu_test.dat"):
        archivo = open('Data/mu_train.dat', 'rb')
        mu_train = pickle.load(archivo)
        archivo.close()
        archivo = open('Data/mu_test.dat', 'rb')
        mu_test = pickle.load(archivo)
        archivo.close()
    elif os.path.exists("Data/mu_train.dat"):
        archivo = open('Data/mu_train.dat', 'rb')
        mu_train = pickle.load(archivo)
        archivo.close()
        mu_test = []
    elif os.path.exists("Data/mu_test.dat"):
        archivo = open('Data/mu_test.dat', 'rb')
        mu_test = pickle.load(archivo)
        archivo.close()
        mu_train = []
    return mu_train, mu_test

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
def CleanFolder():
    KratosMultiphysics.kratos_utilities.DeleteDirectoryIfExisting('Results')
    KratosMultiphysics.kratos_utilities.DeleteDirectoryIfExisting('Data')
    KratosMultiphysics.kratos_utilities.DeleteDirectoryIfExisting('Captures')
    KratosMultiphysics.kratos_utilities.DeleteDirectoryIfExisting('rom_data')
    KratosMultiphysics.kratos_utilities.DeleteFileIfExisting('MuValues.png')
    os.mkdir("Results")
    os.mkdir("Data")
    os.mkdir("Captures")
    os.mkdir("rom_data")

def CleanToTest():
    KratosMultiphysics.kratos_utilities.DeleteDirectoryIfExisting('Results')
    KratosMultiphysics.kratos_utilities.DeleteDirectoryIfExisting('Data')
    KratosMultiphysics.kratos_utilities.DeleteDirectoryIfExisting('Captures')
    os.mkdir("Results")
    os.mkdir("Data")
    os.mkdir("Captures")

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def GetRomManagerParameters():
    general_rom_manager_parameters = KratosMultiphysics.Parameters("""{
            "rom_stages_to_train" : ["ROM"],      // ["ROM","HROM"]
            "rom_stages_to_test"  : [],      // ["ROM","HROM"]
            "paralellism" : null,                        // null, TODO: add "compss"
            "projection_strategy": "galerkin",           // "lspg", "galerkin", "petrov_galerkin"
            "assembling_strategy": "global",             // "global", "elemental"
            "save_gid_output": true,                     // false, true #if true, it must exits previously in the ProjectParameters.json
            "save_vtk_output": false,
            "output_name": "id",                         // "id" , "mu"
            "ROM":{
                "svd_truncation_tolerance": 1e-12,
                "model_part_name": "MainModelPart",
                "nodal_unknowns": ["VELOCITY_POTENTIAL","AUXILIARY_VELOCITY_POTENTIAL"], // Main unknowns. Snapshots are taken from these
                "rom_basis_output_format": "numpy",                                       // "json" "numpy"
                "rom_basis_output_name": "RomParameters",
                "snapshots_control_type": "step",                                        // "step", "time"
                "snapshots_interval": 1,
                "galerkin_rom_bns_settings": {
                    "monotonicity_preserving": false
                },
                "lspg_rom_bns_settings": {
                    "train_petrov_galerkin": false,
                    "basis_strategy": "residuals",                        // 'residuals', 'jacobian', 'reactions'
                    "include_phi": false,
                    "svd_truncation_tolerance": 1e-12,
                    "solving_technique": "normal_equations",              // 'normal_equations', 'qr_decomposition'
                    "monotonicity_preserving": false
                },
                "petrov_galerkin_rom_bns_settings": {
                    "monotonicity_preserving": false
                }
            },
            "HROM":{
                "element_selection_type": "empirical_cubature",
                "initial_candidate_elements_model_part_list": [],
                "element_selection_svd_truncation_tolerance": 1e-12,
                "create_hrom_visualization_model_part" : false,
                "echo_level" : 0
            }
        }""")
    return general_rom_manager_parameters

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

if __name__ == "__main__":

    NumberofMuTrain = 5
    NumberOfMuTest  = 0

    load_old_mu_parameters    = False
    only_test                 = False

    # Definir rango de valores de mach y angulo de ataque
    mach_range  = [ 0.72, 0.74]
    angle_range = [ 1.25, 1.75]

    #::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    #::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    #::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    #::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    #::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    #::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    #::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

    if load_old_mu_parameters:
        mu_train, mu_test = load_mu_parameters()
        plot_mu_values(mu_train,mu_test)

    elif only_test:
        CleanToTest()

        fix_corners_of_parametric_space = False
        mu_train = get_multiple_params_by_Halton_sequence(NumberofMuTrain, angle_range, mach_range,
                                                           fix_corners_of_parametric_space)
        
        mu_test  = get_multiple_params_by_Halton_sequence(NumberOfMuTest , angle_range, mach_range,
                                                          fix_corners_of_parametric_space)

        save_mu_parameters(mu_train,mu_test)
        plot_mu_values(mu_train,mu_test)

    else:
        CleanFolder()

        fix_corners_of_parametric_space = True
        mu_train = get_multiple_params_by_Halton_sequence(NumberofMuTrain, angle_range, mach_range,
                                                           fix_corners_of_parametric_space)
        
        fix_corners_of_parametric_space = False
        mu_test  = get_multiple_params_by_Halton_sequence(NumberOfMuTest , angle_range, mach_range,
                                                          fix_corners_of_parametric_space)

        save_mu_parameters(mu_train,mu_test)
        plot_mu_values(mu_train,mu_test)

    general_rom_manager_parameters = GetRomManagerParameters()

    project_parameters_name = "ProjectParametersPrimalROM.json"

    rom_manager = RomManager(project_parameters_name,general_rom_manager_parameters,CustomizeSimulation,
                                   UpdateProjectParameters, UpdateMaterialParametersFile)

    rom_manager.Fit(mu_train,
                    store_all_snapshots = True)

    rom_manager.Test(mu_test)

    rom_manager.PrintErrors()
