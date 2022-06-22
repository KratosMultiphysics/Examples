import argparse
import KratosMultiphysics
import KratosMultiphysics.ShallowWaterApplication

from KratosMultiphysics.ShallowWaterApplication.shallow_water_analysis import ShallowWaterAnalysis
from KratosMultiphysics.ShallowWaterApplication.utilities import benchmarking_utilities as utils

parser = argparse.ArgumentParser()
parser.add_argument('--rel_damping', type=float)
parser.add_argument('--rel_distance', type=float)
parser.add_argument('--output_name', type=str)
parser.add_argument('--remove_output', type=bool)
args = parser.parse_args()

with open("ProjectParameters.json",'r') as parameter_file:
    parameters = KratosMultiphysics.Parameters(parameter_file.read())

if args.rel_damping is not None:
    utils.GetProcessParameters(parameters['processes'], 'apply_absorbing_boundary_process')['relative_damping'].SetDouble(args.rel_damping)
if args.rel_distance is not None:
    utils.GetProcessParameters(parameters['processes'], 'apply_absorbing_boundary_process')['relative_distance'].SetDouble(args.rel_distance)
if args.output_name is not None:
    utils.GetProcessParameters(parameters['output_processes'], 'multiple_points_output_process')['output_file_settings']['file_name'].SetString(args.output_name)
if args.remove_output:
    utils.KeepOnlyThisProcess(parameters['output_processes'], 'multiple_points_output_process')

model = KratosMultiphysics.Model()
ShallowWaterAnalysis(model, parameters).Run()
