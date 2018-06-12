# Eigenvalue Computation for a cantilever beam

**Author:** Philipp Bucher

**Kratos version:** 6.0

**Source files:** [Beam Eigenvalues](https://github.com/KratosMultiphysics/Examples/tree/master/structural_mechanics/validation/beam_eigenvalue_analysis/source)

## Case Specification

This simple example shows how the eigenvalues (Eigenfrequencies and Eigenmodes) of a cantilever beam can be computed.

The properties of the beam can be seen in the [Materials file](https://github.com/KratosMultiphysics/Examples/tree/master/structural_mechanics/validation/beam_eigenvalue_analysis/source/StructuralMaterials.json)

Here we are only interested in the first three bending modes, for which we can calculate the analytical solution with ([source](http://me-lrt.de/eigenfrequenzen-eigenformen-beim-balken)):

f<sub>i</sub> = _&lambda;<sub>i</sub>/(2 &pi; L<sup>2</sup>)_ (_EI/&rho;A_)<sup>_1/2_</sup>

with lambda for the first eigenfrequencies being:
- &lambda;<sub>1</sub> = 1.875
- &lambda;<sub>2</sub> = 4.694
- &lambda;<sub>3</sub> = 7.855

Using the specified properties we obtain for the first three bending modes:
- f<sub>1</sub> = 0.5595 Hz
- f<sub>2</sub> = 3.5068 Hz
- f<sub>3</sub> = 9.82 Hz

The results obtained with Kratos are :
- f<sub>1</sub> = 0.5596 Hz
- f<sub>2</sub> = 3.5063 Hz
- f<sub>3</sub> = 9.81685 Hz

The corresponding mode-shapes are shown below:

![Mode 1.](data/Mode_1.png)
First Bending Mode

![Mode 2.](data/Mode_2.png)
Second Bending Mode

![Mode 3.](data/Mode_3.png)
Third Bending Mode


