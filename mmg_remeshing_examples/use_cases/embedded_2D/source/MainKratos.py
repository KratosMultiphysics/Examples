from __future__ import print_function, absolute_import, division #makes KratosMultiphysics backward compatible with python 2.6 and 2.7

from KratosMultiphysics import *
from KratosMultiphysics.MeshingApplication import *
from KratosMultiphysics.FluidDynamicsApplication import *
from KratosMultiphysics.ExternalSolversApplication import *

######################################################################################
######################################################################################
######################################################################################

## Parse the ProjectParameters
parameter_file = open("ProjectParameters.json",'r')
ProjectParameters = Parameters( parameter_file.read())

## Get echo level and parallel type
echo_level = ProjectParameters["problem_data"]["echo_level"].GetInt()
parallel_type = ProjectParameters["problem_data"]["parallel_type"].GetString()

## Import KratosMPI if needed
if (parallel_type == "MPI"):
    from KratosMultiphysics.mpi import *
    from KratosMultiphysics.MetisApplication import *
    from KratosMultiphysics.TrilinosApplication import *

## Fluid model part definition
main_model_part = ModelPart(ProjectParameters["problem_data"]["model_part_name"].GetString())
main_model_part.ProcessInfo.SetValue(DOMAIN_SIZE, ProjectParameters["problem_data"]["domain_size"].GetInt())

## Solver construction
import python_solvers_wrapper_fluid
solver = python_solvers_wrapper_fluid.CreateSolver(main_model_part, ProjectParameters)

solver.AddVariables()

## Read the model - note that SetBufferSize is done here
solver.ImportModelPart()

## Add AddDofs
solver.AddDofs()

## Initialize GiD  I/O
output_post  = ProjectParameters.Has("output_configuration")
if (output_post == True):
    if (parallel_type == "OpenMP"):
        from gid_output_process import GiDOutputProcess
        gid_output = GiDOutputProcess(solver.GetComputingModelPart(),
                                      ProjectParameters["problem_data"]["problem_name"].GetString() ,
                                      ProjectParameters["output_configuration"])
    elif (parallel_type == "MPI"):
        from gid_output_process_mpi import GiDOutputProcessMPI
        gid_output = GiDOutputProcessMPI(solver.GetComputingModelPart(),
                                         ProjectParameters["problem_data"]["problem_name"].GetString() ,
                                         ProjectParameters["output_configuration"])

    gid_output.ExecuteInitialize()

## Creation of Kratos model (build sub_model_parts or submeshes)
FluidModel = Model()
FluidModel.AddModelPart(main_model_part)

## Get the list of the skin submodel parts in the object Model
for i in range(ProjectParameters["solver_settings"]["skin_parts"].size()):
    skin_part_name = ProjectParameters["solver_settings"]["skin_parts"][i].GetString()
    FluidModel.AddModelPart(main_model_part.GetSubModelPart(skin_part_name))

## Get the list of the no-skin submodel parts in the object Model (results processes and no-skin conditions)
for i in range(ProjectParameters["solver_settings"]["no_skin_parts"].size()):
    no_skin_part_name = ProjectParameters["solver_settings"]["no_skin_parts"][i].GetString()
    FluidModel.AddModelPart(main_model_part.GetSubModelPart(no_skin_part_name))

## Get the list of the initial conditions submodel parts in the object Model
for i in range(ProjectParameters["initial_conditions_process_list"].size()):
    initial_cond_part_name = ProjectParameters["initial_conditions_process_list"][i]["Parameters"]["model_part_name"].GetString()
    FluidModel.AddModelPart(main_model_part.GetSubModelPart(initial_cond_part_name))

## Get the gravity submodel part in the object Model
for i in range(ProjectParameters["gravity"].size()):
    gravity_part_name = ProjectParameters["gravity"][i]["Parameters"]["model_part_name"].GetString()
    FluidModel.AddModelPart(main_model_part.GetSubModelPart(gravity_part_name))

## Print model_part and properties
if (echo_level > 1) and ((parallel_type == "OpenMP") or (mpi.rank == 0)):
    print("")
    print(main_model_part)
    for properties in main_model_part.Properties:
        print(properties)

## Processes construction
import process_factory
# "list_of_processes" contains all the processes already constructed (boundary conditions, initial conditions and gravity)
# Note 1: gravity is firstly constructed. Outlet process might need its information.
# Note 2: conditions are constructed before BCs. Otherwise, they may overwrite the BCs information.
list_of_processes =  process_factory.KratosProcessFactory(FluidModel).ConstructListOfProcesses( ProjectParameters["gravity"] )
list_of_processes += process_factory.KratosProcessFactory(FluidModel).ConstructListOfProcesses( ProjectParameters["initial_conditions_process_list"] )
list_of_processes += process_factory.KratosProcessFactory(FluidModel).ConstructListOfProcesses( ProjectParameters["boundary_conditions_process_list"] )
list_of_processes += process_factory.KratosProcessFactory(FluidModel).ConstructListOfProcesses( ProjectParameters["auxiliar_process_list"] )
list_of_processes += process_factory.KratosProcessFactory(FluidModel).ConstructListOfProcesses( ProjectParameters["remeshing_process_list"] )

if (echo_level > 1) and ((parallel_type == "OpenMP") or (mpi.rank == 0)):
    for process in list_of_processes:
        print(process)

## Circle distance function
circle_radious = 0.15
center_coordinates = [1.0, 0.5]

for node in main_model_part.Nodes:
    distance = ((node.X-center_coordinates[0])**2+(node.Y-center_coordinates[1])**2)**0.5 - circle_radious
    node.SetSolutionStepValue(DISTANCE, distance)

## Set the SLIP element flag and the elemental distance vector
n_nodes = len(main_model_part.Elements[1].GetNodes())
for element in main_model_part.Elements:
    element.Set(SLIP,False)

    elem_dist = Vector(n_nodes)
    elem_nodes = element.GetNodes()
    for i_node in range(0, n_nodes):
        elem_dist[i_node] = elem_nodes[i_node].GetSolutionStepValue(DISTANCE)
    element.SetValue(ELEMENTAL_DISTANCES, elem_dist)

## Processes initialization
for process in list_of_processes:
    process.ExecuteInitialize()

## Solver initialization
solver.Initialize()

## Stepping and time settings
# delta_time = ProjectParameters["problem_data"]["time_step"].GetDouble()
start_time = ProjectParameters["problem_data"]["start_time"].GetDouble()
end_time = ProjectParameters["problem_data"]["end_time"].GetDouble()

time = start_time
step = 0

if (output_post == True):
    gid_output.ExecuteBeforeSolutionLoop()

for process in list_of_processes:
    process.ExecuteBeforeSolutionLoop()

## Writing the full ProjectParameters file before solving
if ((parallel_type == "OpenMP") or (mpi.rank == 0)) and (echo_level > 0):
    f = open("ProjectParametersOutput.json", 'w')
    f.write(ProjectParameters.PrettyPrintJsonString())
    f.close()

## Set the initial condition
init_p = 0.0
init_v = Vector(3)
init_v[0] = 1.0
init_v[1] = 0.0
init_v[2] = 0.0
for node in main_model_part.Nodes:
    if (node.GetSolutionStepValue(DISTANCE) > 0.0):
        node.SetSolutionStepValue(VELOCITY, init_v)
        node.SetSolutionStepValue(PRESSURE, init_p)

while(time <= end_time):

    delta_time = solver.ComputeDeltaTime()
    step += 1
    time += delta_time
    main_model_part.CloneTimeStep(time)
    main_model_part.ProcessInfo[STEP] = step

    if (parallel_type == "OpenMP") or (mpi.rank == 0):
        print("")
        print("STEP = ", step)
        print("TIME = ", time)

    for process in list_of_processes:
        process.ExecuteInitializeSolutionStep()

    if (main_model_part.Is(MODIFIED) == True):
        ## In case there is remeshing, set distance function again
        for node in main_model_part.Nodes:
            distance = ((node.X-center_coordinates[0])**2+(node.Y-center_coordinates[1])**2)**0.5 - circle_radious
            node.SetSolutionStepValue(DISTANCE, distance)

        ## In case there is remeshing, set the elemental distance vector again
        for element in main_model_part.Elements:
            elem_dist = Vector(n_nodes)
            elem_nodes = element.GetNodes()
            for i_node in range(0, n_nodes):
                elem_dist[i_node] = elem_nodes[i_node].GetSolutionStepValue(DISTANCE)
            element.SetValue(ELEMENTAL_DISTANCES, elem_dist)

        solver.Initialize()
        for process in list_of_processes:
            process.ExecuteInitialize()
        for process in list_of_processes:
            process.ExecuteBeforeSolutionLoop()
        for process in list_of_processes:
            process.ExecuteInitializeSolutionStep()

    if (output_post == True):
        gid_output.ExecuteInitializeSolutionStep()

    if (main_model_part.Is(MODIFIED) == True):
        solver.Clear()

    solver.Solve()

    for process in list_of_processes:
        process.ExecuteFinalizeSolutionStep()

    if (output_post == True):
        gid_output.ExecuteFinalizeSolutionStep()

    for process in list_of_processes:
        process.ExecuteBeforeOutputStep()

    if (gid_output.IsOutputStep()) and (output_post == True):
        gid_output.PrintOutput()

    for process in list_of_processes:
        process.ExecuteAfterOutputStep()

for process in list_of_processes:
    process.ExecuteFinalize()

if (output_post == True):
    gid_output.ExecuteFinalize()
