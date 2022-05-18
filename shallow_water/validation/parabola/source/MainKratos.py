import argparse
import KratosMultiphysics
import KratosMultiphysics.ShallowWaterApplication

from KratosMultiphysics.ShallowWaterApplication.shallow_water_analysis import ShallowWaterAnalysis
import KratosMultiphysics.ShallowWaterApplication.utilities.benchmarking_utilities as utils

parser = argparse.ArgumentParser()
mode = parser.add_mutually_exclusive_group()
mode.add_argument("-r", "--regular_analysis", action="store_const", dest="mode", const="regular_analysis", default="regular_analysis")
mode.add_argument("-c", "--convergence_analysis", action="store_const", dest="mode", const="convergence_analysis")
args = parser.parse_args()

with open("ProjectParameters.json",'r') as parameter_file:
    parameters = KratosMultiphysics.Parameters(parameter_file.read())

if args.mode == 'regular_analysis':
    model = KratosMultiphysics.Model()
    ShallowWaterAnalysis(model, parameters).Run()
else:
    meshes = [0.25, 0.1, 0.05, 0.03, 0.01]
    steps = [0.002] * len(meshes)
    steps[-1] = 0.0005
    input_base_name = 'rectangle_{}'
    output_base_name = 'parabola'
    output_base_path = '.'

    for i in range(len(meshes)):
        input_name = input_base_name.format(meshes[i])
        output_name = output_base_name.format(meshes[i])
        output_path = output_base_path.format(meshes[i])
        output_full_name = output_path + '/' + output_name
        case = parameters.Clone()
        case['solver_settings']['model_import_settings']['input_filename'].SetString(input_name)
        case['solver_settings']['time_stepping']['time_step'].SetDouble(steps[i])
        utils.GetProcessParameters(case['output_processes'], 'gid_output_process')['output_name'].SetString(output_full_name)
        utils.GetProcessParameters(case['output_processes'], 'nodes_output_process')['file_name'].SetString(output_name)
        utils.GetProcessParameters(case['output_processes'], 'nodes_output_process')['output_path'].SetString(output_path)
        model = KratosMultiphysics.Model()
        ShallowWaterAnalysis(model, case).Run()
