from __future__ import absolute_import, division #makes KratosMultiphysics backward compatible with python 2.6 and 2.7

# Importing the Kratos Library
import KratosMultiphysics

# Import applications
import KratosMultiphysics.FluidDynamicsApplication
from KratosMultiphysics.FluidDynamicsApplication.fluid_dynamics_analysis import FluidDynamicsAnalysis
import KratosMultiphysics.kratos_utilities as kratos_utilities

# Avoid printing of Kratos informations
#KratosMultiphysics.Logger.GetDefaultOutput().SetSeverity(KratosMultiphysics.Logger.Severity.WARNING) # avoid printing of Kratos things

# Import packages
import numpy as np
import time
import os

class FluidDynamicsAnalysisProblemZero(FluidDynamicsAnalysis):

    def __init__(self,model,project_parameters):
        super(FluidDynamicsAnalysisProblemZero,self).__init__(model,project_parameters)

if __name__ == "__main__":
    from sys import argv

    if len(argv) > 2:
        err_msg =  'Too many input arguments!\n'
        err_msg += 'Use this script in the following way:\n'
        err_msg += '- With default parameter file (assumed to be called "ProjectParameters.json"):\n'
        err_msg += '    "python fluid_dynamics_analysis.py"\n'
        err_msg += '- With custom parameter file:\n'
        err_msg += '    "python fluid_dynamics_analysis.py <my-parameter-file>.json"\n'
        raise Exception(err_msg)

    if len(argv) == 2: # ProjectParameters is being passed from outside
        parameter_file_name = argv[1]
    else: # using default name
        parameter_file_name = "problem_settings/ProblemZeroParametersVMS.json"

    with open(parameter_file_name,'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())
    model = KratosMultiphysics.Model()

    ini_time = time.time()
    simulation = FluidDynamicsAnalysisProblemZero(model, parameters)
    simulation.Run()
    print("[TIMER] Total analysis time:", time.time()-ini_time)