import json
import KratosMultiphysics as KM

from KratosMultiphysics.NeuralNetworkApplication.neural_network_analysis import NeuralNetworkAnalysis

if __name__ == "__main__":
    # ProjectParametersWithModel generates a simple model without specifying the composition
    with open("ProjectParametersWithModel.json") as json_file:
    # ProjectParametersWithoutModel specifies the model in the json model
    #with open("ProjectParametersWithoutModel.json") as json_file:
        #parameters = json.load(json_file)
        parameters = KM.Parameters(json_file.read())

    trainer = NeuralNetworkAnalysis(parameters)
    trainer.Run()
