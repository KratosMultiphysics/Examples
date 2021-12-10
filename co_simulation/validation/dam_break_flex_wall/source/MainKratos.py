import KratosMultiphysics as KM
from KratosMultiphysics.CoSimulationApplication.co_simulation_analysis import CoSimulationAnalysis

"""
For user-scripting it is intended that a new class is derived
from CoSimulationAnalysis to do modifications
Check also "kratos/python_scripts/analysis_stage.py" for available methods that can be overridden
"""

parameter_file_name = "ProjectParametersCoSim.json"
with open(parameter_file_name,'r') as parameter_file:
    parameters = KM.Parameters(parameter_file.read())

#TODO - Remove loggers before merging to master.
file_logger_info = KM.FileLoggerOutput("KratosInfo.log")
file_logger_info.SetSeverity(KM.Logger.Severity.INFO)
KM.Logger.AddOutput(file_logger_info)

file_logger_warn = KM.FileLoggerOutput("KratosWarning.log")
file_logger_warn.SetSeverity(KM.Logger.Severity.WARNING)
KM.Logger.AddOutput(file_logger_warn)

simulation = CoSimulationAnalysis(parameters)
simulation.Run()
