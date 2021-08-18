from __future__ import print_function, absolute_import, division  # makes KratosMultiphysics backward compatible with python 2.6 and 2.7

# Importing the Kratos Library => only needed to get the CoSim-Python-Scripts on the path!
import KratosMultiphysics as KM
from KratosMultiphysics.CoSimulationApplication.co_simulation_analysis import CoSimulationAnalysis


parameter_file_name = "project_parameters_cosim_pure_SDoF.json"
parameter_file_name = "project_parameters_cosim_pure_fluid.json"
parameter_file_name = "project_parameters_cosim_oscilating_cylinder_fsi.json"

with open(parameter_file_name, 'r') as parameter_file:
    cosim_parameters = KM.Parameters(parameter_file.read())

simulation = CoSimulationAnalysis(cosim_parameters)
simulation.Run()
