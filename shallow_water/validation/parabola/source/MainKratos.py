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
    modes = ['residual_viscosity','gradient_jump','flux_correction']
    labels = ['rv','gj','fc']
    meshes = [0.25, 0.1, 0.05, 0.03, 0.01]
    steps = [0.002] * len(meshes)
    steps[-1] = 0.0005
    input_base_name = 'rectangle_{}'
    output_base_name = 'parabola'

    for mode, label in zip(modes, labels):
        for mesh, step in zip(meshes, steps):
            input_name = input_base_name.format(mesh)
            output_name = output_base_name.format(mesh)
            case = parameters.Clone()
            case['solver_settings']['time_stepping']['automatic_time_step'].SetBool(False)
            case['solver_settings']['time_stepping']['courant_number'].SetDouble(0.5)
            case['solver_settings']['time_stepping']['time_step'].SetDouble(step)
            case['solver_settings']['shock_capturing_type'].SetString(mode)
            utils.GetModelerParameters(case['modelers'], 'import_mdpa_modeler')['input_filename'].SetString(input_name)
            utils.GetProcessParameters(case['output_processes'], 'convergence_output_process')['analysis_label'].SetString(label)
            utils.KeepOnlyThisProcess(case['output_processes'], 'convergence_output_process')
            model = KratosMultiphysics.Model()
            ShallowWaterAnalysis(model, case).Run()
