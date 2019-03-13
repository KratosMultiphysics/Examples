from __future__ import print_function, absolute_import, division #makes KratosMultiphysics backward compatible with python 2.6 and 2.7

import KratosMultiphysics
import KratosMultiphysics.FluidDynamicsApplication

from fluid_dynamics_analysis import FluidDynamicsAnalysis

import sys
import time

# Hierarchy of classes: (>> = inherits to)
# PythonSolver >> FluidSolver >> NavierStokesTwoFluidsSolver
# AnalysisStage >> FluidDynamicsAnalysis >> FluidDynamicsAnalysisWithFlush( to redefine individual functions )
class FluidDynamicsAnalysisWithFlush(FluidDynamicsAnalysis):
    # Constructor of the derived class "FluidDynamicsAnalysisWithFlush"
    def __init__(self,model,project_parameters,flush_frequency=10.0):
        super(FluidDynamicsAnalysisWithFlush,self).__init__(model,project_parameters)
        self.flush_frequency = flush_frequency
        self.last_flush = time.time()

    # Function to define the initial water body by setting a distance field
    # Negative distance value represent water
    # Positive values represent the air-filled volume
    def ModifyInitialGeometry(self):
        L = 0.614   		# Half length of water body
        H = 0.550   		# Height of the water body
        OffsetX = 2.606		# Position of the center of the water body

        # Description of the case can be found e.g. in:
        # Larese, Rossi, Onate, Idelsohn: Validation of the particle finite element method (PFEM) for simulation of free surface flow, 2008
        for node in self._GetSolver().GetComputingModelPart().Nodes:
            d_z = abs(node.Z) - H
            d_x = abs(node.X - OffsetX) - L
            distance = max(d_x,d_z)
            node.SetSolutionStepValue(KratosMultiphysics.DISTANCE, distance)

    # Extension of the function FinalizeSolutionStep() to force writing of buffered output
    def FinalizeSolutionStep(self):
        super(FluidDynamicsAnalysisWithFlush,self).FinalizeSolutionStep()

        if self.parallel_type == "OpenMP":
            now = time.time()
            if now - self.last_flush > self.flush_frequency:
                sys.stdout.flush()
                self.last_flush = now

if __name__ == "__main__":
    # Reading parameters from the *.json file
    with open("ProjectParameters.json",'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())

    # Creation of a model
    model = KratosMultiphysics.Model()

    # Generating the simulation
    simulation = FluidDynamicsAnalysisWithFlush(model,parameters)

    # Running the simulation (exact sequence of steps can be seen by following the class hierarchy)
    simulation.Run()
