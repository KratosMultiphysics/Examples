# We import the libraies
from __future__ import print_function, absolute_import, division #makes KratosMultiphysics backward compatible with python 2.6 and 2.7

# Import Kratos
import KratosMultiphysics
import KratosMultiphysics.MeshingApplication as MeshingApplication

# Import os
import os

# We create the model part
current_model = KratosMultiphysics.Model()
main_model_part = current_model.CreateModelPart("MainModelPart")
main_model_part.ProcessInfo.SetValue(KratosMultiphysics.DOMAIN_SIZE, 3)
main_model_part.ProcessInfo.SetValue(KratosMultiphysics.TIME, 0.0)
main_model_part.ProcessInfo.SetValue(KratosMultiphysics.DELTA_TIME, 1.0)
main_model_part.ProcessInfo.SetValue(KratosMultiphysics.STEP, 1)

# We add the variables needed
main_model_part.AddNodalSolutionStepVariable(KratosMultiphysics.NODAL_H)
main_model_part.AddNodalSolutionStepVariable(KratosMultiphysics.NORMAL)
main_model_part.AddNodalSolutionStepVariable(KratosMultiphysics.IS_FLUID)
main_model_part.AddNodalSolutionStepVariable(KratosMultiphysics.IS_STRUCTURE)
main_model_part.AddNodalSolutionStepVariable(KratosMultiphysics.IS_FREE_SURFACE)
main_model_part.AddNodalSolutionStepVariable(KratosMultiphysics.IS_BOUNDARY)
main_model_part.AddNodalSolutionStepVariable(KratosMultiphysics.FLAG_VARIABLE)
main_model_part.AddNodalSolutionStepVariable(KratosMultiphysics.DISTANCE)
main_model_part.AddNodalSolutionStepVariable(KratosMultiphysics.DISTANCE_GRADIENT)

# We import the model main_model_part
file_path = os.path.dirname(os.path.realpath(__file__))
KratosMultiphysics.ModelPartIO(file_path + "/test_box").ReadModelPart(main_model_part)

# We calculate the gradient of the distance variable
find_nodal_h = KratosMultiphysics.FindNodalHNonHistoricalProcess(main_model_part)
find_nodal_h.Execute()
KratosMultiphysics.VariableUtils().SetNonHistoricalVariableToZero(KratosMultiphysics.NODAL_AREA, main_model_part.Nodes)
local_gradient = KratosMultiphysics.ComputeNodalGradientProcess3D(main_model_part, KratosMultiphysics.DISTANCE, KratosMultiphysics.DISTANCE_GRADIENT, KratosMultiphysics.NODAL_AREA)
local_gradient.Execute()

# We set to zero the metric
KratosMultiphysics.VariableUtils().SetNonHistoricalVariableToZero(MeshingApplication.METRIC_TENSOR_3D, main_model_part.Nodes)

# We define a metric using the ComputeLevelSetSolMetricProcess
metric_parameters = KratosMultiphysics.Parameters("""
{
    "minimal_size"                         : 0.2,
    "maximal_size"                         : 10.0,
    "sizing_parameters":
    {
        "reference_variable_name"          : "DISTANCE",
        "boundary_layer_max_distance"      : 2.0,
        "interpolation"                    : "exponential"
    },
    "enforce_current"                      : false,
    "anisotropy_remeshing"                 : false
}
""")
metric_process = MeshingApplication.ComputeLevelSetSolMetricProcess3D(main_model_part, KratosMultiphysics.DISTANCE_GRADIENT, metric_parameters)
metric_process.Execute()

mmg_parameters = KratosMultiphysics.Parameters("""
{
    "filename"                              : "out",
    "discretization_type"                   : "ISOSURFACE",
    "isosurface_parameters"                 :
    {
        "isosurface_variable"               : "DISTANCE",
        "nonhistorical_variable"            : false,
        "remove_internal_regions"           : true
    },
    "framework"                             : "Eulerian",
    "internal_variables_parameters"         :
    {
        "allocation_size"                       : 1000,
        "bucket_size"                           : 4,
        "search_factor"                         : 2,
        "interpolation_type"                    : "LST",
        "internal_variable_interpolation_list"  : []
    },
    "force_sizes"                           :
    {
        "force_min"                             : true,
        "minimal_size"                          : 0.2,
        "force_max"                             : true,
        "maximal_size"                          : 10.0
    },
    "advanced_parameters"                   :
    {
        "force_hausdorff_value"                 : true,
        "hausdorff_value"                       : 0.1,
        "no_move_mesh"                          : false,
        "no_surf_mesh"                          : false,
        "no_insert_mesh"                        : false,
        "no_swap_mesh"                          : false,
        "normal_regularization_mesh"            : false,
        "deactivate_detect_angle"               : false,
        "force_gradation_value"                 : true,
        "gradation_value"                       : 1.2
    },
    "save_external_files"                   : false,
    "save_mdpa_file"                        : false,
    "max_number_of_searchs"                 : 1000,
    "interpolate_non_historical"            : false,
    "extrapolate_contour_values"            : true,
    "surface_elements"                      : false,
    "search_parameters"                     :
    {
        "allocation_size"                       : 1000,
        "bucket_size"                           : 4,
        "search_factor"                         : 2.0
    },
    "echo_level"                            : 3,
    "debug_result_mesh"                     : false,
    "step_data_size"                        : 0,
    "initialize_entities"                   : true,
    "remesh_at_non_linear_iteration"        : false,
    "buffer_size"                           : 0
}
""")

# We create the remeshing utility
mmg_parameters["filename"].SetString(file_path + "/" + mmg_parameters["filename"].GetString())
mmg_process = MeshingApplication.MmgProcess3D(main_model_part, mmg_parameters)

# Finally we export to GiD
from gid_output_process import GiDOutputProcess
gid_output = GiDOutputProcess(main_model_part,
                            "gid_output_not_remeshed",
                            KratosMultiphysics.Parameters("""
                                {
                                    "result_file_configuration" : {
                                        "gidpost_flags": {
                                            "GiDPostMode": "GiD_PostBinary",
                                            "WriteDeformedMeshFlag": "WriteUndeformed",
                                            "WriteConditionsFlag": "WriteConditions",
                                            "MultiFileFlag": "SingleFile"
                                        },
                                        "nodal_results"               : ["DISTANCE","DISTANCE_GRADIENT"],
                                        "nodal_nonhistorical_results" : ["ANISOTROPIC_RATIO"],
                                        "nodal_flags_results"         : ["BLOCKED"]
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
from vtk_output_process import VtkOutputProcess
vtk_output_process = VtkOutputProcess(current_model,
                            KratosMultiphysics.Parameters("""{
                                    "save_output_files_in_folder"        : false,
                                    "model_part_name"                    : "MainModelPart",
                                    "nodal_solution_step_data_variables" : ["DISTANCE","DISTANCE_GRADIENT"],
                                    "nodal_data_value_variables"         : ["ANISOTROPIC_RATIO"],
                                    "nodal_flags"                        : ["BLOCKED"],
                                    "element_flags"                      : ["TO_ERASE","INSIDE"]
                                }
                                """)
                            )

vtk_output_process.ExecuteInitialize()
vtk_output_process.ExecuteBeforeSolutionLoop()
vtk_output_process.ExecuteInitializeSolutionStep()
vtk_output_process.PrintOutput()
vtk_output_process.ExecuteFinalizeSolutionStep()
vtk_output_process.ExecuteFinalize()

# We remesh
mmg_process.Execute()

# Finally we export to GiD
main_model_part.ProcessInfo.SetValue(KratosMultiphysics.STEP, 2)
from gid_output_process import GiDOutputProcess
gid_output = GiDOutputProcess(main_model_part,
                            "gid_output_remeshed",
                            KratosMultiphysics.Parameters("""
                                {
                                    "result_file_configuration" : {
                                        "gidpost_flags": {
                                            "GiDPostMode": "GiD_PostBinary",
                                            "WriteDeformedMeshFlag": "WriteUndeformed",
                                            "WriteConditionsFlag": "WriteConditions",
                                            "MultiFileFlag": "SingleFile"
                                        },
                                        "nodal_results"               : ["DISTANCE","DISTANCE_GRADIENT"],
                                        "nodal_nonhistorical_results" : ["ANISOTROPIC_RATIO"],
                                        "nodal_flags_results"         : ["BLOCKED"]
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
from vtk_output_process import VtkOutputProcess
vtk_output_process = VtkOutputProcess(current_model,
                            KratosMultiphysics.Parameters("""{
                                    "save_output_files_in_folder"        : false,
                                    "model_part_name"                    : "MainModelPart",
                                    "nodal_solution_step_data_variables" : ["DISTANCE","DISTANCE_GRADIENT"],
                                    "nodal_data_value_variables"         : ["ANISOTROPIC_RATIO"],
                                    "nodal_flags"                        : ["BLOCKED"],
                                    "element_flags"                      : ["TO_ERASE","INSIDE"]
                                }
                                """)
                            )

vtk_output_process.ExecuteInitialize()
vtk_output_process.ExecuteBeforeSolutionLoop()
vtk_output_process.ExecuteInitializeSolutionStep()
vtk_output_process.PrintOutput()
vtk_output_process.ExecuteFinalizeSolutionStep()
vtk_output_process.ExecuteFinalize()
