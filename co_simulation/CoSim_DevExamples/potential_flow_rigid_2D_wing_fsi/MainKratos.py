from __future__ import print_function, absolute_import, division #makes KratosMultiphysics backward compatible with python 2.6 and 2.7

import KratosMultiphysics
from KratosMultiphysics.CompressiblePotentialFlowApplication.potential_flow_analysis import PotentialFlowAnalysis

"""
For user-scripting it is intended that a new class is derived
from PotentialFlowAnalysis to do modifications
"""

if __name__ == "__main__":

    with open("ProjectParameters.json",'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())

    gid_output_file_name = "test_4"
    parameters["output_processes"]["gid_output"][0]["Parameters"]["output_name"].SetString(gid_output_file_name)

    model = KratosMultiphysics.Model()
    simulation = PotentialFlowAnalysis(model,parameters)
    simulation.Run()
