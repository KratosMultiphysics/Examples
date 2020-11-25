# Multilevel Monte Carlo Application Examples

## Use Cases
- [Compressible potential flow problem](use_cases/compressible_potential_flow/README.md)
- [Fluid dynamics building problem](use_cases/fluid_dynamics_building)
- [Wind engineering rectangle problem](use_cases/wind_engineering_rectangle)
    - [Deterministic wind engineering rectangle problem with ensemble average approach](use_cases/wind_engineering_rectangle/deterministic_ensemble_average)
    - [Stochastic wind engineering rectangle problem](use_cases/wind_engineering_rectangle/stochastic_MC)
    - [Stochastic wind engineering rectangle problem with ensemble average approach](use_cases/wind_engineering_rectangle/stochastic_MC_ensemble_average)
- [Wind engineering CAARC problem](use_cases/wind_engineering_CAARC)
    - [Steady inlet wind engineering CAARC problem with ensemble average approach](use_cases/wind_engineering_CAARC/deterministic_steady_inlet_ensemble_average)
    - [Turbulent inlet wind engineering CAARC problem with ensemble average approach](use_cases/wind_engineering_CAARC/deterministic_turbulent_inlet_ensemble_average)

## Validation Cases
- [Elliptic benchmark](validation/elliptic_benchmark)

## Remarks
- To run with `PyCOMPSs`, it is necessary to compile it first. You can find a detailed guide on how to do it [in the wiki](https://github.com/KratosMultiphysics/Kratos/wiki/How-to-run-multiple-cases-using-PyCOMPSs). In addition, the appropriate import has to be changed from
~~~python
from exaqute.ExaquteTaskLocal import *
~~~
to
~~~python
from exaqute.ExaquteTaskPyCOMPSs import *
~~~
wherever needed. We refer to the [MultilevelMonteCarloApplication documentation](https://github.com/KratosMultiphysics/Kratos/tree/master/applications/MultilevelMonteCarloApplication#pycompss) for further details.
In case running with `PyCOMPSs` gives errors, try to replace relative paths with absolute paths, as first attempt to fix the issue.
- These examples make use of some external libraries that are not comptaible with the Kratos Binaries. In order to try these examples, it is necessary to compile Kratos on your own machine.
