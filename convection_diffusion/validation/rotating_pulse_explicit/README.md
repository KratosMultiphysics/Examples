# Transient rotating pulse problem

**Author:** [Riccardo Tosi](https://github.com/riccardotosi)

**Kratos version:** 8.0

**Source files:** [source](source)

## Case Specification

This example is taken from [Donea, J., & Huerta, A. (2003). Finite Element Methods for Flow Problems. Section 5.6.2]. We solve the transient convection diffusion equation
<img src="https://render.githubusercontent.com/render/math?math=\frac{\partial \phi}{\partial t} %2B v \cdot  \nabla \phi %2B \phi \nabla \cdot v - \nabla \cdot k \nabla \phi = f">, where null Dirichlet boundary condition and null initial conditions are set. We refer to the above reference for further details.

Citing [Donea, J., & Huerta, A. (2003). Finite Element Methods for Flow Problems. Section 5.6.2] this problem requires *accurate transport of the unknown and boundary layers appear in the solution due to the Dirichlet boundary conditions. Therefore, high-order time-stepping schemes and stabilized formulations are needed in order to obtain an accurate solution*.

The problem is solved exploiting the **Runge-Kutta 4 time integration explicit method**, and it can be run with four different stabilizations:
* quasi-static algebraic subgrid scale (QSASGS)
* quasi-static orthogonal subgrid scale (QSOSS)
* dynamic algebraic subgrid scale (DASGS)
* dynamic orthogonal subgrid scale (DOSS)

## Results

We present the temporal evolution of <img src="https://render.githubusercontent.com/render/math?math=\phi"> for the *DOSS* case.
<p align="center">
  <img src="data/transient_rotating_pulse.gif" alt="temperature" style="width: 600px;"/>
</p>

We can observe that the results we obtain are consistent with the reference [Donea, J., & Huerta, A. (2003). Finite Element Methods for Flow Problems. Section 5.6.2].