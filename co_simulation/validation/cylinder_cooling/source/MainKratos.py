import KratosMultiphysics as KM
from KratosMultiphysics.CoSimulationApplication.co_simulation_analysis import CoSimulationAnalysis
import time

# get the start time
st = time.time()

"""
For user-scripting it is intended that a new class is derived
from CoSimulationAnalysis to do modifications
Check also "kratos/python_scripts/analysis-stage.py" for available methods that can be overridden
"""

parameter_file_name = "CoSim.json"
with open(parameter_file_name,'r') as parameter_file:
    parameters = KM.Parameters(parameter_file.read())

simulation = CoSimulationAnalysis(parameters)
simulation.Run()

# get the end time
et = time.time()
# get the execution time
elapsed_time = et - st
print('Execution time:', elapsed_time, 'seconds')