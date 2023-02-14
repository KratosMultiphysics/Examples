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
from KratosMultiphysics.StructuralMechanicsApplication.structural_mechanics_analysis import StructuralMechanicsAnalysis
from KratosMultiphysics.RomApplication.structural_mechanics_analysis_rom import StructuralMechanicsAnalysisROM

class StructuralMechanicsAnalysis_FOM(StructuralMechanicsAnalysis):
    def __init__(self, model, project_parameters):
        super().__init__(model, project_parameters)
        self.write = True

    def FinalizeSolutionStep(self):
        super().FinalizeSolutionStep()
        if self.write:
            obtained_output = rom_testing_utilities.GetVectorNodalResults(self._GetSolver().GetComputingModelPart(), KratosMultiphysics.DISPLACEMENT)
            np.save("ExpectedOutput.npy", obtained_output)
            self.write=False


if __name__ == '__main__':
    
    with open("ProjectParameters.json",'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())

    model = KratosMultiphysics.Model()
    simulation = StructuralMechanicsAnalysis_FOM(model,parameters)
    simulation.Run()

    obtained_output = rom_testing_utilities.GetVectorNodalResults(simulation._GetSolver().GetComputingModelPart(), KratosMultiphysics.DISPLACEMENT)
    np.save("ExpectedOutput.npy", obtained_output)

    