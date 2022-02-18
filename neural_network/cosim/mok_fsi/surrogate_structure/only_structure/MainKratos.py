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
load_file = "original_loads.dat"
training_loops = 0
factor_flag = 0

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
      factor = np.random.normal(0.0, 0.01) * factor_flag
      if self.time_counter < 20:
        factor = factor * 15
      if 20<= self.time_counter < 40:
        factor = factor * 5
      if 40<= self.time_counter < 60:
        factor = factor * 2
      i = 0
      for node in fsi_interface.Nodes:
        constant_load = (1.0 + factor) * (force_nodes[2*i])
        node.SetSolutionStepValue(csm.POINT_LOAD_X,0,constant_load)
        constant_load = (1.0 + factor) * (force_nodes[2*i+1])
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


# Run the modified training loops
for i in range(training_loops):
  print('Iteration: ' + str(i))
  # Generate the data from the modified structural analysis
  with open(parameter_file_name, 'r') as parameter_file:
    parameters = KratosMultiphysics.Parameters(parameter_file.read())

  model = KratosMultiphysics.Model()
  if i % 10 == 0:
    factor_flag = 0.0
  else:
    factor_flag = 0.0
  simulation = StructuralMechanicsAnalysisWithVaryingLoad(model, parameters)
  simulation.Run()

  # Further train the neural network with the new data
  with open(neural_network_retrain_file_name) as json_file:
    parameters = KratosMultiphysics.Parameters(json_file.read())

  trainer = NeuralNetworkAnalysis(parameters)
  trainer.Run()

