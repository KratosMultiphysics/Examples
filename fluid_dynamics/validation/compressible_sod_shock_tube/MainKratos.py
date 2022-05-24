#!/usr/bin/env python

import time
import sys
import pathlib

import KratosMultiphysics
import KratosMultiphysics.FluidDynamicsApplication
from KratosMultiphysics.FluidDynamicsApplication.fluid_dynamics_analysis \
    import FluidDynamicsAnalysis


def abs_filepath(relative_filepath: str) -> str:
    return str(pathlib.Path(__file__).parent.resolve()) + "/" \
        + relative_filepath


class FluidDynamicsAnalysisCompressible(FluidDynamicsAnalysis):
    """
    Modified FluidDynamicsAnalysis in order to:
    - Print at the first step
    - Force stdout to flush at regular intervals
    """

    def __init__(self, model, parameters, flush_frequency=10.0):
        super().__init__(model, parameters)
        self.flush_frequency = flush_frequency
        self.last_flush = time.time()
        sys.stdout.flush()
        self.print_count = 0

    def Initialize(self):
        super().Initialize()
        sys.stdout.flush()
        self.OutputSolutionStep()

    def OutputSolutionStep(self):
        self.Flush()
        super().OutputSolutionStep()

    def Flush(self, force=False):
        if not force and self.parallel_type != "OpenMP":
            return

        now = time.time()
        if not force and (now - self.last_flush < self.flush_frequency):
            return

        sys.stdout.flush()
        self.last_flush = now


if __name__ == "__main__":
    with open(abs_filepath("ProjectParameters.json"), 'r') as parameter_file:
        project_parameters = KratosMultiphysics.Parameters(parameter_file.read())

        global_model = KratosMultiphysics.Model()
        simulation = FluidDynamicsAnalysisCompressible(global_model, project_parameters)
        simulation.Run()
