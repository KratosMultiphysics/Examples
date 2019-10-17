import KratosMultiphysics as km
from KratosMultiphysics.FluidDynamicsApplication.fluid_dynamics_analysis import FluidDynamicsAnalysis
import sys

if len(sys.argv) < 2:
    print("Please provide a ProjectParameters json file")
    sys.exit(-1)

parameters = km.Parameters(r'''{}''')

with open(sys.argv[1],'r') as adjoint_parameter_file:
    parameters.AddValue("primal_settings", km.Parameters(adjoint_parameter_file.read()))

model = km.Model()

cfd_model = km.Model()
cfd_simulation = FluidDynamicsAnalysis(cfd_model,parameters["primal_settings"])
cfd_simulation.Run()
