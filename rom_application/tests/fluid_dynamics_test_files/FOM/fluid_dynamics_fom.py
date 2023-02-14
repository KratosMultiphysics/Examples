import os
import types

try:
    import numpy as np
    numpy_available = True
except:
    numpy_available = False

import KratosMultiphysics
import KratosMultiphysics.KratosUnittest as KratosUnittest
import KratosMultiphysics.kratos_utilities as kratos_utilities
import KratosMultiphysics.RomApplication.rom_testing_utilities as rom_testing_utilities
from KratosMultiphysics.FluidDynamicsApplication.fluid_dynamics_analysis import FluidDynamicsAnalysis
import KratosMultiphysics.RomApplication.rom_testing_utilities as rom_testing_utilities

class WriteResults(FluidDynamicsAnalysis):

    def ModifyInitialGeometry(self):
        super().ModifyInitialGeometry()
        self.selected_time_step_solution_container = []

    def FinalizeSolutionStep(self):
        super().FinalizeSolutionStep()
        variables_array = [KratosMultiphysics.VELOCITY_X, KratosMultiphysics.VELOCITY_Y, KratosMultiphysics.PRESSURE]
        array_of_results = rom_testing_utilities.GetNodalResults(self._solver.GetComputingModelPart(), variables_array)
        self.selected_time_step_solution_container.append(array_of_results)

    def Finalize(self):
        super().Finalize()
        np.save("ExpectedOutput.npy", np.array(self.selected_time_step_solution_container).T)

if __name__ == '__main__':
    work_folder = ""
    parameters_filename = "ProjectParameters.json"

    with KratosUnittest.WorkFolderScope(work_folder, __file__):
        # Set up simulation
        with open(parameters_filename,'r') as parameter_file:
            parameters = KratosMultiphysics.Parameters(parameter_file.read())
        model = KratosMultiphysics.Model()
        simulation = WriteResults(model, parameters)

        # Run test case
        simulation.Run()
