
import KratosMultiphysics as KM
import KratosMultiphysics.MeshingApplication as MA
import KratosMultiphysics.StructuralMechanicsApplication as SMA

from KratosMultiphysics.StructuralMechanicsApplication.adaptive_remeshing.adaptative_remeshing_structural_mechanics_analysis import AdaptativeRemeshingStructuralMechanicsAnalysis

## Import define_output
with open("ProjectParameters.json",'r') as parameter_file:
    ProjectParameters = KM.Parameters(parameter_file.read())

# Creating the test
model = KM.Model()
analysis = AdaptativeRemeshingStructuralMechanicsAnalysis(model, ProjectParameters)
KM.Logger.GetDefaultOutput().SetSeverity(KM.Logger.Severity.INFO)
analysis.Run()
