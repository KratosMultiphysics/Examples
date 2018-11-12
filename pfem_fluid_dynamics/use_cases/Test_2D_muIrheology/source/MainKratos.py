import KratosMultiphysics
import KratosMultiphysics.ExternalSolversApplication
import KratosMultiphysics.DelaunayMeshingApplication
import KratosMultiphysics.PfemFluidDynamicsApplication
import KratosMultiphysics.SolidMechanicsApplication

import MainFluidPFEM

model = KratosMultiphysics.Model()

MainFluidPFEM.Solution(model).Run()


