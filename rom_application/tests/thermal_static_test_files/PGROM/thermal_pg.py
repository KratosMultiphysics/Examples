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

if __name__ == '__main__':
    work_folder = ""
    parameters_filename = "ProjectParametersPGROM.json"

    with KratosUnittest.WorkFolderScope(work_folder, __file__):
        # Set up simulation
        with open(parameters_filename,'r') as parameter_file:
            parameters = KratosMultiphysics.Parameters(parameter_file.read())
        model = KratosMultiphysics.Model()
        dummy = rom_testing_utilities.SetUpSimulationInstance(model, parameters)

        class DummyAnalysis(type(dummy)):

            def InitializeSolutionStep(cls):
                super().InitializeSolutionStep()
                # condition = 2000*float(cls.time)
                # cls.project_parameters["processes"]["constraints_process_list"][0]["Parameters"]["value"].SetDouble(condition)

        # Run test case
        dummy.Run()

        obtained_output = rom_testing_utilities.GetScalarNodalResults(dummy._GetSolver().GetComputingModelPart(), KratosMultiphysics.TEMPERATURE)
        np.save("ExpectedOutputPGROM.npy", obtained_output)
