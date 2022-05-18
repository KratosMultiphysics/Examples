import numpy as np
import argparse
import KratosMultiphysics
import KratosMultiphysics.ShallowWaterApplication

from KratosMultiphysics.ShallowWaterApplication.shallow_water_analysis import ShallowWaterAnalysis
from KratosMultiphysics.ShallowWaterApplication.utilities.benchmarking_utilities import GetProcessParameters

parser = argparse.ArgumentParser()
mode = parser.add_mutually_exclusive_group()
mode.add_argument("-r", "--regular_analysis", action="store_const", dest="mode", const="regular_analysis", default="regular_analysis")
mode.add_argument("-d", "--damping_sensitivity", action="store_const", dest="mode", const="damping_sensitivity")

with open("ProjectParameters.json",'r') as parameter_file:
    parameters = KratosMultiphysics.Parameters(parameter_file.read())

args = parser.parse_args()
if args.mode == 'regular_analysis':
    model = KratosMultiphysics.Model()
    ShallowWaterAnalysis(model, parameters).Run()
else:
    output_base_name = 'time_series_{}long_{}damp'
    output_base_path = 'reflection_coefficient'

    relative_dampings = 10**np.linspace(-.5, 1, 15)
    relative_wavelengths = np.array([0.5, 0.7, 1.0, 2.0, 3.0, 5.0])

    for l, rel_dist in enumerate(relative_wavelengths):
        for d, rel_damping in enumerate(relative_dampings):
            output_name = output_base_name.format(l, d)
            output_path = output_base_path.format(l, d)
            case = parameters.Clone()
            boundary_process = GetProcessParameters(case['processes'], 'apply_absorbing_boundary_process')
            boundary_process['relative_damping'].SetDouble(rel_damping)
            boundary_process['relative_distance'].SetDouble(rel_dist)
            point_process = GetProcessParameters(case['processes'], 'multiple_points_output_process')
            point_process['output_file_settings']['file_name'].SetString(output_name)
            point_process['output_file_settings']['output_path'].SetString(output_path)
            model = KratosMultiphysics.Model()
            ShallowWaterAnalysis(model, case).Run()
