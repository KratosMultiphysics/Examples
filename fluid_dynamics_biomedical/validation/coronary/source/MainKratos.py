from __future__ import print_function, absolute_import, division #makes KratosMultiphysics backward compatible with python 2.6 and 2.7

import KratosMultiphysics
import KratosMultiphysics.FluidDynamicsApplication
import KratosMultiphysics.FluidDynamicsBiomedicalApplication
from KratosMultiphysics.FluidDynamicsApplication.fluid_dynamics_analysis import FluidDynamicsAnalysis

import sys
import math
import time

class FluidDynamicsAnalysisWithFlush(FluidDynamicsAnalysis):

    def __init__(self,model,project_parameters,flush_frequency=10.0):
        super(FluidDynamicsAnalysisWithFlush,self).__init__(model,project_parameters)
        self.flush_frequency = flush_frequency
        self.last_flush = time.time()

        time_vector=[0.000000,0.225000,0.255000,0.285000,0.315000,0.345000,0.375000,0.405000,0.435000,0.465000,0.495000,0.525000,0.555000,0.585000,0.615000,0.645000,0.675000,0.705000,0.735000,0.765000,0.795000,0.825000,0.855000,0.885000,0.915000,0.945000,0.975000,1.005000,1.035000,1.065000,1.095000,1.125000]
        flow_values_inlet=[0.000000491006,0.000000491006,0.000000553687,0.000000619851,0.000000665121,0.000000699945,0.000000697623,0.000000679051,0.000000540919,0.000000647710,0.000001154966,0.000001271044,0.000001261757,0.000001195593,0.000001144520,0.000001031925,0.000001000584,0.000000894954,0.000000914687,0.000000914687,0.000000898436,0.000000694141,0.000000665121,0.000000623334,0.000000585609,0.000000565295,0.000000542080,0.000000524668,0.000000535115,0.000000524668,0.000000515382,0.000000505322]
        data = KratosMultiphysics.Matrix(len(time_vector),2)
        for i in range(len(time_vector)):
            data[i,0] = time_vector[i]
            data[i,1] = flow_values_inlet[i]
        self.table = KratosMultiphysics.PiecewiseLinearTable(data)

    def FinalizeSolutionStep(self):
        super(FluidDynamicsAnalysisWithFlush,self).FinalizeSolutionStep()

        if self.parallel_type == "OpenMP":
            now = time.time()
            if now - self.last_flush > self.flush_frequency:
                sys.stdout.flush()
                self.last_flush = now

if __name__ == "__main__":

    with open("ProjectParameters.json",'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())

    model = KratosMultiphysics.Model()
    simulation = FluidDynamicsAnalysisWithFlush(model,parameters)
    simulation.Run()
