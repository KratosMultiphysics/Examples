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
import KratosMultiphysics.StructuralMechanicsApplication

if __name__ == '__main__':
    
    parameters_filename = "ProjectParametersHROM.json"
    with open(parameters_filename,'r') as parameter_file:
            parameters = KratosMultiphysics.Parameters(parameter_file.read())
    model = KratosMultiphysics.Model()
    dummy = rom_testing_utilities.SetUpSimulationInstance(model, parameters)

    class DummyAnalysis(type(dummy)):
        def ModifyInitialGeometry(cls):
            super().ModifyInitialGeometry()
            cls.write = True

        def FinalizeSolutionStep(cls):
            super().FinalizeSolutionStep()
            # if cls.write:
            #     obtained_output = rom_testing_utilities.GetVectorNodalResults(cls._GetSolver().GetComputingModelPart(), KratosMultiphysics.DISPLACEMENT)
            #     np.save("ExpectedOutput.npy", obtained_output)
            #     cls.write=False
        # Run test case
    simulation = DummyAnalysis(model, parameters)

    # Run test case
    simulation.Run()

    obtained_output = rom_testing_utilities.GetVectorNodalResults(simulation._GetSolver().GetComputingModelPart(), KratosMultiphysics.DISPLACEMENT)
    np.save("ExpectedOutputHROM.npy", obtained_output)