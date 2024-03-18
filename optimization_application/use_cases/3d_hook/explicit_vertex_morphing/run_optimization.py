# Import Kratos core and apps
import KratosMultiphysics as Kratos
import KratosMultiphysics.StructuralMechanicsApplication
import KratosMultiphysics.ShapeOptimizationApplication as KratosSOA

# Additional imports
from KratosMultiphysics.OptimizationApplication.optimization_analysis import OptimizationAnalysis

def RunSimulation():
    with open("optimization_parameters.json",'r') as parameter_file:
        parameters = Kratos.Parameters(parameter_file.read())

    # Defining the model_part
    model = Kratos.Model()
    analysis = OptimizationAnalysis(model, parameters)
    analysis.Run()

def VisualizeMdpa():
    model = Kratos.Model()
    model_part = model.CreateModelPart("test")
    Kratos.ModelPartIO("../hook", Kratos.ModelPartIO.READ | Kratos.ModelPartIO.MESH_ONLY).ReadModelPart(model_part)

    Kratos.VtuOutput(model_part.GetSubModelPart("domain")).PrintOutput("testing/domain")
    Kratos.VtuOutput(model_part.GetSubModelPart("design_surface_1")).PrintOutput("testing/design_surface_1")
    Kratos.VtuOutput(model_part.GetSubModelPart("non_design_top_1")).PrintOutput("testing/non_design_top_1")
    Kratos.VtuOutput(model_part.GetSubModelPart("non_design_inner_1")).PrintOutput("testing/non_design_inner_1")

    model_part.CreateSubModelPart("boundary")
    KratosSOA.GeometryUtilities(model_part).ExtractBoundaryNodes("boundary")
    Kratos.VtuOutput(model_part.GetSubModelPart("boundary")).PrintOutput("testing/boundary")

if __name__ == "__main__":
    # VisualizeMdpa()
    RunSimulation()
