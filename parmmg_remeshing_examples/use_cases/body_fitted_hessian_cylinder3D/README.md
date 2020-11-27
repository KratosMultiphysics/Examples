# Body-fitted cylinder 3D with MPI hessian refinement

**Author:** Marc Núñez Corbacho

**Kratos version:** 8.1     

**MMG version:** 5.5.2

**ParMMG version:** 1.3.0

**Source files:** [MPI Body-fitted cylinder 3D](https://github.com/KratosMultiphysics/Examples/tree/master/parmmg_remeshing_examples/use_cases/body_fitted_hessian_cylinder3D/source)

**Application dependencies:** `FluidDynamicsApplication`, `LinearSolversApplications`, `MappingApplication`, `MeshingApplication`, `MetisApplication`,  `StatisticsApplication`, `TrilinosApplication`

To run this example execute:

    export OMP_NUM_THREADS=1
    mpirun -n 8 python3 MainKratos.py
## Case Specification

This test case solves and remeshes and MPI parallel fluid dynamic problem iteratively using ParMMG. The number of iterations are fixed to 4 as showcase but, can they can be changed in the RemeshingParameters.json

![initial](data/cylinder_initial.png)
![final](data/cylinder_remeshed.png)
