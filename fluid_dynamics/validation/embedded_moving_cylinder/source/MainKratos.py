from __future__ import print_function, absolute_import, division #makes KratosMultiphysics backward compatible with python 2.6 and 2.7

import KratosMultiphysics
from KratosMultiphysics.FluidDynamicsApplication.fluid_dynamics_analysis import FluidDynamicsAnalysis

import sys
import time
import math

class FluidDynamicsAnalysisWithFlush(FluidDynamicsAnalysis):

    def __init__(self,model,project_parameters,flush_frequency=10.0):
        super(FluidDynamicsAnalysisWithFlush,self).__init__(model,project_parameters)
        self.flush_frequency = flush_frequency
        self.last_flush = time.time()

    def FinalizeSolutionStep(self):
        super(FluidDynamicsAnalysisWithFlush,self).FinalizeSolutionStep()

        if self.parallel_type == "OpenMP":
            now = time.time()
            if now - self.last_flush > self.flush_frequency:
                sys.stdout.flush()
                self.last_flush = now

    def ModifyInitialGeometry(self):
        super(FluidDynamicsAnalysisWithFlush,self).ModifyInitialGeometry()

        # Read the cylinder geometry
        cylinder_model_part = self.model.CreateModelPart('CylinderModelPart')
        cylinder_model_part.AddNodalSolutionStepVariable(KratosMultiphysics.VELOCITY)
        cylinder_model_part.AddNodalSolutionStepVariable(KratosMultiphysics.DISPLACEMENT)
        KratosMultiphysics.ModelPartIO('cylinder', KratosMultiphysics.ModelPartIO.READ).ReadModelPart(cylinder_model_part)

    def ApplyBoundaryConditions(self):
        # Clone the cylinder solution step data
        cylinder_model_part = self.model.GetModelPart('CylinderModelPart')
        t = self._GetSolver().GetComputingModelPart().ProcessInfo[KratosMultiphysics.TIME]
        cylinder_model_part.CloneTimeStep(t)
        cylinder_model_part.ProcessInfo[KratosMultiphysics.STEP] = self._GetSolver().GetComputingModelPart().ProcessInfo[KratosMultiphysics.STEP]

        # Move the cylinder
        u_x = 0.8 * math.sin(2.0 * math.pi * (t - 0.75) / 3.0)
        v_x = (2.0 * math.pi / 3.0) * 0.8 * math.cos(2.0 * math.pi * (t - 0.75) / 3.0)
        for node in cylinder_model_part.Nodes:
            node.X = node.X0 + u_x
            node.SetSolutionStepValue(KratosMultiphysics.VELOCITY, [v_x, 0.0, 0.0])
            node.SetSolutionStepValue(KratosMultiphysics.DISPLACEMENT, [u_x, 0.0, 0.0])

        # Update the level-set function
        KratosMultiphysics.CalculateDistanceToSkinProcess2D(
            self._GetSolver().GetComputingModelPart(),
            cylinder_model_part).Execute()

        # Apply the rest of boundary conditions
        super(FluidDynamicsAnalysisWithFlush,self).ApplyBoundaryConditions()

        # Set the EMBEDDED_VELOCITY in the intersected elements
        # Note that this is done after the distance modification in the base ApplyBoundaryConditions
        for elem in self._GetSolver().GetComputingModelPart().Elements:
            n_pos = 0
            n_neg = 0
            for node in elem.GetNodes():
                if (node.GetSolutionStepValue(KratosMultiphysics.DISTANCE) < 0):
                    n_neg += 1
                else:
                    n_pos += 1
            if (n_pos != 0 and n_neg != 0):
                elem.SetValue(KratosMultiphysics.EMBEDDED_VELOCITY, [v_x, 0.0, 0.0])
            else:
                elem.SetValue(KratosMultiphysics.EMBEDDED_VELOCITY, [0.0, 0.0, 0.0])


if __name__ == "__main__":

    with open("ProjectParameters.json",'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())

    model = KratosMultiphysics.Model()
    simulation = FluidDynamicsAnalysisWithFlush(model,parameters)
    simulation.Run()
