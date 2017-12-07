from __future__ import print_function, absolute_import, division  # makes KratosMultiphysics backward compatible with python 2.6 and 2.7

from KratosMultiphysics import *
from KratosMultiphysics.FluidDynamicsApplication import *
from KratosMultiphysics.MeshingApplication import *
from KratosMultiphysics.ExternalSolversApplication import *

import os
import process_factory

parameter_file = open("ProjectParameters.json",'r')
ProjectParameters = Parameters( parameter_file.read())

main_model_part = ModelPart(ProjectParameters["problem_data"]["model_part_name"].GetString())
main_model_part.ProcessInfo.SetValue(DOMAIN_SIZE, ProjectParameters["problem_data"]["domain_size"].GetInt())

Model = {ProjectParameters["problem_data"]["model_part_name"].GetString(): main_model_part}

problem_type = ProjectParameters["problem_data"]["problem_type"].GetString() 

solve_problem = ProjectParameters["problem_data"]["solve_problem"].GetBool()

## Solver construction
import python_solvers_wrapper_fluid as fluid_wrapper
solver = fluid_wrapper.CreateSolver(main_model_part, ProjectParameters)

# Add variables (always before importing the model part) (it must be integrated in the ImportModelPart)
# If we integrate it in the model part we cannot use combined solvers
solver.AddVariables()

main_model_part.AddNodalSolutionStepVariable(NODAL_H) 
main_model_part.AddNodalSolutionStepVariable(NODAL_AREA)

# Read model_part (note: the buffer_size is set here) (restart can be read here)
solver.ImportModelPart()

# Add dofs (always after importing the model part) (it must be integrated in the ImportModelPart)
# If we integrate it in the model part we cannot use combined solvers
solver.AddDofs()

# ### Output settings start ####
problem_path = os.getcwd()
problem_name = ProjectParameters["problem_data"]["problem_name"].GetString()

# ### Output settings start ####
output_post = ProjectParameters.Has("output_configuration")
if (output_post == True):
    from gid_output_process import GiDOutputProcess
    output_settings = ProjectParameters["output_configuration"]
    gid_output = GiDOutputProcess(solver.GetComputingModelPart(),
                                        problem_name,
                                        output_settings)
    gid_output.ExecuteInitialize()
    
# Sets strategies, builders, linear solvers, schemes and solving info, and fills the buffer
solver.Initialize()

# Build sub_model_parts or submeshes (rearrange parts for the application of custom processes)
# #Get the list of the submodel part in the object Model
for i in range(ProjectParameters["solver_settings"]["skin_parts"].size()):
    skin_part_name = ProjectParameters["solver_settings"]["skin_parts"][i].GetString()
    Model.update({skin_part_name: main_model_part.GetSubModelPart(skin_part_name)})

## Get the list of the initial conditions submodel parts in the object Model
for i in range(ProjectParameters["initial_conditions_process_list"].size()):
    initial_cond_part_name = ProjectParameters["initial_conditions_process_list"][i]["Parameters"]["model_part_name"].GetString()
    Model.update({initial_cond_part_name: main_model_part.GetSubModelPart(initial_cond_part_name)})

## Get the gravity submodel part in the object Model
for i in range(ProjectParameters["gravity"].size()):
    gravity_part_name = ProjectParameters["gravity"][i]["Parameters"]["model_part_name"].GetString()
    Model.update({gravity_part_name: main_model_part.GetSubModelPart(gravity_part_name)})

## Remeshing processes construction
if (ProjectParameters.Has("initial_remeshing_process") == True):
    remeshing_processes = process_factory.KratosProcessFactory(Model).ConstructListOfProcesses(ProjectParameters["initial_remeshing_process"])
    if (ProjectParameters.Has("list_other_processes") == True):
        remeshing_processes += process_factory.KratosProcessFactory(Model).ConstructListOfProcesses(ProjectParameters["list_other_processes"])
    
    ## Remeshing processes initialization
    print("STARTING ADAPTATIVE LOOP")
    if (ProjectParameters.Has("adaptative_loop") == True):
        adaptative_loop = ProjectParameters["adaptative_loop"].GetInt()
    else:
        adaptative_loop = 1
    for n in range(adaptative_loop):
        print("ADAPTATIVE INTERATION: ", n + 1)
        for process in reversed(remeshing_processes):
            process.ExecuteInitialize()

# Obtain the list of the processes to be applied
list_of_processes = process_factory.KratosProcessFactory(Model).ConstructListOfProcesses( ProjectParameters["gravity"] )
list_of_processes += process_factory.KratosProcessFactory(Model).ConstructListOfProcesses( ProjectParameters["initial_conditions_process_list"] )
list_of_processes += process_factory.KratosProcessFactory(Model).ConstructListOfProcesses( ProjectParameters["boundary_conditions_process_list"] )
if (ProjectParameters.Has("list_other_processes") == True):
    list_of_processes += process_factory.KratosProcessFactory(Model).ConstructListOfProcesses(ProjectParameters["list_other_processes"])
if (ProjectParameters.Has("json_check_process") == True):
    list_of_processes += process_factory.KratosProcessFactory(Model).ConstructListOfProcesses(ProjectParameters["json_check_process"])
if (ProjectParameters.Has("json_output_process") == True):
    list_of_processes += process_factory.KratosProcessFactory(Model).ConstructListOfProcesses(ProjectParameters["json_output_process"])
if (ProjectParameters.Has("compare_two_files_check_process") == True):
    list_of_processes += process_factory.KratosProcessFactory(Model).ConstructListOfProcesses(ProjectParameters["compare_two_files_check_process"])
if (ProjectParameters.Has("recursive_remeshing_process") == True):
    list_of_processes += process_factory.KratosProcessFactory(Model).ConstructListOfProcesses(ProjectParameters["recursive_remeshing_process"])

for process in list_of_processes:
    process.ExecuteInitialize()

# ### START SOLUTION ####

computing_model_part = solver.GetComputingModelPart()

if (output_post == True):
    gid_output.ExecuteBeforeSolutionLoop()

if solve_problem == True:
    for process in list_of_processes:
        process.ExecuteBeforeSolutionLoop()
    
    # #Stepping and time settings (get from process info or solving info)
    # Delta time
    delta_time = ProjectParameters["problem_data"]["time_step"].GetDouble()
    # Start step
    main_model_part.ProcessInfo[TIME_STEPS] = 0
    # Start time
    time = ProjectParameters["problem_data"]["start_time"].GetDouble()
    # End time
    end_time = ProjectParameters["problem_data"]["end_time"].GetDouble()
    step = 0
    init_step = 3

    # Solving the problem (time integration)
    while(time <= end_time):
        time = time + delta_time
        main_model_part.ProcessInfo[TIME_STEPS] += 1
        main_model_part.CloneTimeStep(time)
        step = step + 1
        print("Time: ", time, " Step: ", step)
        
        if(step >= init_step):
            for process in list_of_processes:
                process.ExecuteInitializeSolutionStep()
                
            if (main_model_part.Is(MODIFIED) == True):
                # WE INITIALIZE THE SOLVER
                solver.Initialize()
                # WE RECOMPUTE THE PROCESSES AGAIN
                ## Processes initialization
                for process in list_of_processes:
                    process.ExecuteInitialize()
                ## Processes before the loop
                for process in list_of_processes:
                    process.ExecuteBeforeSolutionLoop()
                ## Processes of initialize the solution step
                for process in list_of_processes:
                    process.ExecuteInitializeSolutionStep()
                
            if (output_post == True):
                gid_output.ExecuteInitializeSolutionStep()
                        
            solver.Clear()
            solver.Solve()
            
            if (output_post == True):
                gid_output.ExecuteFinalizeSolutionStep()

            for process in list_of_processes:
                process.ExecuteFinalizeSolutionStep()

            for process in list_of_processes:
                process.ExecuteBeforeOutputStep()

            if (output_post == True):
                if gid_output.IsOutputStep():
                    gid_output.PrintOutput()
                    
            for process in list_of_processes:
                process.ExecuteAfterOutputStep()

    if (output_post == True):
        gid_output.ExecuteFinalize()

    for process in list_of_processes:
        process.ExecuteFinalize()
