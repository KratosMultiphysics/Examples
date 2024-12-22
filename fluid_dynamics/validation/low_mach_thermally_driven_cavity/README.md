# Low Mach thermally driven cavity

**Author:** [Rubén Zorrilla](https://github.com/rubenzorrilla)

**Kratos version:** 10.0

**Source files:** [Low Mach thermally driven cavity](https://github.com/KratosMultiphysics/Examples/tree/master/fluid_dynamics/validation/low_mach_thermally_driven_cavity/source)

## Case Specification
This example solves the well-known thermally driven cavity flow using a low Mach approximation compressible Navier-Stokes solver.

The problem geometry consists in a 1 x 1 m cavity. No-slip boundary conditions are imposed in all the cavity walls. The initial temperature is 600 ºK. The left wall temperature is set to 960 ºK while the right one is set to 240 ºK. Adiabatic conditions are weakly enforced in top and bottom walls. Pressure is fixed to zero in the top right corner. The fluid is initially at rest so the fluid flow is induced by the thermal effect only. The initial thermodinamic pressure is 101325.0 _Pa_. Gravity (body force) is set to 2.40690342 _m/s<sup>2</sup>_ Note that the material and boundary conditions are set such that the Prandtl number is 0.71 and the Rayleight number is 10<sup>6</sup>.

Concerning the material, a Newtonian fluid with the characteristic parameters listed below is used.
* Dynamic viscosity (&mu;): 1e-03 _Kg/m·s_
* Thermal conductivity (&kappa;): 1.41479 _Kg·m/s<sup>3</sup>·K_
* Specific heat (c<sub>p<{/sub}>): 1.0045e3 _J/Kg·K_
* Heat capacity ratio (&gamma;): 1.4

The time step is 0.25 seconds, while the total simulation time is 30.0 seconds, which is enough to reach an (almost) steady state solution.

## Results
The problem is solved using an ASGS stabilised monolithic formulation. A 50x50 divisions structured mesh made up with linear quadrilateral elements is used.

<p align="center">
  <img src="data/low_mach_thermally_driven_cavity_p.gif" alt="Low Mach thermally driven cavity pressure field [Pa]." style="width: 600px;"/>
</p>

<p align="center">
  <img src="data/low_mach_thermally_driven_cavity_v.gif" alt="Low Mach thermally driven cavity velocity field [m/s]." style="width: 600px;"/>
</p>

<p align="center">
  <img src="data/low_mach_thermally_driven_cavity_t.gif" alt="Low Mach thermally driven cavity temperature field [K]." style="width: 600px;"/>
</p>

<p align="center">
  <img src="data/low_mach_thermally_driven_cavity_rho.gif" alt="Low Mach thermally driven cavity density field [Kg/m<sup>3</sup>]." style="width: 600px;"/>
</p>

