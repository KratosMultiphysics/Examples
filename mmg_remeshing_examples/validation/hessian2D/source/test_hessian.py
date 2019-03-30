from __future__ import print_function, absolute_import, division #makes KratosMultiphysics backward compatible with python 2.6 and 2.7

import KratosMultiphysics
import KratosMultiphysics.MeshingApplication as MeshingApplication

import math

model = KratosMultiphysics.Model()
main_model_part = model.CreateModelPart("MainModelPart")
main_model_part.ProcessInfo.SetValue(KratosMultiphysics.DOMAIN_SIZE, 2)

# We add the variables needed
main_model_part.AddNodalSolutionStepVariable(KratosMultiphysics.DISTANCE)
main_model_part.AddNodalSolutionStepVariable(KratosMultiphysics.NODAL_AREA)

# We import the model main_model_part
KratosMultiphysics.ModelPartIO("2D_hessian_test").ReadModelPart(main_model_part)

# Calculate NODAL_H
find_nodal_h = KratosMultiphysics.FindNodalHNonHistoricalProcess(main_model_part)
find_nodal_h.Execute()

for node in main_model_part.Nodes:
    # Calculate the element size
    node.SetSolutionStepValue(KratosMultiphysics.DISTANCE, 0, math.tanh(-100.0 * (node.Y - 0.5 - 0.25 * math.sin(2*math.pi*node.X))) + math.tanh(100.0 * (node.Y - node.X)))

# We calculate the gardient of the distance variable
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
    "anisotropy_parameters":{
        "reference_variable_name"          : "DISTANCE",
        "hmin_over_hmax_anisotropic_ratio" : 0.15,
        "boundary_layer_max_distance"      : 1.0,
        "interpolation"                    : "Linear"
    }
}"""
)
local_gradient = MeshingApplication.ComputeHessianSolMetricProcess2D(main_model_part, KratosMultiphysics.DISTANCE, metric_param)
local_gradient.Execute()

# We create the remeshing process
remesh_param = KratosMultiphysics.Parameters("""{ }""")
MmgProcess = MeshingApplication.MmgProcess2D(main_model_part, remesh_param)
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
    "nodal_solution_step_data_variables" : ["DISTANCE"],
    "nodal_data_value_variables"         : ["NODAL_H"],
    "nodal_flag"                         : [],
    "element_data_value_variables"       : [],
    "condition_data_value_variables"     : [],
    "gauss_point_variables"              : []
}""")

vtk_io = KratosMultiphysics.VtkOutput(main_model_part, vtk_settings)
vtk_io.PrintOutput()
