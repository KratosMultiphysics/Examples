import time
import sys
import os
import pathlib
import math

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
    - Print when T<0
    - Terminate simulation when T<0
    - Force stdout to flush at regular intervals
    """

    def __init__(self, model, parameters, flush_frequency=10.0):
        super().__init__(model, parameters)
        self.flush_frequency = flush_frequency
        self.last_flush = time.time()
        sys.stdout.flush()

        self.print_count = 0
        self.negative_temp = False

    @classmethod
    def distance_to_corner(cls, u: KratosMultiphysics.Node):
        return (u.X - 0.6)**2 + (u.Y - 0.0)**2 + (u.Y - 0.0)**2

    def _find_lower_corner_node(self):
        eps_2 = 1e-16
        for node in self._GetSolver().GetComputingModelPart().Nodes:
            if self.distance_to_corner(node) < eps_2:
                self._lower_corner_node = node.Id
                KratosMultiphysics.Logger.Print(f"Lower corner node has ID: {self._lower_corner_node}")
                return
        raise RuntimeError("Lower corner node not found")

    def Initialize(self):
        super().Initialize()
        sys.stdout.flush()
        self._find_lower_corner_node()

        self.OutputSolutionStep()

    def InitializeSolutionStep(self):
        node = self._GetSolver().GetComputingModelPart().GetNode(self._lower_corner_node)
        node.SetSolutionStepValue(KratosMultiphysics.MOMENTUM_X, 0.0)
        node.SetSolutionStepValue(KratosMultiphysics.MOMENTUM_Y, 0.0)
        super().InitializeSolutionStep()

    def FinalizeSolutionStep(self):
        """This function performs all the required operations that should
        be executed (for each step) AFTER solving the solution step.
        """

        super().FinalizeSolutionStep()
        self.negative_temp = not self.TemperatureIsPositive()

    def OutputSolutionStep(self):
        """This function printes / writes output files after the solution
        of a step
        """
        self.Flush()
        super().OutputSolutionStep()

    def KeepAdvancingSolutionLoop(self):
        """This function specifies the stopping criteria for breaking the
        solution loop. It can be overridden by derived classes
        """
        if self.negative_temp:
            return False

        return super().KeepAdvancingSolutionLoop()

    def TemperatureIsPositive(self):
        "Checks if the temperature is a positive number at every node"
        for node in self._GetSolver().GetComputingModelPart().Nodes:
            T = node.GetSolutionStepValue(KratosMultiphysics.TEMPERATURE)
            if T < 0.0:
                KratosMultiphysics.Logger.Print("Negative temperature in node with ID: %d" % node.Id)
                return False
            if math.isnan(T):
                KratosMultiphysics.Logger.Print("NaN temperature in node with ID: %d" % node.Id)
                return False
            if math.isinf(T):
                KratosMultiphysics.Logger.Print("Infinite temperature in node with ID: %d" % node.Id)
                return False
        return True

    def Flush(self):
        if self.parallel_type == "OpenMP":
            now = time.time()
            if now - self.last_flush > self.flush_frequency:
                KratosMultiphysics.Logger.Flush()
                sys.stdout.flush()
                self.last_flush = now


if __name__ == "__main__":
    with open(abs_filepath("ProjectParameters.json"), 'r') as parameter_file:
        project_parameters = KratosMultiphysics.Parameters(parameter_file.read())
        global_model = KratosMultiphysics.Model()
        simulation = FluidDynamicsAnalysisCompressible(global_model, project_parameters)
        simulation.Run()
