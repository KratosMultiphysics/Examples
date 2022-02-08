# Cylinder on inclined plane 2D - comparison between analytical and numerical solution with MPM
**Author:** Philip Franz 

**Kratos version:** Development branch. **Expected 6.0** 

**Source files:** [rolling_cylinder_2D](https://github.com/KratosMultiphysics/Examples/tree/master/particle_mechanics/validation/rolling_cylinder/source)

## Case Specification

This is a 2D simulation of a rotating cylinder on an inclined plane. The simulation is set up according to section 4.5.2 of (Iaconeta, 2019). Linear, unstructured, triangular elements with a size of 0.01m are used to initialize the MPs. For the backgroundmesh linear, unstructured, triangular elements with a size of 0.02m are used.
However, in contrast to section 4.5.2 of (Iaconeta, 2019) the inclined plane is modelled by a line with unstructured elements with size 0.01m. On that line a non (grid) conforming Dirichlet boundary condition is imposed by using penalty augmentation based on (Chandra et al., 2021).  


The following application of Kratos is used:
- [ParticleMechanicsApplication](https://github.com/KratosMultiphysics/Kratos/tree/master/applications/ParticleMechanicsApplication)

The problem geometry as well as the boundary conditions are sketched below:

<p align="center">
  <img src="data/cylinder_on_inclined_plane.png" alt="Initial geometry and boundary conditions." width="1400" />
</p>

A hyper elastic Neo Hookean Plane strain (2D) constitutive law with unit thickness is considered with the following material parameters:
* Density (_&rho;_): 7800 Kg/m<sup>3</sup>
* Young's modulus (_E_):  200 MPa
* Poisson ratio (_&nu;_): 0.3

The time step is 0.001 seconds; the total simulation time is 1.0 seconds. The angle (_&alpha;_) of the inclined plane is 60°. The penalty-factor is 1e13. Three material points per cell are considered.

The contact between cylinder and inclined plane is modelled in the first case with the option "contact" (see line 53, file *ProjectParameters.json*) and in the second case with "slip", based on (Chandra et al., 2021).  

## Results
The solutions of the displacement- and velocity function of the above stated problem are compared with the analytical solution of a rolling cylinder on an inclined plane. 

Case 1: Contact
In this case the numerical solution of the simulation is compared to the anaylitcal solution for the displacement function of a rolling cylinder on an inclined plane.

Analytical function for the displacement in y direction: -2/6*g*sin((_&alpha;_))^2*t^2 

The following images show the results of the simulation:



Case 2: Contact
In this case the numerical solution of the simulation is compared to the anaylitcal solution for the displacement and the velocity function of a slipping cylinder on an inclined plane.

Analytical function for the velocity along the direction of the inclined plane: -g*sin((_&alpha;_))^2*t

Analytical function for the displacement in y direction: -1/2*g*sin((_&alpha;_))^2*t^2
 




## References
- Iaconeta, I. (2019). *Discrete-continuum hybrid modelling of flowing and static regimes.* (Ph.D. thesis). Universitat politècnica de Catalunya - Barcelona tech 
- Chandra, B., Singer, V., Teschemacher, T., Wüchner, R., Larese, A. (2021) *Nonconforming Dirichlet boundary conditions in implicit material point method by means of penalty augmentation*. Acta Geotech. 16, 2315–2335. https://doi.org/10.1007/s11440-020-01123-3 