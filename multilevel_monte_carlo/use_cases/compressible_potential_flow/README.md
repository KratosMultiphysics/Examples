# Compressible Potential Flow problem

**Author:** [Riccardo Tosi](https://github.com/riccardotosi)

**Kratos version:** 8.0

**XMC version:** 2.0

**PyCOMPSs version:** 2.7

**Source files:** Synchronous Monte Carlo, Asynchronous Monte Carlo, Synchronous Multilevel Monte Carlo, Asynchronous Multilevel Monte Carlo

## Case Specification
We solve the [compressible potential flow problem](https://github.com/KratosMultiphysics/Kratos/blob/master/applications/CompressiblePotentialFlowApplication/python_scripts/potential_flow_analysis.py) around an airfoil NACA0012. The problem is characterized by stochastic angle of attack

The problem can be run with four different algorithms:

* Synchronous Monte Carlo (SMC),
* Asynchronous Monte Carlo (AMC),
* Synchronous Multilevel Monte Carlo (SMLMC),
* Asynchronous Multilevel Monte Carlo (AMLMC).

Apart from the scheduling, which may be synchronous or asynchronous, similar settings are employed. We refer, for example, to: number of samples estimation, number of indices estimation, maximum number of iterations, tolerance, confidence, etc. Such settings can be observed in the corresponding configuration file of each algorithm, located inside the `problem_settings` folder.

To run the examples, the user should go inside the folder-algorithm of interest and run the `run_mc/mlmc_Kratos.py` Python file. In case one wants to use PyCOMPSs, the user should execute `sh run_with_pycompss.sh` from inside the folder of interest.

## Results


[angle-rand-variable-distribution]:  https://latex.codecogs.com/svg.latex?\alpha\sim~\mathcal[N](5.0,0.05)
