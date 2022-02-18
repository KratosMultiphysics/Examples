import KratosMultiphysics as KM
import tensorflow as tf

from KratosMultiphysics.NeuralNetworkApplication.neural_network_analysis import NeuralNetworkAnalysis

if __name__ == "__main__":

    with open("CNNLSTMProjectParameters.json") as json_file:
        #parameters = json.load(json_file)
        parameters = KM.Parameters(json_file.read())
    with tf.device('gpu:0'):
        trainer = NeuralNetworkAnalysis(parameters)
        trainer.Run()
