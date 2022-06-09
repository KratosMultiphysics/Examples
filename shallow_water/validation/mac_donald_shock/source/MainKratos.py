import argparse
import KratosMultiphysics
import KratosMultiphysics.ShallowWaterApplication

from KratosMultiphysics.ShallowWaterApplication.shallow_water_analysis import ShallowWaterAnalysis
from KratosMultiphysics.ShallowWaterApplication.utilities import benchmarking_utilities as utils

parser = argparse.ArgumentParser()
parser.add_argument("--time_step", type=float)
parser.add_argument("--courant_number", type=float)
parser.add_argument("--automatic_time_step", type=bool)
parser.add_argument("--shock_capturing_type", type=str)
parser.add_argument("--input_filename", type=str)
parser.add_argument("--output_filename", type=str)
parser.add_argument("--analysis_label", type=str)
parser.add_argument("--remove_output", type=bool, default=False)
args = parser.parse_args()

with open("ProjectParameters.json",'r') as parameter_file:
    parameters = KratosMultiphysics.Parameters(parameter_file.read())

if args.time_step is not None:
    parameters['solver_settings']['time_stepping']['time_step'].SetDouble(args.time_step)
if args.courant_number is not None:
    parameters['solver_settings']['time_stepping']['courant_number'].SetDouble(args.courant_number)
if args.automatic_time_step is not None:
    parameters['solver_settings']['time_stepping']['automatic_time_step'].SetBool(args.automatic_time_step)
if args.shock_capturing_type is not None:
    parameters['solver_settings']['shock_capturing_type'].SetString(args.shock_capturing_type)
if args.input_filename is not None:
    utils.GetModelerParameters(parameters['modelers'], 'import_mdpa_modeler')['input_filename'].SetString(args.input_filename)
if args.output_filename is not None:
    utils.GetProcessParameters(parameters['output_processes'], 'convergence_output_process')['file_name'].SetString(args.output_filename)
if args.analysis_label is not None:
    utils.GetProcessParameters(parameters['output_processes'], 'convergence_output_process')['analysis_label'].SetString(args.analysis_label)
if args.remove_output:
    utils.KeepOnlyThisProcess(parameters['output_processes'], 'convergence_output_process')

model = KratosMultiphysics.Model()
ShallowWaterAnalysis(model, parameters).Run()
