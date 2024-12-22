import sys
import time
import importlib

import KratosMultiphysics
import KratosMultiphysics.FluidDynamicsApplication as KratosCFD

def CreateAnalysisStageWithFlushInstance(cls, global_model, parameters):
    class AnalysisStageWithFlush(cls):

        def __init__(self, model,project_parameters, flush_frequency=10.0):
            super().__init__(model,project_parameters)
            self.flush_frequency = flush_frequency
            self.last_flush = time.time()
            sys.stdout.flush()

        def Initialize(self):
            super().Initialize()
            sys.stdout.flush()

        def ModifyAfterSolverInitialize(self):
            super().ModifyAfterSolverInitialize()

            # Initialize temperature field
            t_0 = 600.0
            for node in self.model.GetModelPart("FluidModelPart.FluidParts_Fluid").Nodes:
                node.SetSolutionStepValue(KratosMultiphysics.TEMPERATURE, 0, t_0)
                node.SetSolutionStepValue(KratosMultiphysics.TEMPERATURE, 1, t_0)
                node.SetSolutionStepValue(KratosMultiphysics.TEMPERATURE, 2, t_0)

            t_left = 960
            for node in self.model.GetModelPart("FluidModelPart.NoSlip2D_Left").Nodes:
                node.SetSolutionStepValue(KratosMultiphysics.TEMPERATURE, 0, t_left)
                node.SetSolutionStepValue(KratosMultiphysics.TEMPERATURE, 1, t_left)
                node.SetSolutionStepValue(KratosMultiphysics.TEMPERATURE, 2, t_left)

            t_right = 240
            for node in self.model.GetModelPart("FluidModelPart.NoSlip2D_Right").Nodes:
                node.SetSolutionStepValue(KratosMultiphysics.TEMPERATURE, 0, t_right)
                node.SetSolutionStepValue(KratosMultiphysics.TEMPERATURE, 1, t_right)
                node.SetSolutionStepValue(KratosMultiphysics.TEMPERATURE, 2, t_right)

        def FinalizeSolutionStep(self):
            super().FinalizeSolutionStep()

            if self.parallel_type == "OpenMP":
                now = time.time()
                if now - self.last_flush > self.flush_frequency:
                    sys.stdout.flush()
                    self.last_flush = now

    return AnalysisStageWithFlush(global_model, parameters)

if __name__ == "__main__":

    with open("ProjectParameters.json", 'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())

    analysis_stage_module_name = parameters["analysis_stage"].GetString()
    analysis_stage_class_name = analysis_stage_module_name.split('.')[-1]
    analysis_stage_class_name = ''.join(x.title() for x in analysis_stage_class_name.split('_'))

    analysis_stage_module = importlib.import_module(analysis_stage_module_name)
    analysis_stage_class = getattr(analysis_stage_module, analysis_stage_class_name)

    global_model = KratosMultiphysics.Model()
    simulation = CreateAnalysisStageWithFlushInstance(analysis_stage_class, global_model, parameters)
    simulation.Run()
