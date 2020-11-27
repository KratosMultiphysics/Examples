import os
import sys
import time
import json
#Kratos Imports
import KratosMultiphysics
import KratosMultiphysics.mpi as KratosMPI
import KratosMultiphysics.FluidDynamicsApplication as KratosFluidDynamics
import KratosMultiphysics.MeshingApplication as KratosMeshing
import KratosMultiphysics.MappingApplication as KratosMapping
pickle_message = ""
try:
    import cPickle as pickle
    have_pickle_module = True
except ImportError:
    if sys.version_info > (3, 0):
        try:
            import pickle
            have_pickle_module = True
        except ImportError:
            have_pickle_module = False
            pickle_message = "No pickle module found"
    else:
        have_pickle_module = False
        pickle_message = "No valid pickle module found"

#Kratos Fluid Dynamic Analysis Imports
from FluidDynamicsAnalysisWithMetrics import FluidDynamicsAnalysisWithMetrics as FluidDynamicsAnalysis

with open("ProjectParameters.json",'r') as parameter_file:
    parameters = KratosMultiphysics.Parameters(parameter_file.read())

with open("RemeshingParameters.json",'r') as parameter_file:
    remeshing_parameters = KratosMultiphysics.Parameters(parameter_file.read())

iterations = remeshing_parameters["number_of_iterations"].GetInt()

if remeshing_parameters["start_time_control_value"].GetDouble()>parameters["problem_data"]["end_time"].GetDouble():
    remeshing_parameters["start_time_control_value"].SetDouble(parameters["problem_data"]["end_time"].GetDouble()/2.0)
    KratosMultiphysics.Logger.PrintWarning("Start time to compute the metric is greater than end_time, it has been overwritten to start_time=end_time/2")
statistics_parameters = parameters["processes"]["auxiliar_process_list"][1]["Parameters"]
if statistics_parameters["statistics_start_point_control_value"].GetDouble()>parameters["problem_data"]["end_time"].GetDouble():
    statistics_parameters["statistics_start_point_control_value"].SetDouble(parameters["problem_data"]["end_time"].GetDouble()/2.0)
    KratosMultiphysics.Logger.PrintWarning("Start time to compute the average is greater than end_time, it has been overwritten to start_time=end_time/2")

# Reading some parameters to set-up the output files.
communicator = KratosMultiphysics.DataCommunicator.GetDefault()
rank = communicator.Rank()
size = communicator.Size()
step=1
metric_parameters = remeshing_parameters["metric_parameters"]
endtime = parameters["problem_data"]["end_time"].GetDouble()
ierr = metric_parameters["hessian_strategy_parameters"]["interpolation_error"].GetDouble()
gid_path = 'gid_output_'+str(size)+"_ierr_"+str(ierr)+"_endtime_"+str(endtime)+"_step_"+str(step)
output_name=parameters["output_processes"]["gid_output"][0]["Parameters"]["output_name"].GetString()
parameters["output_processes"]["gid_output"][0]["Parameters"]["output_name"].SetString(gid_path+"/"+output_name+"_initial")
drag_name=parameters["processes"]["auxiliar_process_list"][0]["Parameters"]["output_file_settings"]["file_name"].GetString()
parameters["processes"]["auxiliar_process_list"][0]["Parameters"]["output_file_settings"]["file_name"].SetString(drag_name+"_initial")
parameters["processes"]["auxiliar_process_list"][0]["Parameters"]["output_file_settings"]["output_path"].SetString(gid_path)
# Solving
model = KratosMultiphysics.Model()
simulation = FluidDynamicsAnalysis(model, parameters, remeshing_parameters)
simulation.Run()

main_model_part = simulation._GetSolver().main_model_part

for step in range(1,iterations+1):
    # Creating auxiliar paths to store the gid_outputs
    gid_path = 'gid_output_'+str(size)+"_ierr_"+str(ierr)+"_endtime_"+str(endtime)+"_step_"+str(step)
    if rank == 0:
        if not os.path.exists(gid_path):
            os.makedirs(gid_path)
    communicator.Barrier()
    KratosMultiphysics.Logger.PrintInfo("STEP: ", step)

    if remeshing_parameters["perform_mapping_between_steps"].GetBool():
        serialized_model = KratosMultiphysics.MpiSerializer()
        serialized_model.Save("ModelSerialization", model)

    # Perform parmmg remeshing.
    parmmg_parameters = remeshing_parameters["parmmg_parameters"]
    pmmg_process = KratosMeshing.ParMmgProcess3D(main_model_part, parmmg_parameters)
    pmmg_process.Execute()


    if remeshing_parameters["perform_mapping_between_steps"].GetBool():
        deserialized_initial_model = KratosMultiphysics.Model()
        serialized_model.Load("ModelSerialization", deserialized_initial_model)
        initial_main_model_part = deserialized_initial_model.GetModelPart("FluidModelPart").GetRootModelPart()
        ParallelFillCommunicator = KratosMPI.ParallelFillCommunicator(initial_main_model_part)
        ParallelFillCommunicator.Execute()

        ini_time = time.time()
        # creating a mapper for distributed memory
        mpi_mapper = KratosMapping.MapperFactory.CreateMPIMapper(
            initial_main_model_part,
            main_model_part,
            remeshing_parameters["mapping_parameters"])
        mpi_mapper.Map(KratosMultiphysics.VELOCITY, KratosMultiphysics.VELOCITY)
        mpi_mapper.Map(KratosMultiphysics.PRESSURE, KratosMultiphysics.PRESSURE)

        main_model_part.GetCommunicator().SynchronizeVariable(KratosMultiphysics.VELOCITY)
        main_model_part.GetCommunicator().SynchronizeVariable(KratosMultiphysics.PRESSURE)
        time_elapsed = time.time() - ini_time
        KratosMultiphysics.Logger.PrintInfo("Time spent mapping: ", main_model_part.GetCommunicator().GetDataCommunicator().MaxAll(time_elapsed))

    # Preparing model_part to restart
    main_model_part.RemoveSubModelPart("fluid_computational_model_part")
    main_model_part.ProcessInfo[KratosMultiphysics.TIME] = 0.0
    main_model_part.ProcessInfo[KratosMultiphysics.STEP] = 0

    # Reading again parameters
    with open("ProjectParameters.json",'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())
    with open("RemeshingParameters.json",'r') as parameter_file:
        remeshing_parameters = KratosMultiphysics.Parameters(parameter_file.read())

    if remeshing_parameters["start_time_control_value"].GetDouble()>parameters["problem_data"]["end_time"].GetDouble():
        remeshing_parameters["start_time_control_value"].SetDouble(parameters["problem_data"]["end_time"].GetDouble()/2.0)
        KratosMultiphysics.Logger.PrintWarning("Start time to compute the metric is greater than end_time, it has been overwritten to start_time=end_time/2")
    statistics_parameters = parameters["processes"]["auxiliar_process_list"][1]["Parameters"]
    if statistics_parameters["statistics_start_point_control_value"].GetDouble()>parameters["problem_data"]["end_time"].GetDouble():
        statistics_parameters["statistics_start_point_control_value"].SetDouble(parameters["problem_data"]["end_time"].GetDouble()/2.0)
        KratosMultiphysics.Logger.PrintWarning("Start time to compute the average is greater than end_time, it has been overwritten to start_time=end_time/2")

    # Preparing settings to run an already loaded model
    parameters["solver_settings"]["model_import_settings"]["input_type"].SetString("use_input_model_part")
    output_name=parameters["output_processes"]["gid_output"][0]["Parameters"]["output_name"].GetString()
    parameters["output_processes"]["gid_output"][0]["Parameters"]["output_name"].SetString(gid_path+"/"+output_name)
    parameters["processes"]["auxiliar_process_list"][0]["Parameters"]["output_file_settings"]["output_path"].SetString(gid_path)
    simulation = FluidDynamicsAnalysis(model, parameters, remeshing_parameters)
    simulation.Run()

