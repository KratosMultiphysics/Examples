# Space and time convergence tests

**Author:** [Riccardo Tosi](https://github.com/riccardotosi)

**Kratos version:** 9.0

**Source files:** [section 2.7 of [1]](https://github.com/KratosMultiphysics/Documentation/blob/master/Resources_files/convection_diffusion_explicit_elements/Eulerian_convection_diffusion_explicit_element.pdf)

## Space convergence

We solve the transient convection diffusion equation
<img src="https://render.githubusercontent.com/render/math?math=\frac{\partial \phi}{\partial t} %2B v \cdot  \nabla \phi %2B \phi \nabla \cdot v - \nabla \cdot k \nabla \phi = f"> and validate its reference implementation. We refer to section 2.7.1 of [1] for details.

We validate the implementation by computing the <img src="https://render.githubusercontent.com/render/math?math=l^2"> norm of the error as <img src="https://render.githubusercontent.com/render/math?math=\varepsilon = \sqrt{\int_{\Omega} (\phi - \phi_h)^2 }">, where <img src="https://render.githubusercontent.com/render/math?math=h"> is the mesh size, <img src="https://render.githubusercontent.com/render/math?math=\phi"> and <img src="https://render.githubusercontent.com/render/math?math=\phi_h"> are the analytic and FEM solutions, respectively.

<p align="center">
  <img src="convergence_error_convection_diffusion_explicit_solution.jpg"alt="velocity" style="width: 500px;"/>
</p>

The figure shows that the error <img src="https://render.githubusercontent.com/render/math?math=\varepsilon"> converges as expected for both quasi-static ASGS and quasi-static OSS.

## Time convergence

We solve the transient convection diffusion equation
<img src="https://render.githubusercontent.com/render/math?math=\frac{\partial \phi}{\partial t} %2B v \cdot  \nabla \phi %2B \phi \nabla \cdot v - \nabla \cdot k \nabla \phi = f"> and validate its reference implementation. We refer to section 2.7.2 of [1] for details.

The analytic solution at time <img src="https://render.githubusercontent.com/render/math?math=t"> is <img src="https://render.githubusercontent.com/render/math?math=\phi(t) = x - \sin(t)">. Therefore, it is possible to compute the <img src="https://render.githubusercontent.com/render/math?math=l^2"> norm of the error as
<img src="https://render.githubusercontent.com/render/math?math=\varepsilon = \sqrt{\int_{\Omega} (\phi - \phi_h)^2 }">, where <img src="https://render.githubusercontent.com/render/math?math=h"> is the mesh size, <img src="https://render.githubusercontent.com/render/math?math=\phi"> and <img src="https://render.githubusercontent.com/render/math?math=\phi_h"> are the analytic and FEM solutions, respectively. It is expected to obtain an order four accuracy for the Runge-Kutta 4 time integration scheme.

<p align="center">
  <img src="convergence_error_time_convection_diffusion_bar.jpg"alt="velocity" style="width: 500px;"/>
</p>

The figure shows that the time accuracy is of order four, as expected.


## References

[1] Tosi, R. (2020). Eulerian convection diffusion explicit elements (p. 27). p. 27. Retrieved from https://github.com/KratosMultiphysics/Documentation/blob/master/Resources_files/convection_diffusion_explicit_elements/Eulerian_convection_diffusion_explicit_element.pdf