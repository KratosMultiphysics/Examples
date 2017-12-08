from __future__ import print_function, absolute_import, division #makes KratosMultiphysics backward compatible with python 2.6 and 2.7

import KratosMultiphysics
import KratosMultiphysics.MeshingApplication as MeshingApplication

main_model_part = KratosMultiphysics.ModelPart("MainModelPart")
main_model_part.ProcessInfo.SetValue(KratosMultiphysics.DOMAIN_SIZE, 3)

# We add the variables needed 
main_model_part.AddNodalSolutionStepVariable(KratosMultiphysics.DISTANCE)
main_model_part.AddNodalSolutionStepVariable(KratosMultiphysics.DISTANCE_GRADIENT)
main_model_part.AddNodalSolutionStepVariable(KratosMultiphysics.NODAL_AREA)

# We import the model main_model_part
KratosMultiphysics.ModelPartIO("coarse_sphere").ReadModelPart(main_model_part)

# We calculate the gardient of the distance variable
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
    node.SetValue(MeshingApplication.MMG_METRIC, ZeroVector)
            
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
                                        "nodal_results"       : []
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

