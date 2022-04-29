import argparse
import KratosMultiphysics
import KratosMultiphysics.ShallowWaterApplication

from KratosMultiphysics.ShallowWaterApplication.shallow_water_analysis import ShallowWaterAnalysis
import KratosMultiphysics.ShallowWaterApplication.benchmarks.tools.benchmarking_utilities as utils

from numpy import linspace, array

parser = argparse.ArgumentParser()
mode = parser.add_mutually_exclusive_group()
mode.add_argument("-r", "--regular_analysis", action="store_const", dest="mode", const="regular_analysis", default="regular_analysis")
mode.add_argument("-d", "--damping_sensitivity", action="store_const", dest="mode", const="damping_sensitivity")
args = parser.parse_args()

with open("ProjectParameters.json",'r') as parameter_file:
    parameters = KratosMultiphysics.Parameters(parameter_file.read())

model = KratosMultiphysics.Model()

if args.mode == 'regular_analysis':
    ShallowWaterAnalysis(model, parameters).Run()
else:
    output_base_name = 'reflection_coefficient_{:.1f}'
    output_base_path = ''

    relative_dampings = 10**linspace(-1, 2, 31)
    relative_wavelengths = array([1.0, 1.5, 2.0, 4.0])

    for rel_dist in relative_wavelengths:
        output_name = output_base_name.format(rel_dist)
        output_path = output_base_path.format(rel_dist)
        for rel_damping in relative_dampings:
            case = parameters.Clone()
            utils.GetProcessParameters(case['processes'], 'apply_absorbing_boundary_process')['relative_damping'].SetDouble(rel_damping)
            utils.GetProcessParameters(case['processes'], 'apply_absorbing_boundary_process')['relative_distance'].SetDouble(rel_dist)
            utils.GetProcessParameters(case['output_processes'], 'compute_reflection_coefficient_process')['file_name'].SetString(output_name)
            ShallowWaterAnalysis(model, case).Run()
