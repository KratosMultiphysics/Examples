import KratosMultiphysics as KM

import numpy as np

"""
For user-scripting it is intended that a new class is derived
from CoSimulationAnalysis to do modifications
Check also "kratos/python_scripts/analysis-stage.py" for available methods that can be overridden
"""


with open("data_generation/sdof_solver/results_sdof.dat",'r') as file:
    data = np.genfromtxt(file)

with open("neural_network_training/data/training_in_raw.dat", 'w') as training_in_file:
    for value in data[:,1]:
        training_in_file.write(str(value)+"\n")
with open("neural_network_training/data/training_out_raw.dat", 'w') as training_out_file:
    for value in data[:,2]:
        training_out_file.write(str(value)+"\n")

