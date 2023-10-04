# Example of eigenvalue analysis - Anoeta stadium truss

**Author:** Jon Arambarri Rumayor - Rubén Zorrilla Martínez

**Kratos version:** Current Head

**Source files:** [Anoeta stadium truss eigenvalue analysis](https://github.com/KratosMultiphysics/Examples/tree/master/structural_mechanics/use_cases/anoeta_stadium_truss_eigenvalue_analysis/source)

## Problem definition

This example presents an eigenvalue analysis of the [Anoeta stadium](https://en.wikipedia.org/wiki/Anoeta_Stadium) roof structure.
More specifically, the example focuses on the truss structure that supports the plastic canopy that covers the tiers (see the figures below).

<p align="center">
  <img src="https://github.com/KratosMultiphysics/Examples/blob/master/structural_mechanics/use_cases/anoeta_stadium_truss_eigenvalue_analysis/data/anoeta_truss_1.png?raw=true" alt="Anoeta stadium [1]" style="width: 600px;"/>
</p>

<p align="center">
  <img src="https://github.com/KratosMultiphysics/Examples/blob/master/structural_mechanics/use_cases/anoeta_stadium_truss_eigenvalue_analysis/data/anoeta_truss_2.jpeg?raw=true" alt="Anoeta stadium [2]" style="width: 600px;"/>
</p>

The roof structure is conformed by two curved trusses of almost 200m aligned with the touch lines and two straight trusses of around 155m aligned with the goal lines.
The side trusses intersect the goal ones so the structure can be defined a spatial 3D truss.
While different cross-section areas are used, all the members are made of the same steel, which material properties are
- $E = 206.9$ GPa
- $\rho = 7850.0$ Kg/m^3^

Each member is meshed with a single truss element.
On top of these, nodal concentrated mass elements have been added in addition to the truss ones (see the [MainKratos.py](https://github.com/KratosMultiphysics/Examples/tree/master/structural_mechanics/use_cases/anoeta_stadium_truss_eigenvalue_analysis/source/MainKratos.py) file) in order to account for the weight of the plastic canopy.

Current settings include the calculation of the first five eigenvalues.
If a different number is required, modify the *number_of_eigenvalues* field in the [ProjectParameters.json](https://github.com/KratosMultiphysics/Examples/tree/master/structural_mechanics/use_cases/anoeta_stadium_truss_eigenvalue_analysis/source/ProjectParameters.json).
Last but not least, it is important to mention that the use of the elimination builder and solver needs to be activated to avoid the singularity of the eigenvalue problem by keeping *use_block_builder* option as false in the builder and solver settings section.

## Results

By running the [MainKratos.py](https://github.com/KratosMultiphysics/Examples/tree/master/structural_mechanics/use_cases/anoeta_stadium_truss_eigenvalue_analysis/source/MainKratos.py) script the terminal outputs the fist five eigenvalues, which value is

- $\lambda_{1} = 49.6942$
- $\lambda_{2} = 54.461$
- $\lambda_{3} = 66.1036$
- $\lambda_{4} = 96.0785$
- $\lambda_{5} = 112.096$

corresponding to the frequencies

- $\f_{1} = 1.3813$ Hz
- $\f_{2} = 1.4374$ Hz
- $\f_{3} = 1.6349$ Hz
- $\f_{4} = 2.012$ Hz
- $\f_{5} = 2.0932$ Hz

Complementary, a folder with the postprocess of the eigenmodes is also created.
The animation of the first three ones is shown below.

<p align="center">
  <img src="https://github.com/KratosMultiphysics/Examples/blob/master/structural_mechanics/use_cases/anoeta_stadium_truss_eigenvalue_analysis/data/anoeta_stadium_truss_eigenmode_1?raw=true" alt="1st eigenmode animation." style="width: 600px;"/>
</p>

<p align="center">
  <img src="https://github.com/KratosMultiphysics/Examples/blob/master/structural_mechanics/use_cases/anoeta_stadium_truss_eigenvalue_analysis/data/anoeta_stadium_truss_eigenmode_2?raw=true" alt="2st eigenmode animation." style="width: 600px;"/>
</p>

<p align="center">
  <img src="https://github.com/KratosMultiphysics/Examples/blob/master/structural_mechanics/use_cases/anoeta_stadium_truss_eigenvalue_analysis/data/anoeta_stadium_truss_eigenmode_3?raw=true" alt="3st eigenmode animation." style="width: 600px;"/>
</p>

## References
[1] “Real Sociedad Amplía Los Derechos de Explotación de Anoeta Hasta 2074.” Palco23, Palco23, 17 Feb. 2022, www.palco23.com/clubes/real-sociedad-amplia-los-derechos-de-explotacion-de-anoeta-hasta-2074.

[2] “La Real Sociedad Amplía El Derecho de Explotación de Anoeta Hasta 2074.” 2Playbook, 16 Feb. 2022, www.2playbook.com/clubes/real-sociedad-amplia-derecho-explotacion-anoeta-hasta-2074_6946_102.html. Accessed 4 Oct. 2023.



