from __future__ import print_function, absolute_import, division #makes KratosMultiphysics backward compatible with python 2.6 and 2.7

import KratosMultiphysics
import KratosMultiphysics.MeshingApplication as MeshingApplication

current_model = KratosMultiphysics.Model()
main_model_part = current_model.CreateModelPart("MainModelPart")
main_model_part.ProcessInfo.SetValue(KratosMultiphysics.DOMAIN_SIZE, 3)

# We add the variables needed
main_model_part.AddNodalSolutionStepVariable(KratosMultiphysics.DISTANCE)
main_model_part.AddNodalSolutionStepVariable(KratosMultiphysics.DISTANCE_GRADIENT)

# We import the model main_model_part
KratosMultiphysics.ModelPartIO("coarse_sphere").ReadModelPart(main_model_part)

# We calculate the gardient of the distance variable
find_nodal_h = KratosMultiphysics.FindNodalHNonHistoricalProcess(main_model_part)
find_nodal_h.Execute()
KratosMultiphysics.VariableUtils().SetNonHistoricalVariable(KratosMultiphysics.NODAL_AREA, 0.0, main_model_part.Nodes)
local_gradient = KratosMultiphysics.ComputeNodalGradientProcess3D(main_model_part, KratosMultiphysics.DISTANCE, KratosMultiphysics.DISTANCE_GRADIENT, KratosMultiphysics.NODAL_AREA)
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
level_set_param = KratosMultiphysics.Parameters("""
                        {
                            "minimal_size"                         : 0.1,
                            "enforce_current"                      : false,
                            "anisotropy_remeshing"                 : true,
                            "anisotropy_parameters":
                            {
                                "hmin_over_hmax_anisotropic_ratio"      : 0.01,
                                "boundary_layer_max_distance"           : 0.5,
                                "interpolation"                         : "Linear"
                            }
                        }
                        """)
metric_process = MeshingApplication.ComputeLevelSetSolMetricProcess3D(main_model_part,KratosMultiphysics.DISTANCE_GRADIENT,level_set_param)
metric_process.Execute()

# We create the remeshing process
remesh_param = KratosMultiphysics.Parameters("""{ }""")
MmgProcess = MeshingApplication.MmgProcess3D(main_model_part, remesh_param)
MmgProcess.Execute()

# Finally we export to GiD
from gid_output_process import GiDOutputProcess
gid_output = GiDOutputProcess(main_model_part,
                            "gid_output",
                            KratosMultiphysics.Parameters("""
                                {
                                    "result_file_configuration" : {
                                        "gidpost_flags": {
                                            "GiDPostMode": "GiD_PostBinary",
                                            "WriteDeformedMeshFlag": "WriteUndeformed",
                                            "WriteConditionsFlag": "WriteConditions",
                                            "MultiFileFlag": "SingleFile"
                                        },
                                        "nodal_results"       : ["DISTANCE", "DISTANCE_GRADIENT"]
                                    }
                                }
                                """)
                            )

gid_output.ExecuteInitialize()
gid_output.ExecuteBeforeSolutionLoop()
gid_output.ExecuteInitializeSolutionStep()
gid_output.PrintOutput()
gid_output.ExecuteFinalizeSolutionStep()
gid_output.ExecuteFinalize()

# Finally we export to VTK
vtk_settings = KratosMultiphysics.Parameters("""{
    "model_part_name"                    : "PLEASE_SPECIFY_MODEL_PART_NAME",
    "file_format"                        : "ascii",
    "output_precision"                   : 7,
    "output_control_type"                : "step",
    "output_frequency"                   : 1.0,
    "output_sub_model_parts"             : false,
    "save_output_files_in_folder"        : false,
    "nodal_solution_step_data_variables" : ["DISTANCE","DISTANCE_GRADIENT"],
    "nodal_data_value_variables"         : [],
    "element_data_value_variables"       : [],
    "condition_data_value_variables"     : [],
    "gauss_point_variables"              : []
}""")

vtk_io = KratosMultiphysics.VtkOutput(main_model_part, vtk_settings)
vtk_io.PrintOutput()

