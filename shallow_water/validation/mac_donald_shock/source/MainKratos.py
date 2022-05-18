import argparse
import KratosMultiphysics
import KratosMultiphysics.ShallowWaterApplication

from KratosMultiphysics.ShallowWaterApplication.shallow_water_analysis import ShallowWaterAnalysis
from KratosMultiphysics.ShallowWaterApplication.utilities import benchmarking_utilities as utils

parser = argparse.ArgumentParser()
mode = parser.add_mutually_exclusive_group()
mode.add_argument("-r", "--regular_analysis", action="store_const", dest="mode", const="regular_analysis", default="regular_analysis")
mode.add_argument("-c", "--convergence_analysis", action="store_const", dest="mode", const="convergence_analysis")
args = parser.parse_args()

with open("ProjectParameters.json",'r') as parameter_file:
    parameters = KratosMultiphysics.Parameters(parameter_file.read())

if args.mode == "regular_analysis":
    model = KratosMultiphysics.Model()
    ShallowWaterAnalysis(model, parameters).Run()
else:
    meshes = [2.0, 1.0, 0.5, 0.2, 0.1]
    steps = [0.005] * len(meshes)
    steps[-1] = 0.002
    input_base_name = 'mac_donald_{}'
    output_base_name = 'shock'
    output_base_path = '{}'
    case = parameters.Clone()
    for mesh, time_step in zip(meshes, steps):
        input_name = input_base_name.format(mesh)
        output_name = output_base_name.format(mesh)
        output_path = output_base_path.format(mesh)
        case['solver_settings']['model_import_settings']['input_filename'].SetString(input_name)
        case['solver_settings']['time_stepping']['time_step'].SetDouble(time_step)
        utils.GetProcessParameters(case['output_processes'], 'gid_output_process')['output_name'].SetString(output_path + '/' + output_name)
        utils.GetProcessParameters(case['output_processes'], 'nodes_output_process')['file_name'].SetString(output_name)
        utils.GetProcessParameters(case['output_processes'], 'nodes_output_process')['output_path'].SetString(output_path)
        model = KratosMultiphysics.Model()
        ShallowWaterAnalysis(model, parameters).Run()
