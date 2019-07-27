from __future__ import print_function, absolute_import, division #makes KratosMultiphysics backward compatible with python 2.6 and 2.7

import KratosMultiphysics
import KratosMultiphysics.MeshingApplication as MeshingApplication

import math

model = KratosMultiphysics.Model()
main_model_part = model.CreateModelPart("MainModelPart")
main_model_part.ProcessInfo.SetValue(KratosMultiphysics.DOMAIN_SIZE, 3)

# We add the variables needed
main_model_part.AddNodalSolutionStepVariable(KratosMultiphysics.DISTANCE)
main_model_part.AddNodalSolutionStepVariable(KratosMultiphysics.NODAL_AREA)

# We import the model main_model_part
KratosMultiphysics.ModelPartIO("3D_hessian_test").ReadModelPart(main_model_part)

for i in range(2):
    # Calculate NODAL_H
    find_nodal_h = KratosMultiphysics.FindNodalHNonHistoricalProcess(main_model_part)
    find_nodal_h.Execute()

    for node in main_model_part.Nodes:
        # Calculate the element size
        node.SetSolutionStepValue(KratosMultiphysics.DISTANCE, 0, math.tanh(-100.0 * (node.Y - 0.5 - 0.25 * math.sin(2*math.pi*node.X))) + math.tanh(100.0 * (node.Y - node.X)))

    # We calculate the gardient of the distance variable
    minimal_size = 0.01/float(i + 1)
    metric_param = KratosMultiphysics.Parameters(
    """{
        "hessian_strategy_parameters"              :{
                "estimate_interpolation_error"     : false,
                "interpolation_error"              : 0.004,
                "mesh_dependent_constant"          : 0.28125
        },
        "minimal_size"                      : 0.005,
        "maximal_size"                      : 1.0,
        "enforce_current"                   : false,
        "anisotropy_remeshing"              : true,
        "enforced_anisotropy_parameters":{
            "reference_variable_name"          : "DISTANCE",
            "hmin_over_hmax_anisotropic_ratio" : 0.15,
            "boundary_layer_max_distance"      : 1.0,
            "interpolation"                    : "Linear"
        }
    }"""
    )
    metric_param["minimal_size"].SetDouble(minimal_size)
    local_gradient = MeshingApplication.ComputeHessianSolMetricProcess3D(main_model_part, KratosMultiphysics.DISTANCE, metric_param)
    local_gradient.Execute()

    # We create the remeshing process
    remesh_param = KratosMultiphysics.Parameters("""{ }""")
    MmgProcess = MeshingApplication.MmgProcess3D(main_model_part, remesh_param)
    MmgProcess.Execute()

    find_nodal_h.Execute()

    # Finally we export to GiD
    from KratosMultiphysics.gid_output_process import GiDOutputProcess
    gid_output = GiDOutputProcess(main_model_part,
                                "gid_output_" + str(i),
                                KratosMultiphysics.Parameters("""
                                {
                                    "result_file_configuration" : {
                                        "gidpost_flags": {
                                            "GiDPostMode": "GiD_PostBinary",
                                            "WriteDeformedMeshFlag": "WriteUndeformed",
                                            "WriteConditionsFlag": "WriteConditions",
                                            "MultiFileFlag": "SingleFile"
                                        },
                                        "nodal_results"               : ["DISTANCE"],
                                        "nodal_nonhistorical_results" : ["NODAL_H"]
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
        "model_part_name"                    : "MainModelPart",
        "file_format"                        : "ascii",
        "output_precision"                   : 7,
        "output_control_type"                : "step",
        "output_frequency"                   : 1.0,
        "output_sub_model_parts"             : false,
        "save_output_files_in_folder"        : false,
        "custom_name_prefix"                 : "",
        "nodal_solution_step_data_variables" : ["DISTANCE"],
        "nodal_data_value_variables"         : ["NODAL_H"],
        "nodal_flags"                        : [],
        "element_data_value_variables"       : [],
        "condition_data_value_variables"     : [],
        "gauss_point_variables"              : []
    }""")

    vtk_settings["custom_name_prefix"].SetString("ITER_" + str(i) + "_")
    vtk_io = KratosMultiphysics.VtkOutput(main_model_part, vtk_settings)
    vtk_io.PrintOutput()

