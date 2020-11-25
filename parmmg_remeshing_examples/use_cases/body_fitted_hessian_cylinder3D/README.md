# Body-fitted cylinder 3D with MPI hessian refinement

**Author:** Marc Núñez Corbacho

**Kratos version:** 8.1

**Source files:** [MPI Body-fitted cylinder 3D](https://github.com/KratosMultiphysics/Examples/tree/master/parmmg_remeshing_examples/use_cases/body_fitted_hessian_cylinder3D/source)


## Case Specification

In this test case,

The following applications of Kratos are used:
- *FluidDynamicsApplication* to solve the physical problem
- *StatisticsApplication* to compute statistical quantities of the flow
- *MeshingApplication* with the *MMG* and *ParMMG* module
- *MappingApplication* to perform the interpolation across different levels of refinement

This test case solves and remeshes and MPI parallel fluid dynamic problem iteratively using ParMMG. The number of iterations are fixed to 4 as showcase but, can they can be changed in the RemeshingParameters.json

Radius cylinder = 0.1 m
Box = 1 m x 1 m x 5 m