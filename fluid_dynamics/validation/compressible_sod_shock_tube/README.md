# Sod shock tube

**Author:** [Eduard Gómez](https://github.com/EduardGomezEscandell)

**Kratos version:** 9.1

**Source files:** [Sod shock tube](https://github.com/KratosMultiphysics/Examples/tree/master/fluid_dynamics/validation/compressible_sod_shock_tube/source)

## Case Specification
This is a 2D simulation of the classical Sod shock tube benchmark, using the Euler equations.

The problem geometry consists in a rectangular domain, 1 meter long and 0.1 meters wide, with free-slip conditions on log sides and open boundaries on the sort sides. The Sod shock problem is one-dimensional, which coincides with the X-axis in this case. Hence, no variations along the Y-axis are obseeerved.

The initial condition is diferent on the left and right sides. The separation is located at x=0.5.

| Property      | Left side     | Right side    |
| ------------- | ------------- | ------------- |
| Density       | 1.0           | 0.125         |
| Pressure      | 1.0           | 0.1           |
| Velocity      | 0.0           | 0.0           |

Concerning the material, a perfect fluid with the characteristic parameters listed below is used.
* Dynamic viscosity (&mu;): 0
* Thermal conductivity (&kappa;): 0
* Specific heat (_c<sub>p</sub>_): 722.14 _J/KgK_
* Heat capacity ratio (&gamma;): 1.4

An adaptive time step strategy based on the CFL and Fourier numbers is used.

## Results
The problem is solved with a Variational Multi-Scale stabilized compressible Navier-Stokes formulation written in conservative variables (1). An explicit third order otal-variational-diminishing Runge-Kutta explicit strategy is used for the time discretization, see (2) for more details. The physics-based shock capturing technique described in (3) is also used.

The computational domain is meshed with 36k linear triangular elements. Below are three snapshots depicting the density, velocity and temperature profiles at t=0.15. This case's is interest is in the featuring of three compressible phenomena, from left to right: a rarefication, a contact discontinuity and a normal shock.

<!-- >
TODO: Change figures in this table
</!-->

<p align="center">
  <img src="data/transonic_naca_0012_mach.png" alt="Transonic flow around a NACA0012 profile Mach number field." style="width: 600px;"/>
</p>

<p align="center">
  <img src="data/transonic_naca_0012_density.png" alt="Transonic flow around a NACA0012 profile density field [Kg/m<sup>3</sup>]." style="width: 600px;"/>
</p>

<p align="center">
  <img src="data/transonic_naca_0012_shock_sensor.png" alt="Transonic flow around a NACA0012 profile shock sensor field." style="width: 600px;"/>
</p>

## References
(1) Bayona Roa, C.A., Baiges, J. and Codina, R. (2016), Variational multi-scale finite element approximation of the compressible Navier-Stokes equations, International Journal of Numerical Methods for Heat & Fluid Flow, Vol. 26 No. 3/4, pp. 1240-1271. [https://doi.org/10.1108/HFF-11-2015-0483](https://doi.org/10.1108/HFF-11-2015-0483 )

(2) Gottlieb, S., & Shu, C. W. (1998). Total variation diminishing Runge-Kutta schemes. Mathematics of computation, 67(221), 73-85.[https://doi.org/10.1090/S0025-5718-98-00913-2](https://doi.org/10.1090/S0025-5718-98-00913-2).

(3) Fernandez, P., Nguyen, C., & Peraire, J. (2018), A physics-based shock capturing method for unsteady laminar and turbulent flows. In 2018 AIAA Aerospace Sciences Meeting (p. 0062). [https://doi.org/10.2514/6.2018-0062](https://doi.org/10.2514/6.2018-0062)
