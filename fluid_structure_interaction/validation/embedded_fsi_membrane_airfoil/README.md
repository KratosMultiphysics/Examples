# Flexible membrane airfoil

**Author:** [Rubén Zorrilla](https://github.com/rubenzorrilla)

**Kratos version:** 9.5

**Source files:** [Flexible membrane airfoil](https://github.com/KratosMultiphysics/Examples/tree/master/fluid_structure_interaction/validation/embedded_fsi_membrane_airfoil/source)

## Case Specification
This example reproduces the experimental study of the aerodynamics of a simplified two-dimensional membrane airfoil described in [1]. For doing so, the embedded FSI solver for thin-walled bodies is used [2]. This makes possible to avoid the common preprocessing and mesh entangling issues arising when dealing with volume meshes around membrane-like structures.

The airfoil measures 0.15m and is placed with an angle of attack of 4º. Its material properties are a Young modulus of 250e3Pa and null Poisson ratio. The inlet characteristic velocity is 2.5833m/s and the material properties are set such that the Re is 2500. The structure and fluid density ratio is 441.75.

## Results
The fluid domain is meshed with 144k P1P1 elements. For the structure, 128 line elements implementing a simplified 2D nonlinear membrane model are used. The problem is run for 2s, with a ramp-up period of 1s, so to ensure that the steady state is reached.

The obtained fluid velocity and pressure contour fields as well as the deformed structure displacement vector field are shown below.

<p align="center">
<figure>
  <img src="data/embedded_fsi_membrane_airfoil_fluid_v.gif" alt="Fluid velocity contour field." style="width: 600px;"/>
  <figcaption>Velocity field and level set isosurface.</figcaption>
</figure>
</p>

<p align="center">
<figure>
  <img src="data/embedded_fsi_membrane_airfoil_fluid_p.gif" alt="Fluid pressure contour field." style="width: 600px;"/>
  <figcaption>Pressure field and level set isosurface.</figcaption>
</figure>
</p>

<p align="center">
<figure>
  <img src="data/embedded_fsi_membrane_airfoil_structure_u.gif" alt="Structure displacement vector field." style="width: 600px;"/>
  <figcaption>Pressure field and level set isosurface.</figcaption>
</figure>
</p>

## References
[1] P. Rojratsirikul, Z. Wang and I. Gursul, Unsteady Aerodynamics of Membrane Airfoils, AIAA 2008-613. 46th AIAA Aerospace Sciences Meeting and Exhibit, 2008 [10.2514/6.2008-613](https://doi.org/10.2514/6.2008-613).

[2] R. Zorrilla, R. Rossi, R. Wüchner and E. Oñate, An embedded Finite Element framework for the resolution of strongly coupled Fluid–Structure Interaction problems. Application to volumetric and membrane-like structures, Computer Methods in Applied Mechanics and Engineering (368), 2020 [10.1016/j.cma.2020.113179](https://doi.org/10.1016/j.cma.2020.113179)
