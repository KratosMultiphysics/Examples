# Importing the Kratos Library
from ast import arg
import KratosMultiphysics

# Import packages
import numpy as np

# Import pickle for serialization
import pickle

# Import pycompss
from pycompss.api.task import task
from pycompss.api.api import compss_wait_on, compss_barrier
from pycompss.api.parameter import *
from pycompss.api.constraint import constraint
from pathlib import Path

from KratosMultiphysics.RomApplication.parallel_svd import rsvd
from KratosMultiphysics.RomApplication.randomized_singular_value_decomposition import RandomizedSingularValueDecomposition
from KratosMultiphysics.RomApplication.calculate_rom_basis_output_process import CalculateRomBasisOutputProcess
import json

#importing also dislib's tsqr
from dislib.decomposition.tsqr.base import tsqr

#import relevant dislib array
import dislib as ds

#library for passing arguments to the script from bash
from sys import argv

from demo_case_non_intrusive import interpolate_parameters


#Importing the ECM here TODO paralelize it as well
from KratosMultiphysics.RomApplication.empirical_cubature_method import EmpiricalCubatureMethod

from KratosMultiphysics.CoSimulationApplication.co_simulation_analysis import CoSimulationAnalysis

#importing the auxiliary functions for the dislib arrays
from KratosMultiphysics.RomApplication.auxiliary_functions_workflow import load_blocks_array, load_blocks_rechunk



import pdb

###############################################################################################################################################################################


class TrainROM(CoSimulationAnalysis):

    def __init__(self,cosim_parameters,sample,path):
        super().__init__(cosim_parameters)
        self.sample=sample
        self.path=path
        self.node_in_solid = 15216 #these node ids were found a posteriori from the HROM model part. Better ID can be found from the GiD file (I couldnt open it from home)
        self.node_in_fluid = 45947
        self.matrix_of_solid_fluid_solutions = None  #np.array([[fluid_0, solid_0], ..., [fluid_m, solid_m]])

    def Initialize(self):
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
        for solver in self._solver.solver_wrappers.keys():
            this_analysis_stage = self._solver._GetSolver(solver)._analysis_stage
            computing_model_part = this_analysis_stage._GetSolver().GetComputingModelPart()
            if solver == 'fluid':
                fluid_solution = computing_model_part.GetNode(self.node_in_fluid).GetSolutionStepValue(KratosMultiphysics.TEMPERATURE, 0)
            if solver == 'solid':
                solid_solution = computing_model_part.GetNode(self.node_in_solid).GetSolutionStepValue(KratosMultiphysics.TEMPERATURE, 0)
        if self.matrix_of_solid_fluid_solutions is None:
            self.matrix_of_solid_fluid_solutions= np.array([[fluid_solution],[solid_solution]])
        else:
            self.matrix_of_solid_fluid_solutions = np.c_[self.matrix_of_solid_fluid_solutions, np.array([[fluid_solution],[solid_solution]])]

    def GetSnapshotsMatrices(self):
        matrices = []
        for solver in self._solver.solver_wrappers.keys():
            for process in self._solver._GetSolver(solver)._analysis_stage._GetListOfOutputProcesses():
                if isinstance(process, CalculateRomBasisOutputProcess):
                    BasisOutputProcess = process
            matrices.append(BasisOutputProcess._GetSnapshotsMatrix())

        return matrices


    def GetSolutionsAtControlPoint(self):
        return self.matrix_of_solid_fluid_solutions



###############################################################################################################################################################################


class RetrieveDataForSimulations(CoSimulationAnalysis):

    def __init__(self, project_parameters, sample):
        super().__init__(project_parameters)
        self.sample = sample

    def Run(self):
        self.Initialize()
        self.time = self._GetSolver().AdvanceInTime(self.time)
        self.InitializeSolutionStep()
        self.Finalize()




    def GetData(self):
        cosim_simulation_data = []
        final_time = self.end_time
        for solver in self._solver.solver_wrappers.keys():
            simulations_data = {}
            simulations_data["solver_name"] = solver
            this_analysis_stage = self._solver._GetSolver(solver)._analysis_stage

            time_step_size = this_analysis_stage.project_parameters["solver_settings"]["time_stepping"]["time_step"].GetDouble()

            snapshots_per_simulation = int(final_time/time_step_size) # + 1 #TODO fix extra time step that sometimes appears due to rounding
            number_of_dofs = int(this_analysis_stage._GetSolver().GetComputingModelPart().NumberOfNodes()) #made for TEMPERATURE #TODO make it more robust
            number_of_elements = int(this_analysis_stage._GetSolver().GetComputingModelPart().NumberOfElements())
            number_of_conditions = int(this_analysis_stage._GetSolver().GetComputingModelPart().NumberOfConditions())
            number_of_modes = 30 #hard coded here #TODO incorporate in the workflow a parallel fixed presicion SVD

            simulations_data["snapshots_per_simulation"] = snapshots_per_simulation
            simulations_data["desired_block_size_svd_rom"] = int(number_of_dofs/10),snapshots_per_simulation #TODO automate definition of block size
            simulations_data["desired_block_size_svd_hrom"] = int((number_of_elements+number_of_conditions)/10) , snapshots_per_simulation+number_of_modes  #TODO automate definition of block size
            simulations_data["number_of_dofs"] = number_of_dofs
            simulations_data["number_of_elements"] = number_of_elements
            simulations_data["number_of_conditions"] = number_of_conditions
            simulations_data["number_of_modes"] = number_of_modes
            cosim_simulation_data.append(simulations_data)

        return cosim_simulation_data



###############################################################################################################################################################################


class TrainHROM(CoSimulationAnalysis):

    def __init__(self,cosim_parameters,sample,path):
        super().__init__(cosim_parameters)
        self.sample = sample
        self.path = path


    def Initialize(self):
        for solver in self._solver.solver_wrappers.keys():
            if solver == 'solid':
                this_analysis_stage = self._solver._GetSolver(solver)._analysis_stage
                this_analysis_stage.project_parameters["processes"]["list_other_processes"][0]["Parameters"]["value"].SetDouble(self.sample[0])
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

    def GetSnapshotsMatrices(self):
        residuals_projected = []
        for solver in self._solver.solver_wrappers.keys():
            this_analysis_stage = self._solver._GetSolver(solver)._analysis_stage
            residuals_projected.append(this_analysis_stage.GetHROM_utility()._GetResidualsProjectedMatrix())

        return residuals_projected


###############################################################################################################################################################################



class CreateHROMModelParts(CoSimulationAnalysis):


    def __init__(self, project_parameters):
        super().__init__(project_parameters)


    def Run(self):
        self.Initialize()
        self.time = self._GetSolver().AdvanceInTime(self.time)
        self.InitializeSolutionStep()
        self.Finalize()


    def ComputeParts(self):
        for solver in self._solver.solver_wrappers.keys():
            this_analysis_stage = self._solver._GetSolver(solver)._analysis_stage
            this_analysis_stage.GetHROM_utility().hyper_reduction_element_selector.w = np.load(this_analysis_stage.GetHROM_utility().rom_basis_output_folder / 'aux_w.npy')
            this_analysis_stage.GetHROM_utility().hyper_reduction_element_selector.z = np.load(this_analysis_stage.GetHROM_utility().rom_basis_output_folder / 'aux_z.npy')
            this_analysis_stage.GetHROM_utility().AppendHRomWeightsToRomParameters()
            this_analysis_stage.GetHROM_utility().CreateHRomModelParts()


###############################################################################################################################################################################


# function generating the sample
def GetValueFromListList(Cases,iteration):
    Case = Cases[iteration]
    return Case



@constraint(computingUnits=argv[2])
@task(returns = 3)
def ExecuteInstance_Task(pickled_parameters,Cases,instance, path):
    # overwrite the old parameters serializer with the unpickled one
    serialized_parameters = pickle.loads(pickled_parameters)
    current_parameters = KratosMultiphysics.Parameters()
    serialized_parameters.Load("ParametersSerialization",current_parameters)
    del(serialized_parameters)
    # get sample
    sample = GetValueFromListList(Cases,instance) # take one of them
    simulation = TrainROM(current_parameters,sample,path)
    simulation.Run()
    snapshots = simulation.GetSnapshotsMatrices()
    control_point_matrix = simulation.GetSolutionsAtControlPoint()
    return snapshots[0], snapshots[1], control_point_matrix



@constraint(computingUnits=argv[2])
@task(returns = 2)
def ExecuteInstance_Task_TrainHROM_workflow(pickled_parameters,Cases,instance,path):
    # overwrite the old parameters serializer with the unpickled one
    serialized_parameters = pickle.loads(pickled_parameters)
    current_parameters = KratosMultiphysics.Parameters()
    serialized_parameters.Load("ParametersSerialization",current_parameters)
    del(serialized_parameters)
    # get sample
    sample = GetValueFromListList(Cases,instance) # take one of them
    simulation = TrainHROM(current_parameters,sample,path)
    simulation.Run()
    snapshots = simulation.GetSnapshotsMatrices()
    return snapshots[0], snapshots[1]






@constraint(computingUnits=argv[2])
@task(parameter_file_name=FILE_IN,returns=1) #priobably not required !!!???
def SerializeModelParameters_Task(parameter_file_name):
    with open(parameter_file_name,'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())
    serialized_parameters = KratosMultiphysics.StreamSerializer()
    serialized_parameters.Save("ParametersSerialization", parameters)
    # pickle model and parameters
    pickled_parameters = pickle.dumps(serialized_parameters, 2)  # second argument is the protocol and is NECESSARY (according to pybind11 docs)
    print("\n","#"*50," SERIALIZATION COMPLETED ","#"*50,"\n")
    return pickled_parameters






def GetSimulationsData(parameter_file_name):
    with open(parameter_file_name,'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())
    fake_sample = [5,200]
    simulation = RetrieveDataForSimulations(parameters,fake_sample)
    simulation.Run()
    return simulation.GetData()




def ComputeHROMModelParts(parameter_file_name):
    with open(parameter_file_name,'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())
    simulation = CreateHROMModelParts(parameters)
    simulation.Run()
    simulation.ComputeParts()
    return 0





@constraint(computingUnits=argv[2])
@task(returns=2)
def GetElementsOfPartition(np_array, global_ids, global_weights, title):

    projected_residuals_matrix = np_array * global_weights[:, np.newaxis]

    #u,_,_ = truncated_svd(projected_residuals_matrix, 0)  #numpy "exact" version
    if title == 'intermidiate':
        u, _, _, _ = RandomizedSingularValueDecomposition().Calculate(projected_residuals_matrix) #randomized version with machine precision
        constrain_sum_of_weights = False # setting it to "True" worsens the approximation. Need to implement the orthogonal complement rather and not the row of 1's is implemented
    else:
        u, _, _, _ = RandomizedSingularValueDecomposition().Calculate(projected_residuals_matrix, 1e-6) #randomized version with user-defined tolerance
        constrain_sum_of_weights = False # setting it to "True" worsens the approximation. Need to implement the orthogonal complement rather and not the row of 1's is implemented

    ElementSelector = EmpiricalCubatureMethod()
    ElementSelector.SetUp( u, constrain_sum_of_weights)
    ElementSelector.Initialize()
    ElementSelector.Calculate()
    local_ids = np.squeeze(ElementSelector.z)
    weights = np.squeeze(ElementSelector.w)
    indexes_2 = np.argsort(local_ids) #this is necessary, since dislib cannot return un-ordered indexes

    #return global_ids[local_ids], (weights * global_weights[local_ids])
    return global_ids[local_ids[indexes_2]], (weights[indexes_2] * global_weights[local_ids[indexes_2]])







@constraint(computingUnits=argv[2])
@task()
def SavingElementsAndWeights(working_path,number_of_elements,z,w):
    weights = np.squeeze(w)
    indexes = z
    element_indexes = np.where( indexes < number_of_elements )[0]
    condition_indexes = np.where( indexes >= number_of_elements )[0]
    np.save(working_path+'aux_w.npy',weights)
    np.save(working_path+'aux_z.npy',indexes)
    np.save(working_path+'HROM_ElementWeights.npy',weights[element_indexes])
    np.save(working_path+'HROM_ConditionWeights.npy',weights[condition_indexes])
    np.save(working_path+'HROM_ElementIds.npy',indexes[element_indexes]) #FIXME fix the -1 in the indexes of numpy and ids of Kratos
    np.save(working_path+'HROM_ConditionIds.npy',indexes[condition_indexes]-number_of_elements) #FIXME fix the -1 in the indexes of numpy and ids of Kratos

    return 0




@constraint(computingUnits=argv[2])
@task(returns=1)
def SavingRomParameters(working_path,u,name,conditions_list,nodal_neighbours_list):
    rom_basis_dict = {
        "rom_manager" : True,
        "train_hrom": False,
        "run_hrom": False,
        "projection_strategy": "galerkin",
        "assembling_strategy": "global",
        "rom_format": "numpy",
        "train_petrov_galerkin": {
            "train": False,
            "basis_strategy": "residuals",
            "include_phi": False,
            "svd_truncation_tolerance": 1e-6
        },
        "rom_settings": {},
        "hrom_settings": {},
        "nodal_modes": {},
        "elements_and_weights" : {}
    }

    nodal_unknowns = ["TEMPERATURE"]#RomParams["nodal_unknowns"].GetStringArray()
    rom_basis_dict["rom_basis_output_folder"] = "rom_data" #RomParams["rom_basis_output_folder"]
    rom_basis_dict["hrom_settings"]["hrom_format"] = "numpy"
    rom_basis_dict["hrom_settings"]["include_conditions_model_parts_list"] = conditions_list
    rom_basis_dict["hrom_settings"]["include_nodal_neighbouring_elements_model_parts_list"] = nodal_neighbours_list
    rom_basis_dict["hrom_settings"]["create_hrom_visualization_model_part"] = False
    rom_basis_dict["hrom_settings"]["include_elements_model_parts_list"] = []
    rom_basis_dict["hrom_settings"]["include_minimum_condition"] = False
    rom_basis_dict["hrom_settings"]["include_condition_parents"] = True
    n_nodal_unknowns = len(nodal_unknowns)
    snapshot_variables_list = []
    for var_name in nodal_unknowns:
        if not KratosMultiphysics.KratosGlobals.HasVariable(var_name):
            err_msg = "\'{}\' variable in \'nodal_unknowns\' is not in KratosGlobals. Please check provided value.".format(var_name)
        if not KratosMultiphysics.KratosGlobals.GetVariableType(var_name):
            err_msg = "\'{}\' variable in \'nodal_unknowns\' is not double type. Please check provide double type variables (e.g. [\"DISPLACEMENT_X\",\"DISPLACEMENT_Y\"]).".format(var_name)
        snapshot_variables_list.append(KratosMultiphysics.KratosGlobals.GetVariable(var_name))


    # Save the nodal basis
    rom_basis_dict["rom_settings"]["nodal_unknowns"] = [var.Name() for var in snapshot_variables_list]
    rom_basis_dict["rom_settings"]["number_of_rom_dofs"] = np.shape(u)[1] #TODO: This is way misleading. I'd call it number_of_basis_modes or number_of_rom_modes
    rom_basis_dict["projection_strategy"] = "galerkin" # Galerkin: (Phi.T@K@Phi dq= Phi.T@b), LSPG = (K@Phi dq= b), Petrov-Galerkin = (Psi.T@K@Phi dq = Psi.T@b)
    rom_basis_dict["assembling_strategy"] = "global" # Assemble the ROM globally or element by element: "global" (Phi_g @ J_g @ Phi_g), "element by element" sum(Phi_e^T @ K_e @ Phi_e)
    rom_basis_dict["rom_settings"]["petrov_galerkin_number_of_rom_dofs"] = 0
    rom_basis_output_folder = Path(working_path + '/' + name)  #rom_basis_dict["rom_basis_output_folder"] + '_' + #TODO use the full path and not only the name of the sover!!
    if not rom_basis_output_folder.exists():
        rom_basis_output_folder.mkdir(parents=True)

    # Storing modes in Numpy format
    np.save(rom_basis_output_folder / "RightBasisMatrix.npy", u)
    np.save(rom_basis_output_folder / "NodeIds.npy", np.arange(1,((u.shape[0]+1)/n_nodal_unknowns), 1, dtype=int))

    # Creating the ROM JSON file containing or not the modes depending on "self.rom_basis_output_format"

    output_filename = working_path / rom_basis_output_folder / "RomParameters.json"
    with output_filename.open('w') as f:
        json.dump(rom_basis_dict, f, indent = 4)


    return 0






def get_number_of_singular_values_for_given_tolerance(M, N, s, epsilon):
    dimMATRIX = max(M,N)
    tol = dimMATRIX*np.finfo(float).eps*max(s)/2
    R = np.sum(s > tol)  # Definition of numerical rank
    if epsilon == 0:
        K = R
    else:
        SingVsq = np.multiply(s,s)
        SingVsq.sort()
        normEf2 = np.sqrt(np.cumsum(SingVsq))
        epsilon = epsilon*normEf2[-1] #relative tolerance
        T = (sum(normEf2<epsilon))
        K = len(s)-T
    K = min(R,K)
    return K






def tsqr_svd(ds_array,partitions, tol = 1e-6):

    M,N = ds_array.shape
    print('the shape of the ds array is: ',ds_array)
    Q, R = tsqr(ds_array, n_reduction = partitions, mode="reduced", indexes=None)
    print('the shape of the ds array is: ',Q)
    shape_for_rechunking = Q.shape[1]
    B = Q.T@ds_array
    B = B.collect()
    u_hat, s, _ = np.linalg.svd(B, full_matrices=False) #use dislib's SVD here????
    u_hat_dislib = ds.array(u_hat, block_size=(shape_for_rechunking,shape_for_rechunking))
    number_of_singular_values = get_number_of_singular_values_for_given_tolerance(M, N, s, tol)
    U = Q@u_hat_dislib
    U = U.collect()
    U = U[:,:number_of_singular_values]

    return U









def DivideInPartitions(NumTerms, NumTasks):
    Partitions = np.zeros(NumTasks+1,dtype=np.int)
    PartitionSize = int(NumTerms / NumTasks)
    Partitions[0] = 0
    Partitions[NumTasks] = NumTerms
    for i in range(1,NumTasks):
        Partitions[i] = Partitions[i-1] + PartitionSize
    return Partitions







def get_numpy_array(arr, global_ids):
    b_locks = arr[global_ids]
    blocks = b_locks._blocks
    if len(blocks) == 1:
        if len(blocks[0]) == 1:
            print("Only one block")
            return to_block([blocks[0][0]])
    print("More than one block")

    return to_block(blocks)







@constraint(computingUnits=argv[2])
@task(blocks={Type: COLLECTION_IN, Depth: 2}, returns = np.array)
def to_block(blocks):
    return np.block(blocks)








def Initialize_ECM_Lists(arr): # Generate initial list of ids and weights
    number_of_rows = arr.shape[0]
    global_ids = np.array(range(number_of_rows))
    global_weights = np.ones(len(global_ids))

    return global_ids, global_weights







@constraint(computingUnits=argv[2])
@task(returns=3)
def GetElementsOfPartition_Recursive(np_array, global_ids, global_weights, block_len, block_num, title, final_truncation = 1e-6):

    projected_residuals_matrix = np_array * global_weights[:, np.newaxis] #try making the weights and indexes ds arrays?

    if title == 'intermediate':
        u, _, _, _ = RandomizedSingularValueDecomposition().Calculate(projected_residuals_matrix) #randomized version with machine precision
        constrain_sum_of_weights = False # setting it to "True" worsens the approximation. Need to implement the orthogonal complement rather and not the row of 1's is implemented
    else:
        u, _, _, _ = RandomizedSingularValueDecomposition().Calculate(projected_residuals_matrix,final_truncation) #randomized version with user-defined tolerance
        constrain_sum_of_weights = False # setting it to "True" worsens the approximation. Need to implement the orthogonal complement rather and not the row of 1's is implemented

    ElementSelector = EmpiricalCubatureMethod()
    ElementSelector.SetUp( u, constrain_sum_of_weights)
    ElementSelector.Initialize()
    ElementSelector.Calculate()
    local_ids = np.squeeze(ElementSelector.z)
    weights = np.squeeze(ElementSelector.w)

    indexes_2 = np.argsort(local_ids) #this is necessary, since dislib cannot return un-ordered indexes

    return global_ids[local_ids[indexes_2]], local_ids[indexes_2]+block_len*block_num, weights[indexes_2]*global_weights[local_ids[indexes_2]]







def Parallel_ECM_Recursive(arr,block_len,global_ids,global_weights,final=False, final_truncation=1e-6):
    # arr is a dislib array where all chunks have length block_len. Contains the info for all the elements
    # that were selected in the last recursion
    # global_ids and global_weights are lists with the global values for all the elements in arr

    number_of_rows = arr.shape[0]

    if final:
        print('STARTED FINAL ECM')
        print('Chunks in dslibarray:', len(arr._blocks))
        ecm_mode='final'
        if len(arr._blocks)>1:
            print('Non single-chunk, rechunking.')
            arr=arr.rechunk(arr.shape)
        block_len=number_of_rows
    else:
        print('STARTED INTERMEDIATE ECM')
        print('Chunks in dslibarray:', len(arr._blocks))
        ecm_mode='intermediate'

    # Creating lists to store ids and weights
    ids_global_store = []
    ids_local_store= []
    weights_store = []

    for j in range(len(arr._blocks)):
        # We get the part of the global ids and weights corresponding to the elements in the chunk.
        chunk_global_ids = global_ids[list(range(block_len*j,min(block_len*(j+1),int(number_of_rows))))]
        chunk_global_weights = global_weights[list(range(block_len*j,min(block_len*(j+1),int(number_of_rows))))]
        # We run the ECM algorithm and get the list of chosen elements in both local and global notation, and their global weights
        #print( arr._blocks[j][0] ) #TODO Carefull! if you pass a chunk of zeroes, it explodes!!!
        ids,l_ids,w = GetElementsOfPartition_Recursive(arr._blocks[j][0],chunk_global_ids,chunk_global_weights,block_len,j,ecm_mode,final_truncation)
        ids_global_store.append(ids)
        ids_local_store.append(l_ids)
        weights_store.append(w)

    # Synchronize the ids and weights lists
    for i in range(len(ids_global_store)):
        if i==0:
            temp_global_ids = compss_wait_on(ids_global_store[i])
            temp_local_ids = compss_wait_on(ids_local_store[i])
            temp_global_weights = compss_wait_on(weights_store[i])
        else:
            temp_global_ids = np.r_[temp_global_ids,compss_wait_on(ids_global_store[i])]
            temp_local_ids = np.r_[temp_local_ids,compss_wait_on(ids_local_store[i])]
            temp_global_weights = np.r_[temp_global_weights,compss_wait_on(weights_store[i])]

    global_ids = temp_global_ids
    local_ids = temp_local_ids
    global_weights = temp_global_weights

    # We return the rows of the array corresponding to the chosen elements. Also the global ids and weights.
    # This dislib array will still have the the same chunk size, just with less chunks
    return arr[local_ids], global_ids, global_weights













def Stage0_GetDataForSimulations():
    working_path = argv[1]
    parameter_file_name = working_path + "/ProjectParameters_CoSimulation_workflow.json"
    data = compss_wait_on(GetSimulationsData(parameter_file_name))
    print(data)
    return data





def FOM(parameters, simulations_data):
    # set the ProjectParameters.json path
    working_path = argv[1]
    parameter_file_name = working_path + "/ProjectParameters_CoSimulation_workflow.json"
    # create a serialization of the model and of the project parameters
    pickled_parameters = SerializeModelParameters_Task(parameter_file_name)   #Can we launch the simulations without taking this into account??
    TotalNumberOFCases = len(parameters)

    #bouble_blocks = []
    blocks1 = []
    blocks2 = []
    solutions_at_control_point = []

    # start algorithm
    for instance in range (0,TotalNumberOFCases):
        b1, b2, solutions = ExecuteInstance_Task(pickled_parameters,parameters,instance,working_path)
        blocks1.append(b1)
        blocks2.append(b2)
        solutions_at_control_point.append(solutions)
        #pdb.set_trace()

    number_of_dofs = simulations_data[0]["number_of_dofs"]
    snapshots_per_simulation = simulations_data[0]["snapshots_per_simulation"]
    expected_shape = (number_of_dofs, TotalNumberOFCases*snapshots_per_simulation)  # We will know the size of the array!
    desired_block_size = simulations_data[0]["desired_block_size_svd_rom"]
    simulation_shape = (number_of_dofs, snapshots_per_simulation)

    #TODO cope with failing simulations
    ds_arrays1 = load_blocks_rechunk(blocks1, shape = expected_shape, block_size = simulation_shape, new_block_size = desired_block_size)

    number_of_dofs = simulations_data[1]["number_of_dofs"]
    snapshots_per_simulation = simulations_data[1]["snapshots_per_simulation"]
    expected_shape = (number_of_dofs, TotalNumberOFCases*snapshots_per_simulation)  # We will know the size of the array!
    desired_block_size = simulations_data[1]["desired_block_size_svd_rom"]
    simulation_shape = (number_of_dofs, snapshots_per_simulation)

    #TODO cope with failing simulations
    ds_arrays2 = load_blocks_rechunk(blocks2, shape = expected_shape, block_size = simulation_shape, new_block_size = desired_block_size)

    np.save(working_path+"/FOM_solutions_at_control_point", np.block(compss_wait_on(solutions_at_control_point)))

    return ds_arrays1, ds_arrays2







def Stage2_SVD(snapshots,simulations_data, mu, workflow_rom_parameters):

    for i in range(len(snapshots)):
        working_path = argv[1]
        name = simulations_data[i]["solver_name"]
        # """RSVD #OPTION 1"""
        # desired_rank = 10#simulations_data["number_of_modes"]
        # u,_ = rsvd(snapshots[i], desired_rank)

        """TSRQ SVD #OPTION 2"""
        partitions = workflow_rom_parameters[name]["ROM"]["number_of_partitions"].GetInt()
        tolerance = workflow_rom_parameters[name]["ROM"]["svd_truncation_tolerance"].GetDouble()
        u = tsqr_svd(snapshots[i],partitions, tolerance)

        """LANCZOS SVD #OPTION 3"""
        #DISLIB_ARRAY-COMPATIBLE VERSION OF LANCZOS


        conditions_list = workflow_rom_parameters[name]["HROM"]["include_conditions_model_parts_list"].GetStringArray()
        nodal_neighbours_list = workflow_rom_parameters[name]["HROM"]["include_nodal_neighbouring_elements_model_parts_list"].GetStringArray()

        finished = SavingRomParameters(working_path,u, name,conditions_list, nodal_neighbours_list)
        compss_wait_on(finished)

        #UPDATING SIMULATIONS DATA ACCORINDG TO NUMBER OF MODES OBTAINED
        snapshots_per_simulation = simulations_data[i]["snapshots_per_simulation"]
        simulations_data[i]["number_of_modes"] = int(u.shape[1])
        SIZE1, _ = simulations_data[i]["desired_block_size_svd_hrom"]
        #
        simulations_data[i]["desired_block_size_svd_hrom"] = SIZE1,int(simulations_data[i]["number_of_modes"]*len(mu)*snapshots_per_simulation)





def ROM(parameters, simulations_data, simulation_to_run):
    prepare_files_cosim(workflow_rom_parameters, simulation_to_run)

    if simulation_to_run=="RunHROM" or simulation_to_run=="HHROM":
        ChangeRomFlags(simulations_data, 'runHROMGalerkin')

    # set the ProjectParameters.json path
    working_path = argv[1]
    parameter_file_name = working_path + "/ProjectParameters_CoSimulation_workflow_ROM.json"


    # create a serialization of the model and of the project parameters
    pickled_parameters = SerializeModelParameters_Task(parameter_file_name)   #Can we launch the simulations without taking this into account?? Not doing any heavy lifting in CoSim
    TotalNumberOFCases = len(parameters)


    #bouble_blocks = []
    blocks1 = []
    blocks2 = []
    solutions_at_control_point = []

    # start algorithm
    for instance in range (0,TotalNumberOFCases):
        b1, b2, solutions = ExecuteInstance_Task(pickled_parameters,parameters,instance,working_path)
        blocks1.append(b1)
        blocks2.append(b2)
        solutions_at_control_point.append(solutions)
        #if simulation_to_run =="RunHROM":
            #pdb.set_trace()


    number_of_dofs = simulations_data[0]["number_of_dofs"]
    snapshots_per_simulation = simulations_data[0]["snapshots_per_simulation"]
    expected_shape = (number_of_dofs, TotalNumberOFCases*snapshots_per_simulation)  # We will know the size of the array!
    desired_block_size = simulations_data[0]["desired_block_size_svd_rom"]
    simulation_shape = (number_of_dofs, snapshots_per_simulation)



    #TODO cope with failing simulations
    ds_arrays1 = load_blocks_rechunk(blocks1, shape = expected_shape, block_size = simulation_shape, new_block_size = desired_block_size)

    number_of_dofs = simulations_data[1]["number_of_dofs"]
    snapshots_per_simulation = simulations_data[1]["snapshots_per_simulation"]
    expected_shape = (number_of_dofs, TotalNumberOFCases*snapshots_per_simulation)  # We will know the size of the array!
    desired_block_size = simulations_data[1]["desired_block_size_svd_rom"]
    simulation_shape = (number_of_dofs, snapshots_per_simulation)

    #TODO cope with failing simulations
    ds_arrays2 = load_blocks_rechunk(blocks2, shape = expected_shape, block_size = simulation_shape, new_block_size = desired_block_size)

    np.save(working_path+f"/{simulation_to_run}_solutions_at_control_point", np.block(compss_wait_on(solutions_at_control_point)))

    return ds_arrays1, ds_arrays2








def Stage4_TrainHROM(parameters, simulations_data,workflow_rom_parameters):
    ChangeRomFlags(simulations_data,"trainHROMGalerkin")
    prepare_files_cosim(workflow_rom_parameters, "trainHROM")
    # set the ProjectParameters.json path
    working_path = argv[1]

    parameter_file_name = working_path + "/ProjectParameters_CoSimulation_workflow_ROM.json"

    # create a serialization of the model and of the project parameters
    pickled_parameters = SerializeModelParameters_Task(parameter_file_name)   #Can we launch the simulations without taking this into account??
    TotalNumberOFCases = len(parameters)

    #bouble_blocks = []
    blocks1 = []
    blocks2 = []


    # start algorithm
    for instance in range (0,TotalNumberOFCases):
        b1, b2 = ExecuteInstance_Task_TrainHROM_workflow(pickled_parameters,parameters,instance,working_path) #TODO I am going to set up a second one. Would it be better to use the same class for all, just passing a flag?
        blocks1.append(b1)
        blocks2.append(b2)


    blocks = [blocks1,blocks2]

    for i in range(len(blocks)):
        number_of_modes = simulations_data[i]["number_of_modes"] # I added a 1 here to refer to the outside modelpart
        number_of_elements = simulations_data[i]["number_of_elements"]
        number_of_conditions = simulations_data[i]["number_of_conditions"]
        snapshots_per_simulation = simulations_data[i]["snapshots_per_simulation"]
        expected_shape = (number_of_elements+number_of_conditions, number_of_modes*TotalNumberOFCases*snapshots_per_simulation) #We will know the size of the array!
        desired_block_size = simulations_data[i]["desired_block_size_svd_hrom"]
        simulation_shape = (number_of_elements+number_of_conditions, number_of_modes*snapshots_per_simulation)
        #TODO cope with failing simulations


        # Put blocks into a dslib array with desired number of chunks (all with same size, except the last one that might be smaller)
        NumberOfPartitions =  workflow_rom_parameters[simulations_data[i]["solver_name"]]["HROM"]["number_of_partitions"].GetInt()
        desired_block_size = (int(np.ceil(expected_shape[0]/NumberOfPartitions)),expected_shape[1])
        arr = load_blocks_rechunk(blocks[i], shape = expected_shape, block_size = simulation_shape, new_block_size = desired_block_size)


        type_of_ecm = workflow_rom_parameters[simulations_data[i]["solver_name"]]["HROM"]["empirical_cubature_type"].GetString()


        if type_of_ecm == "partitioned":
            ###Partitioned ECM:
            # Run ECM in recursion, with given tolerance in the final iteration.
            ecm_iterations = 2 # This should be obtained form the simulation parameters
            z,w = Initialize_ECM_Lists(arr)
            for j in range(ecm_iterations):
                if j < ecm_iterations-1:
                    arr,z,w = Parallel_ECM_Recursive(arr,desired_block_size[0],z,w)
                    print('dslibarray shape:', arr.shape)
                    print('Chunks in dslibarray:', len(arr._blocks))
                    print('Global_ids shape:', len(z))
                else:
                    _,z,w = Parallel_ECM_Recursive(arr,desired_block_size[0],z,w,final=True,
                final_truncation = workflow_rom_parameters[simulations_data[i]["solver_name"]]["HROM"]["element_selection_svd_truncation_tolerance"].GetDouble())
                    print('Global_ids shape:', len(z))

        elif type_of_ecm == "monolithic":
            ###Monolithic ECM:

            #TSRQ SVD
            tolerance = workflow_rom_parameters[simulations_data[i]["solver_name"]]["HROM"]["element_selection_svd_truncation_tolerance"].GetDouble()
            u = tsqr_svd(arr,NumberOfPartitions, tolerance)
            ElementSelector = EmpiricalCubatureMethod()
            ElementSelector.SetUp( u, False)
            ElementSelector.Initialize()
            ElementSelector.Calculate()
            z = np.squeeze(ElementSelector.z)
            w = np.squeeze(ElementSelector.w)


        ###################################################################

        finished = SavingElementsAndWeights(working_path+'/'+ simulations_data[i]["solver_name"]+'/',number_of_elements,z,w)
        compss_wait_on(finished)









def StageFinal_CreateHROMModelParts(simulations_data,workflow_rom_parameters):
    working_path = argv[1]
    parameter_file_name = working_path + "/ProjectParameters_CoSimulation_workflow_ROM.json"
    ChangeRomFlags(simulations_data,"trainHROMGalerkin")
    prepare_files_cosim(workflow_rom_parameters, "trainHROM")
    data = compss_wait_on(ComputeHROMModelParts(parameter_file_name))
    return data











def compare_FOM_vs_ROM(SnapshotsMatrixROM, SnapshotsMatrix):
    #using the Frobenious norm of the snapshots of the solution
    original_norm= np.linalg.norm((SnapshotsMatrix.norm().collect()))
    intermediate = ds.data.matsubtract(SnapshotsMatrixROM,SnapshotsMatrix) #(available on latest release)
    intermediate = np.linalg.norm((intermediate.norm().collect()))
    final = intermediate/original_norm
    print('error is of:', final)
    # np.save('relative_error_rom.npy', final)
















def compare_ROM_vs_HROM(SnapshotsMatrixROM, SnapshotsMatrixHROM):
    #using the Frobenious norm of the snapshots of the solution
    original_norm= np.linalg.norm((SnapshotsMatrixROM.norm().collect()))
    intermediate = ds.data.matsubtract(SnapshotsMatrixROM,SnapshotsMatrixHROM) #(available on latest release)
    intermediate = np.linalg.norm((intermediate.norm().collect()))
    final = intermediate/original_norm
    print('error is of:', final)
    #np.save('relative_error_hrom.npy', final)













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
        file_input_name = updated_project_parameters["solver_settings"]["model_import_settings"]["input_filename"]
        materials_filename = updated_project_parameters["solver_settings"]["material_import_settings"]["materials_filename"]
        working_path = argv[1]
        updated_project_parameters["output_processes"]["rom_output"] = [get_rom_output_defaults()]
        updated_project_parameters["output_processes"]["rom_output"][0]["Parameters"]["model_part_name"] = workflow_rom_parameters[solver]["ROM"]["model_part_name"].GetString()
        updated_project_parameters["output_processes"]["rom_output"][0]["Parameters"]["nodal_unknowns"] = workflow_rom_parameters[solver]["ROM"]["nodal_unknowns"].GetStringArray()
        updated_project_parameters["output_processes"]["rom_output"][0]["Parameters"]["rom_basis_output_folder"] = working_path+ '/' + solver
        if simulation_to_run=="FOM":
            # if solver=="fluid":
            #     updated_project_parameters["processes"]["constraints_process_list"][3]["Parameters"]["origin_model_part_file_name"] = working_path + '/velocity_field'
            updated_project_parameters["solver_settings"]["model_import_settings"]["input_filename"] = working_path + '/'+ file_input_name
            updated_project_parameters["solver_settings"]["material_import_settings"]["materials_filename"] = working_path +'/'+ materials_filename
            with open(f'{physics_project_parameters_name}_workflow.json','w') as f:
                json.dump(updated_project_parameters, f, indent = 4)
        else:
            if simulation_to_run=="trainHROM":
                updated_project_parameters["output_processes"]["rom_output"][0]["Parameters"]["snapshots_interval"] = 1e6

            if simulation_to_run=="HHROM":
                updated_project_parameters["solver_settings"]["model_import_settings"]["input_filename"] = file_input_name+"HROM"
            with open(f'{physics_project_parameters_name}.json','w') as f:
                json.dump(updated_project_parameters, f, indent = 4)















def prepare_files_cosim(workflow_rom_parameters, simulation_to_run):
    """pre-pending the absolut path of the files in the Project Parameters"""

    if simulation_to_run == "FOM":
        with open('ProjectParameters_CoSimulation.json','r') as f:
            working_path = argv[1]
            updated_project_parameters = json.load(f)
            solver_keys = updated_project_parameters["solver_settings"]["solvers"].keys()
            for solver in solver_keys:
                file_input_name = updated_project_parameters["solver_settings"]["solvers"][solver]["solver_wrapper_settings"]["input_file"]
                prepare_files_physical_problem(file_input_name, solver, simulation_to_run, workflow_rom_parameters)
                updated_project_parameters["solver_settings"]["solvers"][solver]["solver_wrapper_settings"]["input_file"] = working_path + '/'+ file_input_name + '_workflow'

        with open('ProjectParameters_CoSimulation_workflow.json','w') as f:
            json.dump(updated_project_parameters, f, indent = 4)

    else:
        with open('ProjectParameters_CoSimulation_workflow.json','r') as f:
            working_path = argv[1]
            updated_project_parameters = json.load(f)
            solver_keys = updated_project_parameters["solver_settings"]["solvers"].keys()
            for solver in solver_keys:
                file_input_name = updated_project_parameters["solver_settings"]["solvers"][solver]["solver_wrapper_settings"]["input_file"]
                prepare_files_physical_problem(file_input_name, solver, simulation_to_run, workflow_rom_parameters)
                updated_project_parameters["solver_settings"]["solvers"][solver]["type"] = 'solver_wrappers.kratos.rom_wrapper'

        if simulation_to_run == "ROM":
            with open('ProjectParameters_CoSimulation_workflow_ROM.json','w') as f:
                json.dump(updated_project_parameters, f, indent = 4)















def ChangeRomFlags(simulations_data, simulation_to_run = 'trainHROMGalerkin'):
    folders = [simulations_data[0]["solver_name"], simulations_data[1]["solver_name"]]
    for folder in folders:
        parameters_file_name = f'{folder}/RomParameters.json'
        with open(parameters_file_name, 'r+') as parameter_file:
            f=json.load(parameter_file)
            f['assembling_strategy'] = 'global'
            if simulation_to_run=='GalerkinROM':
                f['projection_strategy']="galerkin"
                f['train_hrom']=False
                f['run_hrom']=False
            elif simulation_to_run=='trainHROMGalerkin':
                f['train_hrom']=True
                f['run_hrom']=False
            elif simulation_to_run=='runHROMGalerkin':
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









def SerialTest(single_case, list_of_simulations_to_launch_in_serial):
    #this function is hardcoded
    workflow_rom_parameters = GetWorkflowROMParameters()
    for case in list_of_simulations_to_launch_in_serial:
        if case=="FOM":
            prepare_files_cosim(workflow_rom_parameters, simulation_to_run="FOM")
            parameter_file_name =  "ProjectParameters_CoSimulation_workflow.json"
            add_vtk_output_to_project_parameters(case)
        if case=="ROM":
            prepare_files_cosim(workflow_rom_parameters, simulation_to_run="ROM")
            parameter_file_name =  "ProjectParameters_CoSimulation_workflow_ROM.json"
            add_vtk_output_to_project_parameters(case)
        if case=="HROM":
            prepare_files_cosim(workflow_rom_parameters, simulation_to_run="RunHROM")
            parameter_file_name =  "ProjectParameters_CoSimulation_workflow_ROM.json"
            add_vtk_output_to_project_parameters(case)
        if case=="HHROM":
            prepare_files_cosim(workflow_rom_parameters, simulation_to_run="HHROM")
            parameter_file_name =  "ProjectParameters_CoSimulation_workflow_ROM.json"
            add_vtk_output_to_project_parameters(case)


        with open(parameter_file_name, 'r') as parameter_file:
            cosim_parameters = KratosMultiphysics.Parameters(parameter_file.read())
        simulation = TrainROM(cosim_parameters, single_case, argv[1])
        simulation.Run()




def get_multiple_params(number_of_params_1, number_of_params_2):

    param1 =  np.random.uniform(10000, 30000, size=number_of_params_1)  # HeatFlux in the solid part
    param2 =  np.random.uniform(200, 1500, size=number_of_params_2)  # Rotation velocity field (this should coincide with the exiting files, or we should be able to interpolate and create the required files)

    #pdb.set_trace()

    mu = []
    for i in range(number_of_params_1):
        for j in range(number_of_params_2):
                mu.append([param1[i],param2[j]])

    from matplotlib import pyplot as plt
    # Create a 3D plot
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')

    # Plot the points
    for i in range(len(mu)):
        ax.scatter(mu[i][0],mu[i][1], c='b', marker='o')

    # Set labels for the axes
    ax.set_xlabel(r'heat flux')
    ax.set_ylabel(r'RPMs')

    # Show the plot
    plt.savefig('sampling_of_parametrix_space.png')

    return mu





if __name__ == '__main__':

    #mu = get_multiple_params(10, 10) #we might need to use a function like this for sampling the parameters space, for now, input by hand
    mu = [
    [50000, 200],         # 200 RPM, 5000 W/m²
    [62500, 250],         # 250 RPM, 62500 W/m²
    [75000, 300],         # 300 RPM, 75000 W/m²
    [87500, 350],         # 350 RPM, 87500 W/m²
    [100000, 400],        # 400 RPM, 100000 W/m²
    [112500, 450],        # 450 RPM, 112500 W/m²
    [125000, 500]         # 500 RPM, 125000 W/m²
    ]


    # Get the analysis directory path from the command line argument
    analysis_directory_path = argv[1]

    # Define the RPM values for which we want to interpolate
    interpolated_rpms = [250, 350, 450] # These are the RPMs that are not part of the CFD precomputed simulations.

    # Call the interpolate_parameters function to perform non-intrusive interpolation
    # for the defined RPM values using the given analysis directory
    interpolate_parameters(analysis_directory_path, interpolated_rpms)

    #      flux   RPMs
    """
    We define the parameters for the simulation.
    In this cas:qe a single parameter is defined.

    More parameters are possible.

    """

    workflow_rom_parameters = GetWorkflowROMParameters()
    prepare_files_cosim(workflow_rom_parameters, simulation_to_run="FOM")
    # Elsewhere, I was able to retrieve which solver was being used, but
    # here I should directly specify to which solver each ROM and HROM properties refer
    # is it robut enough?



    """
    Absolute paths should be used in the ProjectParameters
    and Materials files for running in a cluster
    """



    simulations_data = Stage0_GetDataForSimulations()
    """
    Stage 0
    - The shape of the expected matrices is obtained to allow paralelization
    """


    SnapshotsMatrix1, SnapshotsMatrix2 = FOM(mu, simulations_data)
    """
    Stage 1
    - launches in parallel a Full Order Model (FOM) simulation for each simulation parameter.
    - returns a distributed array (ds-array) with the results of the simulations.
    """

    #pdb.set_trace()

    Stage2_SVD([SnapshotsMatrix1, SnapshotsMatrix2],simulations_data, mu, workflow_rom_parameters)
    """
    Stage 2
    - computes the "fixed rank" randomized SVD in parallel using the dislib library
    - stores the ROM basis in JSON format #TODO improve format
    """
    compss_barrier()


    SnapshotsMatrix1ROM, SnapshotsMatrix2ROM = ROM(mu, simulations_data, simulation_to_run="ROM")
    """
    Stage 3
    - launches the Reduced Order Model simulations for the same simulation parameters used for the FOM
    - stores the results in a distributed array
    """

    compare_FOM_vs_ROM(SnapshotsMatrix1, SnapshotsMatrix1ROM)
    compare_FOM_vs_ROM(SnapshotsMatrix2, SnapshotsMatrix2ROM)
    """
    - Computes the Frobenius norm of the difference of Snapshots FOM and ROM
    - TODO add more parameters in a smart way if norm is above a given threshold
    """


    compss_barrier()
    Stage4_TrainHROM(mu, simulations_data, workflow_rom_parameters)
    """
    Stage 4
    - Launches the same ROM simulation and builds the projected residual in distributed array
    - Analyses the matrix of projected residuals and obtains the elements and weights
    """
    compss_barrier()
    SnapshotsMatrix1HROM, SnapshotsMatrix2HROM  = ROM(mu,simulations_data, simulation_to_run='RunHROM')
    """
    Stage 5
    - launches the Hyper Reduced Order Model simulations for the same simulation parameters used for the FOM and ROM
    - stores the results in a distributed array
    """

    ###
    print('fom vs rom')
    compare_FOM_vs_ROM(SnapshotsMatrix1, SnapshotsMatrix1ROM)
    compare_FOM_vs_ROM(SnapshotsMatrix2, SnapshotsMatrix2ROM)
    """
    - Computes the Frobenius norm of the difference of Snapshots FOM and ROM
    - TODO add more parameters in a smart way if norm is above a given threshold
    """
    print('\nrom vs hrom')
    ###

    compare_ROM_vs_HROM(SnapshotsMatrix1ROM, SnapshotsMatrix1HROM)
    compare_ROM_vs_HROM(SnapshotsMatrix2ROM, SnapshotsMatrix2HROM)


    """
    - Computes the Frobenius norm of the difference of Snapshots ROM and HROM
    - TODO add more parameters in a smart way if norm is above a given threshold
    """


    #This final part can be considered as the first step in the deployment stage
    StageFinal_CreateHROMModelParts(simulations_data,workflow_rom_parameters)
    #compss_barrier()
    #_,_, = ROM(mu, simulations_data, "HHROM")



    #SerialTest(mu[0], ["FOM", "ROM", "HROM","HHROM"]) #This should launch a single scenario of the parameters and store the results in vtk format for comparison
