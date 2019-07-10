# Example of plasticity - Tensile test

**Author:** Vicente Mataix Ferrándiz - Alejandro Cornejo Velázquez

**Kratos version:** Current Head

**Source files:** [Tensile test](https://github.com/KratosMultiphysics/Examples/tree/periodic_bc_examples/structural_mechanics/use_cases/tensile_test_example/source)

## Problem definition

The problem consists on a [tensile test](https://en.wikipedia.org/wiki/Tensile_testing).  Three different meshes have been created, in order to validate the computation of the internal energy dissipation, whcih depends on the element length.

- The hexahedra mesh:

<img src="data/hexa_mesh.png" width="600">

- The tetrahedra mesh:

<img src="data/tetra_mesh.png" width="600">

- The wedge mesh:

<img src="data/wedge_mesh.png" width="600">

## Results

The plastic dissipation at t=20s.

<img src="data/plastic_dissipation_20.png" width="600">

The whole animation:

<img src="data/animation.gif" width="600">


