# Deterministic wind engineering rectangle problem

**Author:** [Riccardo Tosi](https://github.com/riccardotosi)

**Kratos version:** 8.0

**XMC version:** 2.0

**PyCOMPSs version:** 2.7

**Source files:** [Asynchronous and Synchronous Monte Carlo - Ensemble Average](source)

## Case Specification
We solve the [fluid dynamics problem](https://github.com/KratosMultiphysics/Kratos/tree/master/applications/FluidDynamicsApplication) of a fluid passing through a bluff body. The problem is characterized by uniform and stochastic wind inlet velocity. The wind inlet velocity follows the following probability density function ![velocity-rand-variable-distribution]. In this problem, each different wind realization is solved exploiting ensemble average, see [Makarashvili, V., Merzari, E., Obabko, A., Siegel, A., & Fischer, P. (2017). A performance analysis of ensemble averaging for high fidelity turbulence simulations at the strong scaling limit. Computer Physics Communications. https://doi.org/10.1016/j.cpc.2017.05.023] and [Krasnopolsky, B. I. (2018). Optimal Strategy for Modelling Turbulent Flows with Ensemble Averaging on High Performance Computing Systems. Lobachevskii Journal of Mathematics. https://doi.org/10.1134/S199508021804008X] for details.

As seen in [Ayoul-Guilmard, Q., Núñez, M., Ganesh, S., Nobile, F., Rossi, R., & Tosi, R. (2020). D5.3 Report on theoretical work to allow the use of MLMC with adaptive mesh refinement.], we could not prove Multilevel Monte Carlo hypotheses for such turbulent and chaotic problem. For this reason, we apply Monte Carlo, exploiting XMC.

The problem can be run with two different algorithms:

* Synchronous Monte Carlo (SMC),
* Asynchronous Monte Carlo (AMC),

and by default AMC is selected. If one is interested in running SMC, it is needed to select `asynchronous = false` in the solver wrapper settings.

The Quantities of Interest of the problem are the drag force, the base moment and the pressure field. Statistical convergence is assessed for the drag force.

All settings can be observed in the corresponding configuration file of the algorithm, located inside the `problem_settings` folder.

To run the examples, the user should go inside the source folder and run the `run_xmc_mc.py` Python file. In case one wants to use PyCOMPSs, the user should execute `run.sh` from inside the source folder.

## Results

The velocity and pressure fields evolution of the problem are shown next.
![velocity](data/velocity.gif)
![velocity](data/pressure.gif)

The power sums and the h-statistics of both the time averaged and time series drag force, base moment and pressure field can be found [here](source/power_sums_outputs).

In addition,the drag coefficient we estimate from the drag force is consistent with literature [Bruno, L., Salvetti, M. V., & Ricciardelli, F. (2014). Benchmark on the aerodynamics of a rectangular 5:1 cylinder: An overview after the first four years of activity. Journal of Wind Engineering and Industrial Aerodynamics, 126, 87–106. https://doi.org/10.1016/j.jweia.2014.01.005].


[velocity-rand-variable-distribution]: https://latex.codecogs.com/svg.latex?u_{inlet}\sim~\mathcal{N}(2.0,0.02)