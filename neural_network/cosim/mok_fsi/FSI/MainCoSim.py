from __future__ import print_function, absolute_import, division  # makes KratosMultiphysics backward compatible with python 2.6 and 2.7

# Importing the Kratos Library => only needed to get the CoSim-Python-Scripts on the path!
import KratosMultiphysics
import KratosMultiphysics.CoSimulationApplication

# Importing the base class
from KratosMultiphysics.CoSimulationApplication.co_simulation_analysis import CoSimulationAnalysis
import json

parameter_file_name = "cosim_mok_fsi_parameters_weak.json"
#parameter_file_name = "cosim_mok_fsi_parameters_strong.json"

with open(parameter_file_name, 'r') as parameter_file:
    cosim_parameters = KratosMultiphysics.Parameters(parameter_file.read())

simulation = CoSimulationAnalysis(cosim_parameters)
simulation.Run()
