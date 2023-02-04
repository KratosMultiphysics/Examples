import KratosMultiphysics
from KratosMultiphysics.CompressiblePotentialFlowApplication.potential_flow_analysis import PotentialFlowAnalysis

with open("ProjectParametersPrimal.json",'r') as parameter_file:
	parameters = KratosMultiphysics.Parameters(parameter_file.read())
input_file =parameters["solver_settings"]["model_import_settings"]["input_filename"].GetString()

model = KratosMultiphysics.Model()
simulation = PotentialFlowAnalysis(model,parameters)
simulation.Run()

with open("ProjectParametersAdjoint.json",'r') as parameter_file:
	parameters = KratosMultiphysics.Parameters(parameter_file.read())
parameters["solver_settings"]["model_import_settings"]["input_filename"].SetString(input_file)

model = KratosMultiphysics.Model()
adjoint_simulation = PotentialFlowAnalysis(model,parameters)
adjoint_simulation.Run()
