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
from KratosMultiphysics.MeshMovingApplication.mesh_moving_analysis import MeshMovingAnalysis

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def GenerateMeshes(id, angle, typename):

    with open("ProjectParametersMeshMoving.json",'r') as parameter_file:
        mesh_parameters = KratosMultiphysics.Parameters(parameter_file.read())
    mesh_parameters["processes"]["boundary_conditions_process_list"][0]["Parameters"]["rotation_angle"].SetDouble(angle*-np.pi/180)

    model = KratosMultiphysics.Model()
    mesh_simulation = MeshMovingAnalysis(model,mesh_parameters)
    mesh_simulation.Run()

    mainmodelpart = model["MainModelPart"]
    KratosMultiphysics.ModelPartIO("Meshes/" + typename + "_mesh_" + str(id), KratosMultiphysics.IO.WRITE | KratosMultiphysics.IO.MESH_ONLY).WriteModelPart(mainmodelpart)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def CustomizeSimulation(cls, global_model, parameters):

    class CustomSimulation(cls):

        def __init__(self, model,project_parameters, custom_param = None):
            super().__init__(model,project_parameters)
            self.custom_param  = custom_param

        def Initialize(self):
            super().Initialize()
            if parameters["output_processes"].Has("gid_output"):
                nametype = parameters["output_processes"]["gid_output"][0]["Parameters"]["output_name"].GetString()
                simulationtype = nametype.split('_')[0].split('/')[1]
                if simulationtype == "ROM":
                    parameters["solver_settings"]["solving_strategy_settings"]["advanced_settings"]["first_alpha_value"].SetDouble(0.5)
                    parameters["solver_settings"]["relative_tolerance"].SetDouble(1e-9)


        def FinalizeSolutionStep(self):
            super().FinalizeSolutionStep()

            if parameters["output_processes"].Has("gid_output"):
                nametype = parameters["output_processes"]["gid_output"][0]["Parameters"]["output_name"].GetString()
                simulationtype = nametype.split('_')[0].split('/')[1]

                nametype = parameters["solver_settings"]["model_import_settings"]["input_filename"].GetString()
                typename = nametype.split('/')[-1].split('_')[0]
                id       = nametype.split('/')[1].split('_')[-1]
                # guardar aqui datos directamente de la skin
                if typename == "test":
                    fout=open("Data/"+simulationtype+"_"+typename+"_"+str(id)+".dat",'w')
                else:
                    fout=open("Data/"+simulationtype+"_"+typename+"_"+str(id)+".dat",'w')
                modelpart = self.model["MainModelPart.Body2D_Body"]
                for node in modelpart.Nodes:
                    x=node.X ; y=node.Y ; z=node.Z
                    cp=node.GetValue(KratosMultiphysics.PRESSURE_COEFFICIENT)
                    fout.write("%s %s %s %s\n" %(x,y,z,cp))
                fout.close()

        def CustomMethod(self):
            return self.custom_param

    return CustomSimulation(global_model, parameters)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def UpdateProjectParameters(parameters, mu=None):

    mach_infinity          = mu[1]
    id                     = mu[2]
    typename               = mu[3]

    parameters["solver_settings"]["model_import_settings"]["input_filename"].SetString("Meshes/" + typename + "_mesh_" + str(id))
    parameters["processes"]["boundary_conditions_process_list"][0]["Parameters"]["mach_infinity"].SetDouble(mach_infinity)

    return parameters

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def UpdateMaterialParametersFile(material_parametrs_file_name, mu):
    pass

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# get multiple parameters
#
def get_multiple_params_by_Halton_sequence(number_of_values,angle,mach,name,fix_corners_of_parametric_space):
    if fix_corners_of_parametric_space and number_of_values < 4:
        print("Setting number of values to 4.")
        number_of_values = 4
    sampler = qmc.Halton(d=2)
    # sampler = qmc.LatinHypercube(d=2)
    sample = sampler.random(number_of_values)
    mu = []
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
        #Angle of attack , Mach infinit, id, name
        mu.append([np.round(values[i,0],3), np.round(values[i,1],3), i, name])
        GenerateMeshes(i, np.round(values[i,0]), name)
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
def plot_Cps(mu_train,mu_test):
    case_names = ["FOM","ROM","HROM"]
    markercolor = ["ob","xr","+g"]
    for j in range(len(mu_train)):
        cp_min = 0
        cp_max = 0
        fig = plt.figure()
        fig.set_figwidth(12.0)
        fig.set_figheight(8.0)
        for n, name in enumerate(case_names):
            if os.path.exists("Data/"+name+"_"+"train"+"_"+str(j)+".dat"):
                x  = np.loadtxt("Data/"+name+"_"+"train"+"_"+str(j)+".dat",usecols=(0,))
                cp = np.loadtxt("Data/"+name+"_"+"train"+"_"+str(j)+".dat",usecols=(3,))
                fig = plt.plot(x, cp, markercolor[n], markersize = 3.0, label = name)
                if np.min(cp) < cp_min:
                    cp_min = np.min(cp)
                if np.max(cp) > cp_max:
                    cp_max = np.max(cp)
        fig = plt.title('Cp vs x - ' + "angle: " + str(np.round(mu_train[j][0],2)) + "º " + "mach: " + str(np.round(mu_train[j][1],2)))
        fig = plt.axis([-0.05,1.35,cp_max+0.1,cp_min-0.1])
        fig = plt.ylabel('Cp')
        fig = plt.xlabel('x')
        fig = plt.grid()
        fig = plt.legend()
        fig = plt.tight_layout()
        fig = plt.savefig("Captures/Simulation_train_" + str(j) + "_A_" + str(np.round(mu_train[j][0],2)) + "_M_" + str(mu_train[j][1])+".png")
        fig = plt.close('all')

    for j in range(len(mu_test)):
        cp_min = 0
        cp_max = 0
        fig = plt.figure()
        fig.set_figwidth(12.0)
        fig.set_figheight(8.0)
        for n, name in enumerate(case_names):
            if os.path.exists("Data/"+name+"_"+"test"+"_"+str(j)+".dat"):
                x  = np.loadtxt("Data/"+name+"_"+"test"+"_"+str(j)+".dat",usecols=(0,))
                cp = np.loadtxt("Data/"+name+"_"+"test"+"_"+str(j)+".dat",usecols=(3,))
                fig = plt.plot(x, cp, markercolor[n], markersize = 3.0, label = name)
                if np.min(cp) < cp_min:
                    cp_min = np.min(cp)
                if np.max(cp) > cp_max:
                    cp_max = np.max(cp)
        fig = plt.title('Cp vs x - ' + "angle: " + str(np.round(mu_test[j][0],2)) + "º " + "mach: " + str(np.round(mu_test[j][1],2)))
        fig = plt.axis([-0.05,1.35,cp_max+0.1,cp_min-0.1])
        fig = plt.ylabel('Cp')
        fig = plt.xlabel('x')
        fig = plt.grid()
        fig = plt.legend()
        fig = plt.tight_layout()
        fig = plt.savefig("Captures/Simulation_test_" + str(j) + "_A_" + str(np.round(mu_test[j][0])) + "_M_" + str(mu_test[j][1])+".png")
        fig = plt.close('all')

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# save / load parameters
#
def save_mu_parameters(mu_train, mu_test):
    archivo = open('Data/mu_train.dat', 'wb')
    pickle.dump(mu_train, archivo)
    archivo.close()
    archivo = open('Data/mu_test.dat', 'wb')
    pickle.dump(mu_test, archivo)
    archivo.close()

def load_mu_parameters():
    archivo = open('Data/mu_train.dat', 'rb')
    mu_train = pickle.load(archivo)
    archivo.close()
    archivo = open('Data/mu_test.dat', 'rb')
    mu_test = pickle.load(archivo)
    archivo.close()
    return mu_train, mu_test

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
def CleanFolder():
    KratosMultiphysics.kratos_utilities.DeleteDirectoryIfExisting('Results')
    KratosMultiphysics.kratos_utilities.DeleteDirectoryIfExisting('Data')
    KratosMultiphysics.kratos_utilities.DeleteDirectoryIfExisting('Captures')
    KratosMultiphysics.kratos_utilities.DeleteDirectoryIfExisting('Meshes')
    KratosMultiphysics.kratos_utilities.DeleteDirectoryIfExisting('rom_data')
    KratosMultiphysics.kratos_utilities.DeleteFileIfExisting('MuValues.png')
    KratosMultiphysics.kratos_utilities.DeleteFileIfExisting('branch_CompressiblePotentialFlow.post.lst')
    os.mkdir("Results")
    os.mkdir("Data")
    os.mkdir("Captures")
    os.mkdir("Meshes")
    os.mkdir("rom_data")

def CleanToTest():
    KratosMultiphysics.kratos_utilities.DeleteDirectoryIfExisting('Results')
    KratosMultiphysics.kratos_utilities.DeleteDirectoryIfExisting('Data')
    KratosMultiphysics.kratos_utilities.DeleteDirectoryIfExisting('Captures')
    KratosMultiphysics.kratos_utilities.DeleteDirectoryIfExisting('Meshes')
    os.mkdir("Results")
    os.mkdir("Data")
    os.mkdir("Captures")
    os.mkdir("Meshes")

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

def GetRomManagerParameters():
    general_rom_manager_parameters = KratosMultiphysics.Parameters("""{
            "rom_stages_to_train" : ["ROM"],      // ["ROM","HROM"]
            "rom_stages_to_test"  : ["ROM"],      // ["ROM","HROM"]
            "paralellism" : null,                        // null, TODO: add "compss"
            "projection_strategy": "petrov_galerkin",           // "lspg", "galerkin", "petrov_galerkin"
            "assembling_strategy": "global",             // "global", "elemental"
            "save_gid_output": true,                     // false, true #if true, it must exits previously in the ProjectParameters.json
            "save_vtk_output": false,
            "output_name": "mu",                         // "id" , "mu"
            "ROM":{
                "svd_truncation_tolerance": 1e-30,
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
                    "basis_strategy": "reactions",                        // 'residuals', 'jacobian', 'reactions'
                    "include_phi": false,
                    "svd_truncation_tolerance": 1e-30,
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
                "element_selection_svd_truncation_tolerance": 1e-30,
                "create_hrom_visualization_model_part" : false,
                "echo_level" : 0
            }
        }""")
    return general_rom_manager_parameters

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

if __name__ == "__main__":

    NumberofMuTrain = 15
    NumberOfMuTest  = 15

    load_old_mu_parameters = False
    only_test              = False

    # Definir rango de valores de mach y angulo de ataque
    mach_range  = [ 0.72, 0.73]
    angle_range = [ 1.00, 1.25]

    #::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    #::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    #::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    #::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    #::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    #::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::
    #::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::::

    if load_old_mu_parameters:
        mu_train, mu_test = load_mu_parameters()

    elif only_test:
        CleanToTest()

        fix_corners_of_parametric_space = False
        mu_train = get_multiple_params_by_Halton_sequence(NumberofMuTrain, angle_range, mach_range, "train",
                                                           fix_corners_of_parametric_space)
        
        mu_test  = get_multiple_params_by_Halton_sequence(NumberOfMuTest , angle_range, mach_range, "test" ,
                                                          fix_corners_of_parametric_space)

        save_mu_parameters(mu_train,mu_test)
        plot_mu_values(mu_train,mu_test)

    else:
        CleanFolder()

        fix_corners_of_parametric_space = True
        mu_train = get_multiple_params_by_Halton_sequence(NumberofMuTrain, angle_range, mach_range, "train",
                                                           fix_corners_of_parametric_space)
        
        fix_corners_of_parametric_space = False
        mu_test  = get_multiple_params_by_Halton_sequence(NumberOfMuTest , angle_range, mach_range, "test" ,
                                                          fix_corners_of_parametric_space)

        save_mu_parameters(mu_train,mu_test)
        plot_mu_values(mu_train,mu_test)

    general_rom_manager_parameters = GetRomManagerParameters()

    project_parameters_name = "ProjectParametersPrimalROM.json"

    rom_manager = RomManager(project_parameters_name,general_rom_manager_parameters,CustomizeSimulation,
                                   UpdateProjectParameters, UpdateMaterialParametersFile)

    rom_manager.Fit(mu_train)

    rom_manager.Test(mu_test)

    rom_manager.PrintErrors()

    plot_Cps(mu_train,mu_test)


