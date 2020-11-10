import KratosMultiphysics
import KratosMultiphysics.StructuralMechanicsApplication as StructuralMechanics

from KratosMultiphysics.StructuralMechanicsApplication.structural_mechanics_analysis import StructuralMechanicsAnalysis

class StructuralMechanicsAnalysisWithEigenPostProcessing(StructuralMechanicsAnalysis):
    """This class prints information abt the computen Eigenvectors
    It also shows how the "StructuralMechanicsAnalysis" can be customized by deriving from it
    """
    def Finalize(self):
        super().Finalize()
        main_model_part_name = self.project_parameters["solver_settings"]["model_part_name"].GetString()
        main_model_part = self.model[main_model_part_name]
        # Postprocessing the output in the terminal:
        print("Computed Eigenvalues:\n", main_model_part.ProcessInfo[StructuralMechanics.EIGENVALUE_VECTOR])
        print("Computed Eigenvectors on Node 1:\n", main_model_part.GetNode(1).GetValue(StructuralMechanics.EIGENVECTOR_MATRIX)) # for node with id 1
        # to get the output on every node (A lot!):
        # for node in main_model_part.Nodes:
        #     print(node.GetValue(StructuralMechanics.EIGENVECTOR_MATRIX))

if __name__ == "__main__":

    with open("ProjectParameters.json",'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())

    model = KratosMultiphysics.Model()
    simulation = StructuralMechanicsAnalysisWithEigenPostProcessing(model,parameters)
    simulation.Run()
