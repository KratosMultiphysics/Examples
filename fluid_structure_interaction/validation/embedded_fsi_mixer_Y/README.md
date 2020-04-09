# Mixer with flexible blades

**Author:** [Rubén Zorrilla](https://github.com/rubenzorrilla)

**Kratos version:** 7.1

**Source files:** [Mixer with flexible blades](https://github.com/KratosMultiphysics/Examples/tree/master/fluid_structure_interaction/validation/embedded_fsi_mixer_Y/source)

## Case Specification
This example is specifically conceived to prove the extended scope of applicatoin of embedded mesh methods. Hence, it involves extremely large rotations, which would be impossible to solve by using a body fitted ALE based approach.

The problem is set up as a 2D idealization of a turbine mixer with clockwise-anticlockwise alternate rotation. The problem geometry is a unit diameter circle with three embedded flexible blades. An imposed rotation is enforced in the blades axis to emulate the spin of the rotor. Such rotation changes the direction (anticlockwise to clockwise and viceversa) after More details on the dimensions, material settings and boundary conditions can be found in [not available yet](link_to_article_here).

## Results
The fluid domain is meshed with a 45 and 540 radial and perimeter subdivisions Q1P1 elements centered structured mesh. Each one of the flexible blades is meshed with an 8x39 subdivisions structured mesh made with Total Lagrangian quadrilateral elements. The problem is run for 20s so three complete rotations (anticlockwise - clockwise - anticlockwise) are simulated.

The obtained velocity and pressure fields, together with the level set zero isosurface representing the deformed geometry, are shown below.

<p align="center">
  <img src="data/embedded_fsi_mixer_Y_v.gif" alt="Velocity field and level set isosurface." style="width: 600px;"/>
  <figcaption>"{{"Velocity field and level set isosurface.}}"</figcaption>
</p>

<p align="center">
  <img src="data/embedded_fsi_mixer_Y_p.gif" alt="Pressure field and level set isosurface." style="width: 600px;"/>
  <figcaption>"{{Pressure field and level set isosurface.}}"</figcaption>
</p>

## References
(references not available yet)
