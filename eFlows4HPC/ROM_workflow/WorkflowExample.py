# Importing the Kratos Library
import KratosMultiphysics

# Import packages
import numpy as np

# Import pickle for serialization
import pickle

# Import pycompss
from pycompss.api.task import task
from pycompss.api.api import compss_wait_on
from pycompss.api.parameter import *

from KratosMultiphysics.RomApplication.parallel_svd import rsvd

from KratosMultiphysics.FluidDynamicsApplication.fluid_dynamics_analysis import FluidDynamicsAnalysis
from KratosMultiphysics.RomApplication.fluid_dynamics_analysis_rom import FluidDynamicsAnalysisROM
import json

#import relevant dislib array
import dislib as ds

#library for passing arguments to the script from bash
from sys import argv

#Importing the ECM here TODO paralelize it as well
from KratosMultiphysics.RomApplication.empirical_cubature_method import EmpiricalCubatureMethod

#importing the romapp
import KratosMultiphysics.RomApplication as romapp

#importing the auxiliary functions for the dislib arrays
from KratosMultiphysics.RomApplication.auxiliary_functions_workflow import load_blocks_array, load_blocks_rechunk



###############################################################################################################################################################################


class TrainROM(FluidDynamicsAnalysis):

    def __init__(self, model, project_parameters,sample):
        super().__init__(model, project_parameters)
        self.velocity = sample[0]
        #self.ith_parameter = sample[i] #more paramateres possible
        self.time_step_solution_container = []

    def ModifyInitialProperties(self):
        super().ModifyInitialProperties()
        self.project_parameters["processes"]["boundary_conditions_process_list"][0]["Parameters"]["modulus"].SetString(str(self.velocity)+'*y*(1-y)*sin(pi*t*0.5)')
        self.project_parameters["processes"]["boundary_conditions_process_list"][1]["Parameters"]["modulus"].SetString(str(self.velocity)+"*y*(1-y)" )


    def FinalizeSolutionStep(self):
        super().FinalizeSolutionStep()
        ArrayOfResults = []
        for node in self._GetSolver().GetComputingModelPart().Nodes:
            ArrayOfResults.append(node.GetSolutionStepValue(KratosMultiphysics.VELOCITY_X, 0))
            ArrayOfResults.append(node.GetSolutionStepValue(KratosMultiphysics.VELOCITY_Y, 0))
            ArrayOfResults.append(node.GetSolutionStepValue(KratosMultiphysics.PRESSURE, 0))
        self.time_step_solution_container.append(ArrayOfResults)

    def GetSnapshotsMatrix(self):
        ### Building the Snapshot matrix ####
        SnapshotMatrix = np.zeros((len(self.time_step_solution_container[0]), len(self.time_step_solution_container)))
        for i in range(len(self.time_step_solution_container)):
            Snapshot_i= np.array(self.time_step_solution_container[i])
            SnapshotMatrix[:,i] = Snapshot_i.transpose()
        self.time_step_solution_container = []
        return SnapshotMatrix


###############################################################################################################################################################################


class RetrieveDataForSimulations(FluidDynamicsAnalysis):

    def __init__(self, model, project_parameters,sample):
        super().__init__(model, project_parameters)
        self.velocity = sample[0]


    def Run(self):
        self.Initialize()
        self.time = self._GetSolver().AdvanceInTime(self.time)
        self.InitializeSolutionStep()
        self.FinalizeSolutionStep()
        self.Finalize()

    def GetData(self):
        simulations_data = {}
        final_time = self.project_parameters["problem_data"]["end_time"].GetDouble()
        time_step_size = self.project_parameters["solver_settings"]["time_stepping"]["time_step"].GetDouble()

        snapshots_per_simulation = int(final_time/time_step_size)
        number_of_dofs = int(self._GetSolver().GetComputingModelPart().NumberOfNodes()*3) #vx, vy and p #TODO make it more robust
        number_of_elements = int(self._GetSolver().GetComputingModelPart().NumberOfElements())
        number_of_conditions = int(self._GetSolver().GetComputingModelPart().NumberOfConditions())
        number_of_modes = 30 #hard coded here #TODO incorporate in the workflow a parallel fixed presicion SVD

        simulations_data["snapshots_per_simulation"] = snapshots_per_simulation
        simulations_data["desired_block_size_svd_rom"] = 500,500 #TODO automate definition of block size
        simulations_data["desired_block_size_svd_hrom"] = 5000,5000 #TODO automate definition of block size
        simulations_data["number_of_dofs"] = number_of_dofs
        simulations_data["number_of_elements"] = number_of_elements
        simulations_data["number_of_conditions"] = number_of_conditions
        simulations_data["number_of_modes"] = number_of_modes


        return simulations_data



###############################################################################################################################################################################



class RunROM_SavingData(FluidDynamicsAnalysisROM):

    def __init__(self, model, project_parameters,path,sample):
        super().__init__(model, project_parameters, path=path)
        self.velocity = sample[0]
        #self.ith_parameter = sample[i] #more paramateres possible
        self.time_step_solution_container = []

    def ModifyInitialProperties(self):
        super().ModifyInitialProperties()
        self.project_parameters["processes"]["boundary_conditions_process_list"][0]["Parameters"]["modulus"].SetString(str(self.velocity)+'*y*(1-y)*sin(pi*t*0.5)')
        self.project_parameters["processes"]["boundary_conditions_process_list"][1]["Parameters"]["modulus"].SetString(str(self.velocity)+"*y*(1-y)" )


    def FinalizeSolutionStep(self):
        super().FinalizeSolutionStep()
        ArrayOfResults = []
        for node in self._GetSolver().GetComputingModelPart().Nodes:
            ArrayOfResults.append(node.GetSolutionStepValue(KratosMultiphysics.VELOCITY_X, 0))
            ArrayOfResults.append(node.GetSolutionStepValue(KratosMultiphysics.VELOCITY_Y, 0))
            ArrayOfResults.append(node.GetSolutionStepValue(KratosMultiphysics.PRESSURE, 0))
        self.time_step_solution_container.append(ArrayOfResults)

    def GetSnapshotsMatrix(self):
        ### Building the Snapshot matrix ####
        SnapshotMatrix = np.zeros((len(self.time_step_solution_container[0]), len(self.time_step_solution_container)))
        for i in range(len(self.time_step_solution_container)):
            Snapshot_i= np.array(self.time_step_solution_container[i])
            SnapshotMatrix[:,i] = Snapshot_i.transpose()
        self.time_step_solution_container = []
        return SnapshotMatrix


###############################################################################################################################################################################


class TrainHROM(FluidDynamicsAnalysisROM):

    def __init__(self, model, project_parameters,path,sample,ElementSelector):
        super().__init__(model, project_parameters,path=path,hyper_reduction_element_selector=ElementSelector)
        self.velocity = sample[0]
        #self.ith_parameter = sample[i] #more paramateres possible
        self.time_step_solution_container = []

    def ModifyInitialProperties(self):
        super().ModifyInitialProperties()
        self.project_parameters["processes"]["boundary_conditions_process_list"][0]["Parameters"]["modulus"].SetString(str(self.velocity)+'*y*(1-y)*sin(pi*t*0.5)')
        self.project_parameters["processes"]["boundary_conditions_process_list"][1]["Parameters"]["modulus"].SetString(str(self.velocity)+"*y*(1-y)" )


    def GetResidualsSnapshots(self):
        return self.residuals_snapshots


###############################################################################################################################################################################


class RunHROM_SavingData(FluidDynamicsAnalysisROM):

    def __init__(self, model, project_parameters,path,sample):
        super().__init__(model, project_parameters,path=path)
        self.velocity = sample[0]
        #self.ith_parameter = sample[i] #more paramateres possible
        self.time_step_solution_container = []

    def ModifyInitialProperties(self):
        super().ModifyInitialProperties()
        self.project_parameters["processes"]["boundary_conditions_process_list"][0]["Parameters"]["modulus"].SetString(str(self.velocity)+'*y*(1-y)*sin(pi*t*0.5)')
        self.project_parameters["processes"]["boundary_conditions_process_list"][1]["Parameters"]["modulus"].SetString(str(self.velocity)+"*y*(1-y)" )



    def ModifyAfterSolverInitialize(self):
        super().ModifyAfterSolverInitialize()
        with open(self.path + '/ElementsAndWeights.json') as f:
            hrom_parameters = KratosMultiphysics.Parameters(f.read())
        computing_model_part = self._GetSolver().GetComputingModelPart().GetRootModelPart()
        # Set the HROM weights in elements and conditions
        hrom_weights_elements = hrom_parameters["Elements"]
        for key,value in zip(hrom_weights_elements.keys(), hrom_weights_elements.values()):
            computing_model_part.GetElement(int(key)+1).SetValue(romapp.HROM_WEIGHT, value.GetDouble()) #FIXME: FIX THE +1

        hrom_weights_condtions = hrom_parameters["Conditions"]
        for key,value in zip(hrom_weights_condtions.keys(), hrom_weights_condtions.values()):
            computing_model_part.GetCondition(int(key)+1).SetValue(romapp.HROM_WEIGHT, value.GetDouble()) #FIXME: FIX THE +1

    def FinalizeSolutionStep(self):
        super().FinalizeSolutionStep()
        ArrayOfResults = []
        for node in self._GetSolver().GetComputingModelPart().Nodes:
            ArrayOfResults.append(node.GetSolutionStepValue(KratosMultiphysics.VELOCITY_X, 0))
            ArrayOfResults.append(node.GetSolutionStepValue(KratosMultiphysics.VELOCITY_Y, 0))
            ArrayOfResults.append(node.GetSolutionStepValue(KratosMultiphysics.PRESSURE, 0))
        self.time_step_solution_container.append(ArrayOfResults)

    def GetSnapshotsMatrix(self):
        ### Building the Snapshot matrix ####
        SnapshotMatrix = np.zeros((len(self.time_step_solution_container[0]), len(self.time_step_solution_container)))
        for i in range(len(self.time_step_solution_container)):
            Snapshot_i= np.array(self.time_step_solution_container[i])
            SnapshotMatrix[:,i] = Snapshot_i.transpose()
        self.time_step_solution_container = []
        return SnapshotMatrix


###############################################################################################################################################################################



# function generating the sample
def GetValueFromListList(Cases,iteration):
    Case = Cases[iteration]
    return Case



@task(returns = np.array)
def ExecuteInstance_Task(pickled_model,pickled_parameters,path,Cases,instance):
    # overwrite the old model serializer with the unpickled one
    model_serializer = pickle.loads(pickled_model)
    current_model = KratosMultiphysics.Model()
    model_serializer.Load("ModelSerialization",current_model)
    del(model_serializer)
    # overwrite the old parameters serializer with the unpickled one
    serialized_parameters = pickle.loads(pickled_parameters)
    current_parameters = KratosMultiphysics.Parameters()
    serialized_parameters.Load("ParametersSerialization",current_parameters)
    del(serialized_parameters)
    # get sample
    sample = GetValueFromListList(Cases,instance) # take one of them
    simulation = TrainROM(current_model,current_parameters,sample)
    simulation.Run()
    return simulation.GetSnapshotsMatrix()



@task(returns = np.array)
def ExecuteInstance_Task_ROM(pickled_model,pickled_parameters,path,Cases,instance):
    # overwrite the old model serializer with the unpickled one
    model_serializer = pickle.loads(pickled_model)
    current_model = KratosMultiphysics.Model()
    model_serializer.Load("ModelSerialization",current_model)
    del(model_serializer)
    # overwrite the old parameters serializer with the unpickled one
    serialized_parameters = pickle.loads(pickled_parameters)
    current_parameters = KratosMultiphysics.Parameters()
    serialized_parameters.Load("ParametersSerialization",current_parameters)
    del(serialized_parameters)
    # get sample
    sample = GetValueFromListList(Cases,instance) # take one of them
    simulation = RunROM_SavingData(current_model,current_parameters,path,sample)
    simulation.Run()
    return simulation.GetSnapshotsMatrix()



@task(returns = np.array)
def ExecuteInstance_Task_HROM(pickled_model,pickled_parameters,path,Cases,instance):
    # overwrite the old model serializer with the unpickled one
    model_serializer = pickle.loads(pickled_model)
    current_model = KratosMultiphysics.Model()
    model_serializer.Load("ModelSerialization",current_model)
    del(model_serializer)
    # overwrite the old parameters serializer with the unpickled one
    serialized_parameters = pickle.loads(pickled_parameters)
    current_parameters = KratosMultiphysics.Parameters()
    serialized_parameters.Load("ParametersSerialization",current_parameters)
    del(serialized_parameters)
    # get sample
    sample = GetValueFromListList(Cases,instance) # take one of them
    simulation = RunHROM_SavingData(current_model,current_parameters,path,sample)
    simulation.Run()
    return simulation.GetSnapshotsMatrix()



#TODO this is not doing it very efficiently. It should return ds_arrays instead of np_arrays
@task(returns = np.array)
def ExecuteInstance_Task_TrainHROM(pickled_model,pickled_parameters,path,Cases,instance,ElementSelector):
    # overwrite the old model serializer with the unpickled one
    model_serializer = pickle.loads(pickled_model)
    current_model = KratosMultiphysics.Model()
    model_serializer.Load("ModelSerialization",current_model)
    del(model_serializer)
    # overwrite the old parameters serializer with the unpickled one
    serialized_parameters = pickle.loads(pickled_parameters)
    current_parameters = KratosMultiphysics.Parameters()
    serialized_parameters.Load("ParametersSerialization",current_parameters)
    del(serialized_parameters)
    # get sample
    sample = GetValueFromListList(Cases,instance) # take one of them
    simulation = TrainHROM(current_model,current_parameters,path,sample,ElementSelector)
    simulation.Run()
    return simulation.GetResidualsSnapshots()



@task(parameter_file_name=FILE_IN,returns=2)
def SerializeModelParameters_Task(parameter_file_name):
    with open(parameter_file_name,'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())
    model = KratosMultiphysics.Model()
    fake_sample = [5]
    simulation = TrainROM(model,parameters,fake_sample)
    serialized_model = KratosMultiphysics.StreamSerializer()
    serialized_model.Save("ModelSerialization",simulation.model)
    serialized_parameters = KratosMultiphysics.StreamSerializer()
    serialized_parameters.Save("ParametersSerialization",simulation.project_parameters)
    # pickle dataserialized_data
    pickled_model = pickle.dumps(serialized_model, 2) # second argument is the protocol and is NECESSARY (according to pybind11 docs)
    pickled_parameters = pickle.dumps(serialized_parameters, 2)
    print("\n","#"*50," SERIALIZATION COMPLETED ","#"*50,"\n")
    return pickled_model,pickled_parameters



@task(parameter_file_name=FILE_IN, returns = 1)
def GetSimulationsData(parameter_file_name):
    with open(parameter_file_name,'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())
    model = KratosMultiphysics.Model()
    fake_sample = [5]
    simulation = RetrieveDataForSimulations(model,parameters,fake_sample)
    simulation.Run()
    return simulation.GetData()



def Stage0_GetDataForSimulations():
    working_path = argv[1]
    parameter_file_name = working_path + "/ProjectParameters_workflow.json"
    data = compss_wait_on(GetSimulationsData(parameter_file_name))
    return data



def Stage1_RunFOM(parameters, simulations_data):
    # set the ProjectParameters.json path
    working_path = argv[1]
    parameter_file_name = working_path + "/ProjectParameters_workflow.json"
    # create a serialization of the model and of the project parameters
    pickled_model,pickled_parameters = SerializeModelParameters_Task(parameter_file_name)
    TotalNumberOFCases = len(parameters)

    blocks = []
    # start algorithm
    for instance in range (0,TotalNumberOFCases):
        blocks.append(ExecuteInstance_Task(pickled_model,pickled_parameters,working_path,parameters,instance))

    number_of_dofs = simulations_data["number_of_dofs"]
    snapshots_per_simulation = simulations_data["snapshots_per_simulation"]
    expected_shape = (number_of_dofs, TotalNumberOFCases*snapshots_per_simulation) #We will know the size of the array!
    desired_block_size = simulations_data["desired_block_size_svd_rom"]
    simulation_shape = (number_of_dofs, snapshots_per_simulation)
    #TODO cope with failing simulations

    arr = load_blocks_rechunk(blocks, shape = expected_shape, block_size = simulation_shape, new_block_size = desired_block_size)

    return arr




def Stage2_rSVD(SnapshotsMatrix, simulations_data):

    desired_rank = simulations_data["number_of_modes"]
    u,_ = rsvd(SnapshotsMatrix, desired_rank)


    ### Saving the nodal basis ###  #TODO improve format
    basis_POD={"rom_settings":{},"nodal_modes":{}}
    basis_POD["rom_settings"]["nodal_unknowns"] = ["VELOCITY_X","VELOCITY_Y","PRESSURE"]
    basis_POD["rom_settings"]["number_of_rom_dofs"] = np.shape(u)[1]
    Dimensions = len(basis_POD["rom_settings"]["nodal_unknowns"])
    N_nodes=np.shape(u)[0]/Dimensions
    N_nodes = int(N_nodes)
    node_Id=np.linspace(1,N_nodes,N_nodes)
    i = 0
    for j in range (0,N_nodes):
        basis_POD["nodal_modes"][int(node_Id[j])] = (u[i:i+Dimensions].tolist())
        i=i+Dimensions

    with open('RomParameters.json', 'w') as f:
        json.dump(basis_POD,f, indent=2)
    print('\n\nNodal basis printed in json format\n\n')




def Stage3_RunROM(parameters, simulations_data):
    # set the ProjectParameters.json path
    working_path = argv[1]
    parameter_file_name = working_path + "/ProjectParameters_workflow.json"
    # create a serialization of the model and of the project parameters
    pickled_model,pickled_parameters = SerializeModelParameters_Task(parameter_file_name)
    TotalNumberOFCases = len(parameters)
    blocks = []
    # start algorithm
    for instance in range (0,TotalNumberOFCases):
        blocks.append(ExecuteInstance_Task_ROM(pickled_model,pickled_parameters,working_path,parameters,instance))

    number_of_dofs = simulations_data["number_of_dofs"]
    snapshots_per_simulation = simulations_data["snapshots_per_simulation"]
    expected_shape = (number_of_dofs, TotalNumberOFCases*snapshots_per_simulation) #We will know the size of the array!
    desired_block_size = simulations_data["desired_block_size_svd_rom"]
    simulation_shape = (number_of_dofs, snapshots_per_simulation)
    #TODO cope with failing simulations

    arr = load_blocks_rechunk(blocks, shape = expected_shape, block_size = simulation_shape, new_block_size = desired_block_size)

    return arr



def Stage4_TrainHROM(parameters, simulations_data):
    # set the ProjectParameters.json path
    working_path = argv[1]
    parameter_file_name = working_path + "/ProjectParameters_workflow.json"
    # create a serialization of the model and of the project parameters
    pickled_model,pickled_parameters = SerializeModelParameters_Task(parameter_file_name)
    TotalNumberOFCases = len(parameters)
    blocks = []
    # start algorithm
    for instance in range (0,TotalNumberOFCases):
        blocks.append(ExecuteInstance_Task_TrainHROM(pickled_model,pickled_parameters,working_path,parameters,instance,'EmpiricalCubature'))

    number_of_modes = simulations_data["number_of_modes"]
    number_of_elements = simulations_data["number_of_elements"]
    number_of_conditions = simulations_data["number_of_conditions"]
    snapshots_per_simulation = simulations_data["snapshots_per_simulation"]
    expected_shape = (number_of_elements+number_of_conditions, number_of_modes*TotalNumberOFCases*snapshots_per_simulation) #We will know the size of the array!
    desired_block_size = simulations_data["desired_block_size_svd_rom"]
    simulation_shape = (number_of_elements+number_of_conditions, number_of_modes*snapshots_per_simulation)
    #TODO cope with failing simulations

    arr = load_blocks_rechunk(blocks, shape = expected_shape, block_size = simulation_shape, new_block_size = desired_block_size)
    BasisResiduals,_ = rsvd(arr, number_of_modes**2)

    ECM = EmpiricalCubatureMethod(ECM_tolerance = 1e-6)
    ECM.SetUp(BasisResiduals)
    ECM.Run()
    w = np.squeeze(ECM.w)
    ### Saving Elements and conditions
    ElementsAndWeights = {}
    ElementsAndWeights["Elements"] = {}
    ElementsAndWeights["Conditions"] = {}
    #Only one element found !
    if type(ECM.z)==np.int64 or type(ECM.z)==np.int32:
        if ECM.z <=number_of_elements-1:
            ElementsAndWeights["Elements"][int(ECM.z)] = (float(w))
        else:
            ElementsAndWeights["Conditions"][int(ECM.z)-number_of_elements] = (float(w))
    #Many elements found
    else:
        for j in range (0,len(ECM.z)):
            if ECM.z[j] <= number_of_elements-1:
                ElementsAndWeights["Elements"][int(ECM.z[j])] = (float(w[j]))
            else:
                ElementsAndWeights["Conditions"][int(ECM.z[j])-number_of_elements] = (float(w[j]))

    with open('ElementsAndWeights.json', 'w') as f:
        json.dump(ElementsAndWeights,f, indent=2)
    print('\n\n Elements and conditions selected have been saved in a json file\n\n')




def Stage5_RunHROM(parameters, simulations_data):
    # set the ProjectParameters.json path
    working_path = argv[1]
    parameter_file_name = working_path + "/ProjectParameters_workflow.json"
    # create a serialization of the model and of the project parameters
    pickled_model,pickled_parameters = SerializeModelParameters_Task(parameter_file_name)
    TotalNumberOFCases = len(parameters)
    blocks = []
    # start algorithm
    for instance in range (0,TotalNumberOFCases):
        blocks.append(ExecuteInstance_Task_HROM(pickled_model,pickled_parameters,working_path,parameters,instance))
    number_of_dofs = simulations_data["number_of_dofs"]
    snapshots_per_simulation = simulations_data["snapshots_per_simulation"]
    expected_shape = (number_of_dofs, TotalNumberOFCases*snapshots_per_simulation) #We will know the size of the array!
    desired_block_size = simulations_data["desired_block_size_svd_rom"]
    simulation_shape = (number_of_dofs, snapshots_per_simulation)
    #TODO cope with failing simulations

    arr = load_blocks_rechunk(blocks, shape = expected_shape, block_size = simulation_shape, new_block_size = desired_block_size)

    return arr



def compare_FOM_vs_ROM(SnapshotsMatrixROM, SnapshotsMatrix):
    #using the Frobenious norm of the snapshots of the solution
    original_norm= np.linalg.norm((SnapshotsMatrix.norm().collect()))
    intermediate = ds.data.matsubtract(SnapshotsMatrixROM,SnapshotsMatrix) #(available on latest release)
    intermediate = np.linalg.norm((intermediate.norm().collect()))
    final = intermediate/original_norm
    np.save('relative_error_rom.npy', final)



def compare_ROM_vs_HROM(SnapshotsMatrixROM, SnapshotsMatrixHROM):
    #using the Frobenious norm of the snapshots of the solution
    original_norm= np.linalg.norm((SnapshotsMatrixROM.norm().collect()))
    intermediate = ds.data.matsubtract(SnapshotsMatrixROM,SnapshotsMatrixHROM) #(available on latest release)
    intermediate = np.linalg.norm((intermediate.norm().collect()))
    final = intermediate/original_norm
    np.save('relative_error_hrom.npy', final)



def prepare_files():
    """pre-pending the absolut path of the files in the Project Parameters"""
    with open('ProjectParameters.json','r') as f:
        updated_project_parameters = json.load(f)
        file_input_name = updated_project_parameters["solver_settings"]["model_import_settings"]["input_filename"]
        materials_filename = updated_project_parameters["solver_settings"]["material_import_settings"]["materials_filename"]
        working_path = argv[1]
        updated_project_parameters["solver_settings"]["model_import_settings"]["input_filename"] = working_path + '/'+ file_input_name
        updated_project_parameters["solver_settings"]["material_import_settings"]["materials_filename"] = working_path +'/'+ materials_filename

    with open('ProjectParameters_workflow.json','w') as f:
        json.dump(updated_project_parameters, f, indent = 4)



if __name__ == '__main__':

    parameters=[[5],[6]] #inlet fluid velocity
    """
    We define the parameters for the simulation.
    In this case a single parameter is defined.
    More parameters are possible.
    """


    prepare_files()
    """
    Absolute paths should be used in the ProjectParameters
    and Materials files for running in a cluster
    """


    simulations_data = Stage0_GetDataForSimulations()
    """
    Stage 0
    - The shape of the expected matrices is obtained to allow paralelization
    """


    SnapshotsMatrix = Stage1_RunFOM(parameters, simulations_data)
    """
    Stage 1
    - launches in parallel a Full Order Model (FOM) simulation for each simulation parameter.
    - returns a distributed array (ds-array) with the results of the simulations.
    """


    Stage2_rSVD(SnapshotsMatrix, simulations_data)
    """
    Stage 2
    - computes the "fixed rank" randomized SVD in parallel using the dislib library
    - stores the ROM basis in JSON format #TODO improve format
    """


    SnapshotsMatrixROM = Stage3_RunROM(parameters, simulations_data)
    """
    Stage 3
    - launches the Reduced Order Model simulations for the same simulation parameters used for the FOM
    - stores the results in a distributed array
    """

    compare_FOM_vs_ROM(SnapshotsMatrix, SnapshotsMatrixROM)
    """
    - Computes the Frobenius norm of the difference of Snapshots FOM and ROM
    - TODO add more parameters in a smart way if norm is above a given threshold
    """


    Stage4_TrainHROM(parameters, simulations_data)
    """
    Stage 4
    - Launches the same ROM simulation and builds the projected residual in distributed array
    - Analyses the matrix of projected residuals and obtains the elements and weights
    """


    SnapshotsMatrixHROM = Stage5_RunHROM(parameters,simulations_data)
    """
    Stage 5
    - launches the Hyper Reduced Order Model simulations for the same simulation parameters used for the FOM and ROM
    - stores the results in a distributed array
    """


    compare_ROM_vs_HROM(SnapshotsMatrixROM, SnapshotsMatrixHROM)
    """
    - Computes the Frobenius norm of the difference of Snapshots ROM and HROM
    - TODO add more parameters in a smart way if norm is above a given threshold
    """







