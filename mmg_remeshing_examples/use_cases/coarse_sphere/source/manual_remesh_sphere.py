# We import the libraies
from __future__ import print_function, absolute_import, division #makes KratosMultiphysics backward compatible with python 2.6 and 2.7

import KratosMultiphysics
import KratosMultiphysics.MeshingApplication as MeshingApplication

# We create the model part
current_model = KratosMultiphysics.Model()
main_model_part = current_model.CreateModelPart("MainModelPart")
main_model_part.ProcessInfo.SetValue(KratosMultiphysics.DOMAIN_SIZE, 3)

# We add the variables needed
main_model_part.AddNodalSolutionStepVariable(KratosMultiphysics.DISTANCE)
main_model_part.AddNodalSolutionStepVariable(KratosMultiphysics.NODAL_H)

# We import the model main_model_part
KratosMultiphysics.ModelPartIO("coarse_sphere").ReadModelPart(main_model_part)

# We know that the gradient is unitary and in X direction
UnityVector = KratosMultiphysics.Vector(3)
UnityVector[0] = 1.0
UnityVector[1] = 0.0
UnityVector[2] = 0.0

# We set to zero the metric
MetricVector = KratosMultiphysics.Vector(6)

for node in main_model_part.Nodes:
    # Calculate the element size
    distance = node.GetSolutionStepValue(KratosMultiphysics.DISTANCE, 0)
    nodal_h = node.GetSolutionStepValue(KratosMultiphysics.NODAL_H, 0)
    element_size = 0.1
    if (abs(distance) > 0.5):
        element_size = nodal_h

    # Calculate anisotropic ratio
    ratio = 1.0
    if (abs(distance) < 0.5):
        ratio = 0.01 + (abs(distance)/0.5) * (1.0 - 0.01);

    # We get the gradient
    gradient_value = UnityVector

    # Finally we calculate the metric
    coeff0 = 1.0/(element_size * element_size);
    coeff1 = coeff0/(ratio * ratio);

    v0v0 = gradient_value[0]*gradient_value[0];
    v0v1 = gradient_value[0]*gradient_value[1];
    v0v2 = gradient_value[0]*gradient_value[2];
    v1v1 = gradient_value[1]*gradient_value[1];
    v1v2 = gradient_value[1]*gradient_value[2];
    v2v2 = gradient_value[2]*gradient_value[2];

    MetricVector[0] = coeff0*(1.0 - v0v0) + coeff1*v0v0
    MetricVector[1] = coeff0*(1.0 - v1v1) + coeff1*v1v1
    MetricVector[2] = coeff0*(1.0 - v2v2) + coeff1*v2v2
    MetricVector[3] = coeff0*(    - v0v1) + coeff1*v0v1
    MetricVector[4] = coeff0*(    - v1v2) + coeff1*v1v2
    MetricVector[5] = coeff0*(    - v0v2) + coeff1*v0v2
    node.SetValue(MeshingApplication.METRIC_TENSOR_3D, MetricVector)

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
                                    "nodal_results"       : ["DISTANCE"]
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
    "nodal_data_value_variables"         : [],
    "element_data_value_variables"       : [],
    "condition_data_value_variables"     : [],
    "gauss_point_variables"              : []
}""")

vtk_io = KratosMultiphysics.VtkOutput(main_model_part, vtk_settings)
vtk_io.PrintOutput()
