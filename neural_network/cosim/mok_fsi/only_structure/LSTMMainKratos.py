import KratosMultiphysics as KM

from KratosMultiphysics.NeuralNetworkApplication.neural_network_analysis import NeuralNetworkAnalysis

if __name__ == "__main__":

    with open("LSTMProjectParameters.json") as json_file:
        #parameters = json.load(json_file)
        parameters = KM.Parameters(json_file.read())

    trainer = NeuralNetworkAnalysis(parameters)
    trainer.Run()