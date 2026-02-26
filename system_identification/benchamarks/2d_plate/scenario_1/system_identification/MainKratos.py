import os
import KratosMultiphysics as Kratos
from KratosMultiphysics.OptimizationApplication.optimization_analysis import OptimizationAnalysis
from KratosMultiphysics.StructuralMechanicsApplication.structural_mechanics_analysis import StructuralMechanicsAnalysis


if __name__ == "__main__":
    with open("OptimizationParameters.json", "r") as file_input:
        file_data = file_input.read()

        # if sensor_error file exist, remove it

        if os.path.exists("sensor_error.txt"):
            os.remove("sensor_error.txt")

        model = Kratos.Model()
        analysis = OptimizationAnalysis(model, Kratos.Parameters(file_data))

        analysis.Run()

        mp = model.GetModelPart("Structure")
        damage_5 = mp.GetSubModelPart("damage_5")
        aver_E = 0.0
        for element in damage_5.Elements:
            aver_E += element.Properties[Kratos.YOUNG_MODULUS]
        aver_E /= damage_5.NumberOfElements()
        print(f"Averaged Young's modulus in damage_5: {aver_E:.2e} Pa")

        
