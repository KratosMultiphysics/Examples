
import KratosMultiphysics
import KratosMultiphysics.EmpireApplication

# Importing the base class
from co_simulation_steady_analysis import CoSimulationSteadyAnalysis
import json

# parameter_file_name = "project_parameters_cosim_pure_SDoF.json"
# parameter_file_name = "project_parameters_cosim_pure_fluid.json"
parameter_file_name = "project_parameters_cosim_naca0012_small_fsi.json"

with open(parameter_file_name, 'r') as parameter_file:
    cosim_parameters = json.load(parameter_file)

simulation = CoSimulationSteadyAnalysis(cosim_parameters)
simulation.Run()
