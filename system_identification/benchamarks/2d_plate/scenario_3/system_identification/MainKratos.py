import os
import KratosMultiphysics as Kratos
from KratosMultiphysics.OptimizationApplication.optimization_analysis import OptimizationAnalysis
from KratosMultiphysics.StructuralMechanicsApplication.structural_mechanics_analysis import StructuralMechanicsAnalysis


if __name__ == "__main__":
    with open("OptimizationParameters.json", "r") as file_input:
        file_data = file_input.read()

        model = Kratos.Model()
        analysis = OptimizationAnalysis(model, Kratos.Parameters(file_data))

        analysis.Run()

        
