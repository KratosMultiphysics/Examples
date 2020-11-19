# Convection-diffusion of a Gaussian hill problem

**Author:** [Riccardo Tosi](https://github.com/riccardotosi)

**Kratos version:** 8.0

**Source files:** [source](source)

## Case Specification

This example is taken from [Donea, J., & Huerta, A. (2003). Finite Element Methods for Flow Problems. Section 5.6.1] and adapted to run on a two-dimensional mesh. We solve the transient convection diffusion equation
<img src="https://render.githubusercontent.com/render/math?math=\frac{\partial \phi}{\partial t} %2B v \cdot  \nabla \phi %2B \phi \nabla \cdot v - \nabla \cdot k \nabla \phi = f">,
where specific initial conditions are set. We refer to the above reference for further details.

The problem is solved exploiting the **Runge-Kutta 4 time integration explicit method**, and it can be run with four different stabilizations:
* quasi-static algebraic subgrid scale (QSASGS)
* quasi-static orthogonal subgrid scale (QSOSS)
* dynamic algebraic subgrid scale (DASGS)
* dynamic orthogonal subgrid scale (DOSS)

## Results

We present the temporal evolution of <img src="https://render.githubusercontent.com/render/math?math=\phi"> for the *DOSS* case.
<p align="center">
  <img src="data/gaussian_hill_with_diffusion_finest_mesh.gif" alt="temperature" style="width: 600px;"/>
</p>

We can observe the results we obtain are consistent with both the reference [Donea, J., & Huerta, A. (2003). Finite Element Methods for Flow Problems. Section 5.6.1].

Moreover, we also compared our numerical solution against the analytical solution <img src="https://render.githubusercontent.com/render/math?math=\frac{5}{7\sigma} \exp(-(\frac{x-x_0-vt}{l\sigma})^2)">, where <img src="https://render.githubusercontent.com/render/math?math=\sigma=\sqrt{1%2B4kl^2}">, <img src="https://render.githubusercontent.com/render/math?math=x_0=\frac{2}{15}">, <img src="https://render.githubusercontent.com/render/math?math=k=\exp(-3)"> the diffusivity, <img src="https://render.githubusercontent.com/render/math?math=l=\frac{7\sqrt{2}}{300}">, <img src="https://render.githubusercontent.com/render/math?math=v=1"> the convective velocity and <img src="https://render.githubusercontent.com/render/math?math=t"> the simulation time. All physical quantities unit measures are expressed according to the Convection Diffusion application and the `materials.json` file. The <img src="https://render.githubusercontent.com/render/math?math=l^2"> norm we obtain is 0.001575 for the *DOSS* element.