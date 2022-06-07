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
    modes = ['residual_viscosity','gradient_jump','flux_correction']
    labels = ['rv','gj','fc']
    meshes = [2.0, 1.0, 0.5, 0.2, 0.1]
    steps = [0.005] * len(meshes)
    steps[-1] = 0.002
    input_base_name = 'mac_donald_{}'
    for mode, label in zip(modes, labels):
        for mesh, time_step in zip(meshes, steps):
            case = parameters.Clone()
            input_name = input_base_name.format(mesh)
            case['solver_settings']['time_stepping']['automatic_time_step'].SetBool(True)
            case['solver_settings']['time_stepping']['courant_number'].SetDouble(0.5)
            case['solver_settings']['time_stepping']['time_step'].SetDouble(time_step)
            case['solver_settings']['shock_capturing_type'].SetString(mode)
            utils.GetModelerParameters(case['modelers'], 'import_mdpa_modeler')['input_filename'].SetString(input_name)
            utils.GetProcessParameters(case['output_processes'], 'convergence_output_process')['analysis_label'].SetString(label)
            utils.KeepOnlyThisProcess(case['output_processes'], 'convergence_output_process')
            model = KratosMultiphysics.Model()
            try:
                ShallowWaterAnalysis(model, case).Run()
            except RuntimeError:
                pass
