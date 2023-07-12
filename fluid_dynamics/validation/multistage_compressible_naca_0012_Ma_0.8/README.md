# Multistage transonic flow around a NACA0012 profile

**Author:** [Marco Antonio Zuñiga Perez](https://github.com/marco1410)

**Kratos version:** 9.3.1

**Source files:** [Multistage transonic flow around a NACA0012 profile](https://github.com/KratosMultiphysics/Examples/tree/master/fluid_dynamics/validation/multistage_compressible_naca_0012_Ma_0.8/source)

## Case Specification
This is a 2D simulation of a NACA0012 profile under transonic flow conditions (Ma = 0.8).

The same case as the one presented in [Transonic flow around a NACA0012 profile](https://github.com/KratosMultiphysics/Examples/tree/master/fluid_dynamics/validation/compressible_naca_0012_Ma_0.8/source) is solved in here but exploiting the Kratos multistage capabilities. Hence, in a first simulation stage the CompressiblePotentialFlowApplication is used to obtain a steady potential flow solution. Then, this solution is used as initial condition for the compressible Navier-Stokes simulation stage. As it can be observed in the settings file, this requires using an operation that converts the potential flow magnitudes to conservative ones. On top of increasing the robustness of the simulation during the very first steps, this reduces the simulation time required to reach the compressible Navier-Stokes steady state solution.

COMMENT SOMETHING ABOUT THE CHECKPOINTING

Further details on the case configuration, results and reference can be found in [here](https://github.com/KratosMultiphysics/Examples/tree/master/fluid_dynamics/validation/compressible_naca_0012_Ma_0.8).