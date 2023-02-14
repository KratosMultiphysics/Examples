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
    def ModifyInitialGeometry(self):
        super().ModifyInitialGeometry()
        self.time_snapshots = [2,4,6,8,10]
        self.selected_time_step_solution_container = []

    def FinalizeSolutionStep(self):
        super().FinalizeSolutionStep()
        time = self._GetSolver().GetComputingModelPart().ProcessInfo[KratosMultiphysics.TIME]
        if np.any(np.isclose(time, self.time_snapshots)):
            self.selected_time_step_solution_container.append(rom_testing_utilities.GetVectorNodalResults(self._GetSolver().GetComputingModelPart(), KratosMultiphysics.DISPLACEMENT))
    
    def Finalize(self):
        super().Finalize()
        np.save("ExpectedOutput.npy", np.array(self.selected_time_step_solution_container).T)
        


if __name__ == '__main__':
    
    with open("ProjectParameters.json",'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())

    model = KratosMultiphysics.Model()
    simulation = StructuralMechanicsAnalysis_FOM(model,parameters)
    simulation.Run()

    