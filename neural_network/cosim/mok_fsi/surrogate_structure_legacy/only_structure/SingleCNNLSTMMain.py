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
neural_network_original_file_name = "CNNLSTMProjectParameters.json"
neural_network_retrain_file_name = "NeuralNetworkProjectParameters.json"
load_file = "data/training_in_raw.dat"


class StructuralMechanicsAnalysisWithVaryingLoad(StructuralMechanicsAnalysis):
    def __init__(self, model, project_parameters):
      super(StructuralMechanicsAnalysisWithVaryingLoad, self).__init__(model, project_parameters)
      self.time_counter = 0
      with open(load_file, 'r') as loads_file:
        	self.forces = np.genfromtxt(loads_file)

    def InitializeSolutionStep(self):
      super(StructuralMechanicsAnalysisWithVaryingLoad, self).InitializeSolutionStep()
      fsi_interface = self.model["Structure.PointLoad2D_FSI"]

      force_nodes = self.forces[self.time_counter]
      i=0
      for node in fsi_interface.Nodes:
        constant_load =(force_nodes[2*i])
        node.SetSolutionStepValue(csm.POINT_LOAD_X,0,constant_load)
        constant_load = (force_nodes[2*i+1])
        node.SetSolutionStepValue(csm.POINT_LOAD_Y,0,constant_load)
        i += 1
      self.time_counter += 1

# Run the original Structure simulation
with open(parameter_file_name, 'r') as parameter_file:
    parameters = KratosMultiphysics.Parameters(parameter_file.read())

model = KratosMultiphysics.Model()
simulation = StructuralMechanicsAnalysisWithVaryingLoad(model, parameters)
simulation.Run()

# Generate and train the Neural Network for the first time
with open(neural_network_original_file_name) as json_file:
  parameters = KratosMultiphysics.Parameters(json_file.read())

trainer = NeuralNetworkAnalysis(parameters)
trainer.Run()



