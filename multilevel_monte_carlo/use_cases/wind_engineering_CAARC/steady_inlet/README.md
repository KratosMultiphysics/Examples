# Steady inlet wind engineering CAARC problem with ensemble average method

**Author:** [Riccardo Tosi](https://github.com/riccardotosi) and [Marc Núñez](https://github.com/marcnunezc) and [Brendan Keith](https://brendankeith.github.io/)

**Kratos version:** 8.1

**XMC version:** Kratos default version

**PyCOMPSs version:** Kratos default version to run in serial, >2.8 to run with `runcompss`

**Source files:** [Ensemble average - Asynchronous and Synchronous Monte Carlo](source)

**Application dependencies:** `ConvectionDiffusionApplication`, `ExaquteSandboxApplication`, `FluidDynamicsApplication`, `LinearSolversApplications`, `MappingApplication`, `MeshingApplication`, `MultilevelMonteCarloApplication`, `StatisticsApplication`

## Case Specification
We solve the [fluid dynamics problem](https://github.com/KratosMultiphysics/Kratos/tree/master/applications/FluidDynamicsApplication) of a fluid passing through a building, namely the Commonwealth Advisory Aeronautical Council (CAARC) [1].

The problem presents a deterministic steady-state wind inlet velocity profile, which follows a logarithmic profile. Therefore, there is no uncertainty. To reduce the time to solution, ensemble average (see [2] and [3]) is applied, exploiting XMC.

The ensemble average strategy is run on top of the Monte Carlo algorithm. Then, the problem can be run with two different algorithms:

* Synchronous Monte Carlo (SMC),
* Asynchronous Monte Carlo (AMC),

and by default AMC is selected. If one is interested in running SMC, it is needed to select `asynchronous = false` in the [XMC settings](source/problem_settings/ProjectParametersCAARC_MC_steadyInlet.json).

The Quantities of Interest of the problem are the drag force, the base moment and the pressure field. Statistical convergence is assessed for the drag force.

All settings can be observed in the corresponding configuration file [of the problem](source/problem_settings/ProjectParametersCAARC_MC_steadyInlet.json) and [of the algorithm](source/problem_settings/parameters_xmc_asynchronous_mc_CAARC3d_Fractional.json). We remark that for example the user can change the `end_time` and the transient time of the simulation by changing `end_time` and `burnin_time`.

To run the examples, the user should go inside the source folder and run the `run_mc_Kratos.py` Python file. In case one wants to use PyCOMPSs, the user should execute `run.sh` from inside the source folder.

## Results

The velocity and pressure fields evolution of the problem are shown next.
<p align="center">
  <img src="data/velocity.gif" alt="velocity" style="width: 600px;"/>
</p>
<p align="center">
  <img src="data/pressure.gif" alt="pressure" style="width: 600px;"/>
</p>

An example of power sums and h-statistics of both time averaged and time series drag force, base moment and pressure field can be found [here](source/power_sums_outputs).

We comment that a literature comparison with respect to [4], [1] and [5] has been performed, to ensure the correctness and accuracy of our solution.

## Refrences

[1] Braun, A. L., & Awruch, A. M. (2009). Aerodynamic and aeroelastic analyses on the CAARC standard tall building model using numerical simulation. Computers and Structures, 87(9–10), 564–581. https://doi.org/10.1016/j.compstruc.2009.02.002

[2] Makarashvili, V., Merzari, E., Obabko, A., Siegel, A., & Fischer, P. (2017). A performance analysis of ensemble averaging for high fidelity turbulence simulations at the strong scaling limit. Computer Physics Communications. https://doi.org/10.1016/j.cpc.2017.05.023

[3] Krasnopolsky, B. I. (2018). Optimal Strategy for Modelling Turbulent Flows with Ensemble Averaging on High Performance Computing Systems. Lobachevskii Journal of Mathematics. https://doi.org/10.1134/S199508021804008X

[4] Obasaju, E. D. (1992). Measurement of forces and base overturning moments on the CAARC tall building model in a simulated atmospheric boundary layer. Journal of Wind Engineering and Industrial Aerodynamics. https://doi.org/10.1016/0167-6105(92)90361-D

[5] Huang, S., Li, Q. S., & Xu, S. (2007). Numerical evaluation of wind effects on a tall steel building by CFD. Journal of Constructional Steel Research. https://doi.org/10.1016/j.jcsr.2006.06.033