# Multilevel Monte Carlo Application Examples

## Use Cases
- [Compressible potential flow problem](use_cases/compressible_potential_flow/README.md)
- [Fluid dynamics building problem](use_cases/fluid_dynamics_building)
- [Wind engineering rectangle problem](use_cases/wind_engineering_rectangle)
- [Wind engineering CAARC problem](use_cases/wind_engineering_CAARC)
    - [Steady inlet wind engineering CAARC problem with ensemble average approach](use_cases/wind_engineering_CAARC/steady_inlet_monte_carlo)
    - [Turbulent inlet wind engineering CAARC problem with ensemble average approach](use_cases/wind_engineering_CAARC/turbulent_inlet_monte_carlo)

## Validation Cases
- [Elliptic benchmark](validation/elliptic_benchmark)

## Remarks
- To run with `PyCOMPSs`, it is necessary to compile it first. You can find a detailed guide on how to do it in the [Kratos wiki](https://github.com/KratosMultiphysics/Kratos/wiki/How-to-run-multiple-cases-using-PyCOMPSs). In addition, the environment variable `EXAQUTE_BACKEND=pycompss` must be set. We refer to the [MultilevelMonteCarloApplication documentation](https://github.com/KratosMultiphysics/Kratos/tree/master/applications/MultilevelMonteCarloApplication#pycompss) for further details.
In case running with `PyCOMPSs` gives errors, try to replace relative paths with absolute paths in configuration `json` files, as first attempt to fix the issue.
- These examples make use of some external libraries that are not compatible with the Kratos binaries. In order to try these examples, it is necessary to compile Kratos on your own machine.
