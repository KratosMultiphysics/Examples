import KratosMultiphysics as KM

from KratosMultiphysics.StructuralMechanicsApplication.structural_mechanics_analysis import StructuralMechanicsAnalysis
from KratosMultiphysics.NeuralNetworkApplication.neural_network_analysis import NeuralNetworkAnalysis

if __name__ == "__main__":

	# Data generation for training
    with open("DataGenerationTrainingParameters.json") as json_file:
        parameters = KM.Parameters(json_file.read())
	
    model = KM.Model()
    solver = StructuralMechanicsAnalysis(model, parameters)
    solver.Run()
    
    # Data generation for testing
    with open("DataGenerationTestingParameters.json") as json_file:
        parameters = KM.Parameters(json_file.read())
    model = KM.Model()
    solver = StructuralMechanicsAnalysis(model, parameters)
    solver.Run()
    
    # Hypermodel tuning
    with open("TunerParameters.json") as json_file:
        parameters = KM.Parameters(json_file.read())

    tuner = NeuralNetworkAnalysis(parameters)
    tuner.Run()
    
    # Best model training and testing
    with open("TrainerParameters.json") as json_file:
        parameters = KM.Parameters(json_file.read())

    trainer = NeuralNetworkAnalysis(parameters)
    trainer.Run()
