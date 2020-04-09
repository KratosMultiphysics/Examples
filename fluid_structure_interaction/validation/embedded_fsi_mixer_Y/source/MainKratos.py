from __future__ import print_function, absolute_import, division #makes KratosMultiphysics backward compatible with python 2.6 and 2.7

import KratosMultiphysics
import KratosMultiphysics.FSIApplication

from KratosMultiphysics.FSIApplication.fsi_analysis import FSIAnalysis

import sys
import time
import numpy

class FSIAnalysisWithFlush(FSIAnalysis):

    def __init__(self, model, project_parameters, flush_frequency=10.0):
        super(FSIAnalysisWithFlush,self).__init__(model, project_parameters)
        self.flush_frequency = flush_frequency
        self.last_flush = time.time()

    def ApplyBoundaryConditions(self):
        super(FSIAnalysisWithFlush,self).ApplyBoundaryConditions()

        model_part = self.model.GetModelPart("Structure.DISPLACEMENT_DisplacementBC")
        time = model_part.ProcessInfo[KratosMultiphysics.TIME]
        tol_zero = 1.0e-12
        if (numpy.trunc(time // (2.0 * numpy.pi)) % 2) <  tol_zero:
            w = 1.0
        else:
            w = -1.0
        inc_tetha = w * time
        disp = KratosMultiphysics.Vector(3)
        disp[2] = 0.0
        for node in model_part.Nodes:
            tetha_0 = numpy.arctan2(node.Y0, node.X0)
            rad_0 = numpy.sqrt(node.X0**2 + node.Y0**2)
            tetha = tetha_0 + inc_tetha
            disp[0] = rad_0 * numpy.cos(tetha) - node.X0
            disp[1] = rad_0 * numpy.sin(tetha) - node.Y0
            node.Fix(KratosMultiphysics.DISPLACEMENT_X)
            node.Fix(KratosMultiphysics.DISPLACEMENT_Y)
            node.SetSolutionStepValue(KratosMultiphysics.DISPLACEMENT, 0, disp)

    def FinalizeSolutionStep(self):
        super(FSIAnalysisWithFlush,self).FinalizeSolutionStep()

        if self.parallel_type == "OpenMP":
            now = time.time()
            if now - self.last_flush > self.flush_frequency:
                sys.stdout.flush()
                self.last_flush = now

if __name__ == "__main__":

    with open("ProjectParameters.json",'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())

    model = KratosMultiphysics.Model()
    simulation = FSIAnalysisWithFlush(model, parameters)
    simulation.Run()
