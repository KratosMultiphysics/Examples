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
    parameters_filename = "ProjectParametersLSPGROM.json"

    with KratosUnittest.WorkFolderScope(work_folder, __file__):
        # Set up simulation
        with open(parameters_filename,'r') as parameter_file:
            parameters = KratosMultiphysics.Parameters(parameter_file.read())
        model = KratosMultiphysics.Model()
        dummy = rom_testing_utilities.SetUpSimulationInstance(model, parameters)

        class DummyAnalysis(type(dummy)):
            def ModifyInitialGeometry(cls):
                super().ModifyInitialGeometry()
                cls.time_snapshots = [500,1200,2500,3000,3600]
                cls.selected_time_step_solution_container = []

            def FinalizeSolutionStep(cls):
                super().FinalizeSolutionStep()
                if int(cls._GetSolver().GetComputingModelPart().ProcessInfo[KratosMultiphysics.TIME]) in cls.time_snapshots:
                    cls.selected_time_step_solution_container.append(rom_testing_utilities.GetScalarNodalResults(cls._GetSolver().GetComputingModelPart(), KratosMultiphysics.TEMPERATURE))
            
            def Finalize(cls):
                super().Finalize()
                np.save("ExpectedOutputLSPGROM.npy", np.array(cls.selected_time_step_solution_container).T)
        
        # Run test case
        simulation = DummyAnalysis(model, parameters)

        # Run test case
        simulation.Run()
