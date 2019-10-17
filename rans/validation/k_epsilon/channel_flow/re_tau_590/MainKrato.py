from __future__ import print_function, absolute_import, division  #makes KratosMultiphysics backward compatible with python 2.6 and 2.7

import KratosMultiphysics
from KratosMultiphysics.kratos_utilities import CheckIfApplicationsAvailable
from KratosMultiphysics.RANSModellingApplication.periodic_fluid_dynamics_analysis import PeriodicFluidDynamicsAnalysis

if __name__ == "__main__":
    if (CheckIfApplicationsAvailable("EigenSolversApplication")):
        with open("ProjectParameters_eigen_solver.json", 'r') as parameter_file:
            parameters = KratosMultiphysics.Parameters(parameter_file.read())
    else:
        KratosMultiphysics.Logger.PrintInfo("Using Kratos native direct solvers.")
        with open("ProjectParameters.json", 'r') as parameter_file:
            parameters = KratosMultiphysics.Parameters(parameter_file.read())

    model = KratosMultiphysics.Model()
    simulation = PeriodicFluidDynamicsAnalysis(model, parameters)
    simulation.Run()
