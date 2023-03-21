
# Importing the Kratos Library => only needed to get the CoSim-Python-Scripts on the path!
import KratosMultiphysics
import KratosMultiphysics.EmpireApplication

# Importing the base class
from co_simulation_analysis import CoSimulationAnalysis
import json

parameter_file_name = "project_parameters_cosim_pure_structural.json"
parameter_file_name = "project_parameters_cosim_pure_fluid.json"
parameter_file_name = "project_parameters_cosim_wall_fsi.json"

with open(parameter_file_name, 'r') as parameter_file:
    cosim_parameters = json.load(parameter_file)

simulation = CoSimulationAnalysis(cosim_parameters)
simulation.Run()
