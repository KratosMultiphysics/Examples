import argparse
import KratosMultiphysics
import KratosMultiphysics.ShallowWaterApplication

from KratosMultiphysics.ShallowWaterApplication.shallow_water_analysis import ShallowWaterAnalysis
from KratosMultiphysics.ShallowWaterApplication.utilities import benchmarking_utilities as utils

parser = argparse.ArgumentParser()
parser.add_argument('--input_filename', type=str)
parser.add_argument('--output_filename', type=str)
parser.add_argument('--analysis_label', type=str)
parser.add_argument('--remove_output', type=bool)
args = parser.parse_args()

with open("ProjectParameters.json",'r') as parameter_file:
    parameters = KratosMultiphysics.Parameters(parameter_file.read())

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
