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

    def InitializeSolutionStep(self):
        super().InitializeSolutionStep()
        # condition = 2000*float(self.time)
        # self.project_parameters["processes"]["constraints_process_list"][0]["Parameters"]["value"].SetDouble(condition)
        debug = True

    def Finalize(self):
        super().Finalize()
        # if self.write_flag:
        #     obtained_output = rom_testing_utilities.GetScalarNodalResults(simulation._GetSolver().GetComputingModelPart(), KratosMultiphysics.TEMPERATURE)
        #     np.save("ExpectedOutput.npy", obtained_output)
        #     self.write_flag = False

if __name__ == '__main__':
    work_folder = ""
    parameters_filename = "ProjectParameters.json"

    with KratosUnittest.WorkFolderScope(work_folder, __file__):
        # Set up simulation
        with open(parameters_filename,'r') as parameter_file:
            parameters = KratosMultiphysics.Parameters(parameter_file.read())
        model = KratosMultiphysics.Model()
        simulation = WriteResults(model, parameters)
        simulation.write_flag = True
        # Run test case
        simulation.Run()

        obtained_output = rom_testing_utilities.GetScalarNodalResults(simulation._GetSolver().GetComputingModelPart(), KratosMultiphysics.TEMPERATURE)
        np.save("ExpectedOutput.npy", obtained_output)
