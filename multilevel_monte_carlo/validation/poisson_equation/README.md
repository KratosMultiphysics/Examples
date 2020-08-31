# Elliptic benchmark problem

**Author:** [Riccardo Tosi](https://github.com/riccardotosi)

**Kratos version:** 8.0

**XMC version:** 2.0

**PyCOMPSs version:** 2.7

**Source files:** Synchronous Monte Carlo, Asynchronous Monte Carlo, Synchronous Multilevel Monte Carlo, Asynchronous Multilevel Monte Carlo

## Case Specification
Let's consider the stationary heat equation with a varying heat flux, a square two-dimensional domain and Dirichlet boundary conditions. The problem reads as:

![diffusion-eq]

![boundary-cond] ,

where ![domain], ![forcing] and ![rand-variable-distribution], i.e. ![rand-variable-symbol] follows a beta distribution. The thermal diffusivity is ![thermal-diffusivity-value] for simplicity. The Quantity of Interest (QoI) we are interested in is the integral over the whole domain of the temperature, meaning:

![qoi] .

The problem can be run with four different algorithms:

* Synchronous Monte Carlo (SMC),
* Asynchronous Monte Carlo (AMC),
* Synchronous Multilevel Monte Carlo (SMLMC),
* Asynchronous Multilevel Monte Carlo (AMLMC).

Apart from the scheduling, which may be synchronous or asynchronous, similar settings are employed. We refer, for example, to: number of samples estimation, number of indices estimation, maximum number of iterations, tolerance, confidence, etc. Such settings can be observed in the corresponding configuration file of each algorithm, located inside the `problem_settings` folder.

To run the examples, the user should go inside the folder-algorithm of interest and run the `run_mc/mlmc_Kratos.py` Python file. In case one wants to use PyCOMPSs, the user should execute `sh run_with_pycompss.sh` from inside the folder of interest.

## Results

The expected result is to observe statistical accuracy and scheduling parallelism for the asynchronous algorithms.
For this reason, we report the graph dependencies of SMC and of AMC.

SMC: ![SMC graph](https://github.com/KratosMultiphysics/Examples/blob/mlmc/add-examples/multilevel_monte_carlo/validation/poisson_equation/source/SMC_graph.PNG)
AMC: ![AMC graph](https://github.com/KratosMultiphysics/Examples/blob/mlmc/add-examples/multilevel_monte_carlo/validation/poisson_equation/source/AMC_graph.PNG)

SMLMC and AMLMC graphs present similar behaviors, with the difference that samples are run on different accuracy levels.

[diffusion-eq]: https://latex.codecogs.com/svg.latex?\nabla\cdot(K\nabla~u)=\varepsilon~f\qquad~u\in\Omega
[boundary-cond]: https://latex.codecogs.com/svg.latex?u=0\qquad~u\in\partial(\Omega)
[domain]: https://latex.codecogs.com/svg.latex?\Omega=[0,1]^{2}
[rand-variable-distribution]:  https://latex.codecogs.com/svg.latex?\varepsilon\sim~Beta(2,6)
[qoi]:  https://latex.codecogs.com/svg.latex?QoI=\int_{\Omega}u(x,y)dx~dy
[forcing]:  https://latex.codecogs.com/svg.latex?f=-432(x^2+y^2-x-y)
[rand-variable-symbol]:  https://latex.codecogs.com/svg.latex?\varepsilon
[thermal-diffusivity-value]:  https://latex.codecogs.com/svg.latex?K=1
[temperature-symbol]: https://latex.codecogs.com/svg.latex?u
