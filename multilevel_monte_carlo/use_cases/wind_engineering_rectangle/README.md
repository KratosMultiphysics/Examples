# Wind engineering rectangle problem with deterministic and stochastic inlet boundary conditions

**Author:** [Riccardo Tosi](https://riccardotosi.github.io) and [Marc Núñez](https://github.com/marcnunezc) and [Brendan Keith](https://brendankeith.github.io/)

**Kratos version:** 9.0

**XMC version:** Kratos default version

**PyCOMPSs version:** Kratos default version to run in serial, >2.8 to run with `runcompss`

**Source files:** [Asynchronous and Synchronous Monte Carlo](source)

**Application dependencies:** `ConvectionDiffusionApplication`, `ExaquteSandboxApplication`, `FluidDynamicsApplication`, `LinearSolversApplications`, `MappingApplication`, `MeshingApplication`, `MultilevelMonteCarloApplication`, `StatisticsApplication`

## Case Specification
We solve the [fluid dynamics problem](https://github.com/KratosMultiphysics/Kratos/tree/master/applications/FluidDynamicsApplication) of a fluid passing through a bluff body. The problem is characterized by uniform wind inlet velocity, constant in time. Two different problems can be solved:

* constant in time deterministic inlet boundary conditions: wind velocity modulus is <img src="https://render.githubusercontent.com/render/math?math=2m/s">,
* constant in time stochastic inlet boundary conditions: wind velocity modulus is random and it behaves as <img src="https://render.githubusercontent.com/render/math?math=u_{inlet}\sim\mathcal{N}(2.0,0.02)">.

Each realization with fixed inlet boundary condition can be solved exploiting ensemble average, see [1] for details.

As seen in [2], we could not prove standard Multilevel Monte Carlo hypotheses for such a turbulent and chaotic problem. For this reason, we solve it by apllying Monte Carlo.

The problem can be run with two different algorithms:

* Synchronous Monte Carlo (SMC),
* Asynchronous Monte Carlo (AMC),

and by default AMC is selected. If one is interested in running SMC, it is needed to select `asynchronous = false` in the solver wrapper settings of XMC settings (in `parameters_xmc.json`). To change the inlet boundary condition, you can set `true` or `false` the key `random_velocity_modulus` of Kratos settings (in `ProjectParametersRectangularCylinder2D_Fractional.json`). Please observe that for running you may want to increase the number of realizations per level, the time horizon of each realization and the burn-in time (initial transient we discard when computing statistics to discard dependencies from initial conditions).

The Quantities of Interest of the problem are the drag force and the pressure field and their time-averaged counterparts. Statistical convergence is assessed for the time-averaged drag force.

All settings can be observed in the corresponding configuration file of the algorithm, located inside the `problem_settings` folder.

To run the examples, the user should go inside the source folder and run the `run_mc_Kratos.py` Python file. In case one wants to use PyCOMPSs, the user should execute `run.sh` from inside the source folder.

## Results

The velocity and pressure fields evolution of the problem are shown next.
<img src="data/velocity.gif" alt="velocity" width="750"/>
<img src="data/pressure.gif" alt="pressure" width="750"/>

Three cases are run:

* deterministic inlet boundary conditions and ensemble average,
* stochastic inlet boundary conditions,
* stochastic inlet boundary conditions and ensemble average,

The power sums and the h-statistics of both the time averaged and time series drag force, base moment and pressure field can be found [here](source/power_sums_outputs).

The drag coefficient we estimate from the drag force is consistent with literature [3].

## References

[1] Tosi, R., Núñez, M., Pons-Prats, J., Principe, J. & Rossi, R. (2022). On the use of ensemble averaging techniques to accelerate the Uncertainty Quantification of CFD predictions in wind engineering. Journal of Wind Engineering and Industrial Aerodynamics. https://doi.org/10.1016/j.jweia.2022.105105

[2] Ayoul-Guilmard, Q., Núñez, M., Ganesh, S., Nobile, F., Rossi, R., & Tosi, R. (2020). D5.3 Report on theoretical work to allow the use of MLMC with adaptive mesh refinement.

[3] Bruno, L., Salvetti, M. V., & Ricciardelli, F. (2014). Benchmark on the aerodynamics of a rectangular 5:1 cylinder: An overview after the first four years of activity. Journal of Wind Engineering and Industrial Aerodynamics, 126, 87–106. https://doi.org/10.1016/j.jweia.2014.01.005
