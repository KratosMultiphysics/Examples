# Dam break against a flexible wall FSI benchmark

**Author:** [Carlos E. Flores](https://github.com/ceulogiof)

**Kratos version:** 8.1

**Source files:** [FSI-DamBreakFlexWall](https://github.com/KratosMultiphysics/Examples/tree/master/co_simulation/validation/dam_break_flex_wall/source)

## Case Specification

This is a 2D FSI simulation of the dam break against a flexible wall benchmark test, originally proposed by Walhorn et al (2005). It consists in a 2D water column inside a chamber that contains a flexible wall structure attached to the middle of the bottom wall. The main challenge of the test is that the densities of the fluid and the structure have a similar order of magnitude, leading to a strongly coupled problem in which large interactions and displacements between the two fields appear. The reference solutions have been taken from  Cerquaglia et al (2019), Meduri et al (2018) and Ryzhakov et al (2010). The following applications of Kratos are used:
* CoSimulationApplication
* PfemFluidDynamicsApplication
* StructuralMechanicsApplication
* CoSimulationApplication
* MappingApplication
* MeshingApplication
* LinearSolversApplication

The problem geometry as well as the boundary conditions are sketched below.
<p align="center">
  <img src="data/dam_break_flex_wall_geometry.png" alt="Dam break against a flexible wall benchmark geometry." style="width: 400px;"/>
</p>

Where:
* L: 0.146 _m_
* H: 0.080 _m_
* W: 0.012 _m_

For the boundary conditions, v = 0 was imposed in every wall.

A Newtonian constitutive law is considered in the fluid domain. The fluid characteristic parameters are:
* Density (&rho;): 1000 _Kg/m<sup>3</sup>_
* Kinematic viscosity (&nu;): 0.001 _m<sup>2</sup>/s_

On the other hand, a hyper elastic plane stress constitutive law with unit thickness is considered in the structure domain. The structure characteristic parameters are
* Density (&rho;): 2500 _Kg/m<sup>3</sup>_
* Elastic modulus (E):  1.00000E+06 _Pa_
* Poisson ratio (&nu;): 0.0

The time step is 0.0005 seconds, while the total simulation time is 1.0 second.

The mesh was created with the GiD meshing utility, using triangular elements for both domains, averaging 2mm in size.

## Results
The problem stated above has been solved with a mesh composed by around 300 triangular, solid, total Lagrangian elements for the structural domain. For the fluid domain, a mesh composed by around 13500 linear triangular, two-step udpated lagrangian elements have been used. The obtained velocity field, together with the deformed geometry, is shown below for t = 0.458 _s_. Besides, the obtained displacement field compared with the reference solutions is depicted as well.

<p align="center">
  <img src="data/flow_field_vel_t0.458.png" alt="Obtained velocity field (t = 0.458)." style="width: 600px;"/>
</p>

<p align="center">
  <img src="data/dam_break_flex_wall_ux.png" alt="Horizontal displacement comparison." style="width: 400px;"/>
</p>

## References
Cerquaglia, M., Thomas, D., Boman, R., Terrapon, V., and Ponthot, J.-P. (2019). A fully partitioned Lagrangian framework for FSI problems characterized by free surfaces, large solid deformations and displacements, and strong added-mass effects. _Computer Methods in Applied Mechanics and Engineering_, 348:409–442. [https://doi.org/10.1016/j.cma.2019.01.021](https://doi.org/10.1016/j.cma.2019.01.021)

Meduri, S., Cremonesi, M., Perego, U., Bettinotti, O., Kurkchubasche, A., and Oancea, V. (2018). A partitioned fully explicit lagrangian finite element method for highly nonlinear fluid-structure interaction problems. _Int. J. Numer. Meth. Engng._, 113(1):43–64. [https://doi.org/10.1002/nme.5602](https://doi.org/10.1002/nme.5602)

Ryzhakov, P. B., Rossi, R., Idelsohn, S. R., and Oñate, E. (2010). A monolithic Lagrangian approach for fluid-structure interaction problems. _Computational Mechanics_, 46(6):883–
899. [https://doi.org/10.1007/s00466-010-0522-0](https://doi.org/10.1007/s00466-010-0522-0)

Walhorn, E., Kölke, A., Hübner, B., and Dinkler, D. (2005). Fluid-structure coupling within a monolithic model involving free surface flows. _Computers & Structures_ 83, 2100–2111. [https://doi.org/10.1016/j.compstruc.2005.03.010](https://doi.org/10.1016/j.compstruc.2005.03.010)

