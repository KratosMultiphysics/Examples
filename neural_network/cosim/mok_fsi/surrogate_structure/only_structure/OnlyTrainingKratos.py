from __future__ import print_function, absolute_import, division  # makes KratosMultiphysics backward compatible with python 2.6 and 2.7

# Importing the Kratos Library => only needed to get the CoSim-Python-Scripts on the path!
import KratosMultiphysics
import KratosMultiphysics.StructuralMechanicsApplication as csm

# Importing the base class
from KratosMultiphysics.StructuralMechanicsApplication.structural_mechanics_analysis import StructuralMechanicsAnalysis
from KratosMultiphysics.NeuralNetworkApplication.neural_network_analysis import NeuralNetworkAnalysis
import json
import numpy as np

parameter_file_name = "ProjectParametersCSM.json"
# neural_network_original_file_name = "LSTMProjectParameters.json"
# neural_network_original_file_name = "ConvProjectParameters.json"
# neural_network_original_file_name = "Conv2DProjectParameters.json"
neural_network_original_file_name = "CNNLSTMProjectParameters_new.json"
neural_network_retrain_file_name = "NeuralNetworkProjectParameters.json"


# Generate and train the Neural Network for the first time
with open(neural_network_original_file_name) as json_file:
  parameters = KratosMultiphysics.Parameters(json_file.read())

trainer = NeuralNetworkAnalysis(parameters)
trainer.Run()



