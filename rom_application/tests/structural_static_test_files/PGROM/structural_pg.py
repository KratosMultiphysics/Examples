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
    
    parameters_filename = "ProjectParametersPGROM.json"
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

        # Run test case
    simulation = DummyAnalysis(model, parameters)

    # Run test case
    simulation.Run()

    obtained_output = rom_testing_utilities.GetVectorNodalResults(simulation._GetSolver().GetComputingModelPart(), KratosMultiphysics.DISPLACEMENT)
    np.save("ExpectedOutputPGROM.npy", obtained_output)