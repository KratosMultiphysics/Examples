# Woodward-Colella Mach 3 step

**Author:** [Eduard Gómez](https://github.com/EduardGomezEscandell)

**Kratos version:** 9.1

**Source files:** [Woodward and Colella's step](https://github.com/KratosMultiphysics/Examples/tree/master/fluid_dynamics/validation/compressible_step_woodward_colella/source)

## Case Specification
This is a 2D simulation of the classical step from Woodward and Collela (1), using the Euler equations.

The problem geometry consists of a rectangle with a step at the bottom. The boundaing rectangle has a width of 3m and a height of 1m. The step is located 0.6 meters to the right of the bottom-left corner, and it rises to 0.1m above the bottom edge.

The top and bottom boundaries, as well as the step are free-slip. The node at the bottom of the step (0.6, 0.0), has its velocity set to zero for numerical stability purposes. The right boundary is left open. The left boundary enforces same values as the initial conditions:
* Density (&rho;): 1.4 _kg/m<sup>3</sup>
* Pressure (_p_): 1.0 _Pa_
* Velocity (_v_): [3.0, 0.0] _m/s_
* Temperature (_T_): 0.0024728 _K_

The strange temperature is the truncated value is such that the speed of sound is 1.0 _m/s_.

Concerning the material, a perfect fluid with the characteristic parameters listed below is used.
* Dynamic viscosity (&mu;): 0
* Thermal conductivity (&kappa;): 0
* Specific heat (_c<sub>p</sub>_): 722.14 _J/KgK_
* Heat capacity ratio (&gamma;): 1.4

An adaptive time step strategy based on the CFL and Fourier number is used.

## Results
The problem is solved with a Variational Multi-Scale stabilized compressible Navier-Stokes formulation written in conservative variables (2). A Back-And-Forth Error Compensation Correction time-scheme is used, from (3). The physics-based shock capturing technique described in (4) is also used.

The computational domain is meshed with 100k linear triangular elements.

Current implementation fails to solve this case, due to insufficient artifficial difusivity.


## References
(1) Woodward, P., & Colella, P. (1984). The numerical simulation of two-dimensional fluid flow with strong shocks. Journal of computational physics, 54(1), 115-173. [https://doi.org/10.1016/0021-9991(84)90142-6](https://doi.org/10.1016/0021-9991(84\)90142-6)

(2) Bayona Roa, C.A., Baiges, J. and Codina, R. (2016), Variational multi-scale finite element approximation of the compressible Navier-Stokes equations, International Journal of Numerical Methods for Heat & Fluid Flow, Vol. 26 No. 3/4, pp. 1240-1271. [https://doi.org/10.1108/HFF-11-2015-0483](https://doi.org/10.1108/HFF-11-2015-0483 )

(3) Hashemi, M. R., Rossi, R., & Ryzhakov, P. B. (2022). An enhanced non-oscillatory BFECC algorithm for finite element solution of advective transport problems. Computer Methods in Applied Mechanics and Engineering, 391, 114576. [https://doi.org/10.1016/j.cma.2022.114576](https://doi.org/10.1016/j.cma.2022.114576)

(4) Fernandez, P., Nguyen, C., & Peraire, J. (2018), A physics-based shock capturing method for unsteady laminar and turbulent flows. In 2018 AIAA Aerospace Sciences Meeting (p. 0062). [https://doi.org/10.2514/6.2018-0062](https://doi.org/10.2514/6.2018-0062)
