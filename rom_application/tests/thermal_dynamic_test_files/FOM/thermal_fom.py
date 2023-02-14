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
from  KratosMultiphysics.ConvectionDiffusionApplication.convection_diffusion_analysis import ConvectionDiffusionAnalysis
import KratosMultiphysics.RomApplication.rom_testing_utilities as rom_testing_utilities

class WriteResults(ConvectionDiffusionAnalysis):

    def ModifyInitialGeometry(self):
        super().ModifyInitialGeometry()
        self.time_snapshots = [500,1200,2500,3000,3600]
        self.selected_time_step_solution_container = []

    def FinalizeSolutionStep(self):
        super().FinalizeSolutionStep()
        if int(self._GetSolver().GetComputingModelPart().ProcessInfo[KratosMultiphysics.TIME]) in self.time_snapshots:
            self.selected_time_step_solution_container.append(rom_testing_utilities.GetScalarNodalResults(self._GetSolver().GetComputingModelPart(), KratosMultiphysics.TEMPERATURE))
    
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
