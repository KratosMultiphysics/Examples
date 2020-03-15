from __future__ import print_function, absolute_import, division #makes KratosMultiphysics backward compatible with python 2.6 and 2.7

import KratosMultiphysics
import KratosMultiphysics.FluidDynamicsApplication

from KratosMultiphysics.FluidDynamicsApplication.fluid_dynamics_analysis import FluidDynamicsAnalysis
from math import pi, cos

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
        init_h = 1.7    # height of water at rest
        wave_h = 0.8    # height of the wave

        for node in self._GetSolver().GetComputingModelPart().Nodes:
            if ( node.X < pi/2 ):
                # "inside" the region of the initial wave
                waterlevel = init_h + 0.5 * wave_h * ( cos(2.0*node.X) + 1.0 )
            else:
                # "outside" the region of the initial wave
                waterlevel = init_h

            distance = node.Y - waterlevel
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
