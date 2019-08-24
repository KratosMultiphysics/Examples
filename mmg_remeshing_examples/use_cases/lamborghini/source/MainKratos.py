from __future__ import print_function, absolute_import, division #makes KratosMultiphysics backward compatible with python 2.6 and 2.7

import KratosMultiphysics
import KratosMultiphysics.MeshingApplication as MeshingApplication

import os

# We create the model part
current_model = KratosMultiphysics.Model()
main_model_part = current_model.CreateModelPart("MainModelPart")
main_model_part.ProcessInfo.SetValue(KratosMultiphysics.DOMAIN_SIZE, 3)
main_model_part.ProcessInfo.SetValue(KratosMultiphysics.TIME, 0.0)
main_model_part.ProcessInfo.SetValue(KratosMultiphysics.DELTA_TIME, 1.0)
#main_model_part.ProcessInfo.SetValue(KratosMultiphysics.STEP, 1)

# We add the variables needed
main_model_part.AddNodalSolutionStepVariable(KratosMultiphysics.DISTANCE)
main_model_part.AddNodalSolutionStepVariable(KratosMultiphysics.DISTANCE_GRADIENT)

# We import the model main_model_part
file_path = os.path.dirname(os.path.realpath(__file__))
KratosMultiphysics.ModelPartIO(file_path + "/lamborgini_small").ReadModelPart(main_model_part)

# We calculate the gradient of the distance variable
find_nodal_h = KratosMultiphysics.FindNodalHNonHistoricalProcess(main_model_part)
find_nodal_h.Execute()
KratosMultiphysics.VariableUtils().SetNonHistoricalVariable(KratosMultiphysics.NODAL_AREA, 0.0, main_model_part.Nodes)
local_gradient = KratosMultiphysics.ComputeNodalGradientProcess(main_model_part, KratosMultiphysics.DISTANCE, KratosMultiphysics.DISTANCE_GRADIENT, KratosMultiphysics.NODAL_AREA)
local_gradient.Execute()

# We set to zero the metric
ZeroVector = KratosMultiphysics.Vector(6)
ZeroVector[0] = 0.0
ZeroVector[1] = 0.0
ZeroVector[2] = 0.0
ZeroVector[3] = 0.0
ZeroVector[4] = 0.0
ZeroVector[5] = 0.0

for node in main_model_part.Nodes:
    node.SetValue(MeshingApplication.METRIC_TENSOR_3D, ZeroVector)

# We define a metric using the ComputeLevelSetSolMetricProcess
mmg_parameters = KratosMultiphysics.Parameters("""
{
    "model_part_name"                   : "MainModelPart",
    "step_frequency"                    : 0,
    "initial_remeshing"                 : true,
    "automatic_remesh"                  : true,
    "automatic_remesh_parameters"       :{
        "automatic_remesh_type"            : "Ratio",
        "min_size_ratio"                   : 1.0,
        "max_size_ratio"                   : 10.0,
        "refer_type"                       : "Mean"
    },
    "echo_level"                        : 3
}
""")

from KratosMultiphysics.MeshingApplication.mmg_process import MmgProcess
process = MmgProcess(current_model, mmg_parameters)
process.ExecuteInitialize()
process.ExecuteInitializeSolutionStep()
process.ExecuteFinalizeSolutionStep()

# Finally we export to GiD
gid_parameters = KratosMultiphysics.Parameters("""
{
    "result_file_configuration" : {
        "gidpost_flags": {
            "GiDPostMode": "GiD_PostBinary",
            "WriteDeformedMeshFlag": "WriteUndeformed",
            "WriteConditionsFlag"  : "WriteConditions",
            "MultiFileFlag"        : "SingleFile"
        },
        "nodal_results"               : ["DISTANCE","DISTANCE_GRADIENT"],
        "nodal_nonhistorical_results" : ["NODAL_H"]
    }
}
""")

from KratosMultiphysics.gid_output_process import GiDOutputProcess
gid_output = GiDOutputProcess(main_model_part, "gid_output", gid_parameters)

gid_output.ExecuteInitialize()
gid_output.ExecuteBeforeSolutionLoop()
gid_output.ExecuteInitializeSolutionStep()
gid_output.PrintOutput()
gid_output.ExecuteFinalizeSolutionStep()
gid_output.ExecuteFinalize()

# Finally we export to VTK
vtk_settings = KratosMultiphysics.Parameters("""{
    "model_part_name"                    : "MainModelPart",
    "file_format"                        : "ascii",
    "output_precision"                   : 7,
    "output_control_type"                : "step",
    "output_frequency"                   : 1.0,
    "output_sub_model_parts"             : false,
    "save_output_files_in_folder"        : false,
    "nodal_solution_step_data_variables" : ["DISTANCE","DISTANCE_GRADIENT"],
    "nodal_data_value_variables"         : ["NODAL_H"],
    "element_data_value_variables"       : [],
    "condition_data_value_variables"     : [],
    "gauss_point_variables"              : []
}""")

vtk_io = KratosMultiphysics.VtkOutput(main_model_part, vtk_settings)
vtk_io.PrintOutput()
