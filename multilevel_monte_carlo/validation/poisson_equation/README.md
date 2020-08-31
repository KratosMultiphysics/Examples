# Poisson equation

**Author:** [Riccardo Tosi](https://github.com/riccardotosi)

**Kratos version:** 8.0

**XMC version:** 2.0

**PyCOMPSs version:** 2.7

**Source files:** Synchronous Monte Carlo, Asynchronous Monte Carlo, Synchronous Multilevel Monte Carlo, Asynchronous Multilevel Monte Carlo

## Case Specification
Let's consider the stationary heat equation with a varying heat flux, a square two-dimensional domain and Dirichlet boundary conditions. Thus the problem reads as:

![diffusion-eq]

![boundary-cond] ,

where ![domain], ![forcing] and ![rand-variable-distribution], i.e. ![rand-variable-symbol] follows a beta distribution. The thermal diffusivity is ![thermal-diffusivity-value] for simplicity. The Quantity of Interest (QoI) we are interested about is the integral over the whole domain of the temperature, meaning:

![qoi] .

We want to highlight that in the `SimulationScenario` class we added the `EvaluateQuantityOfInterest(self)` function with respect to the `AnalysisStage` base class. This function computes the QoI, given the results of the analysis. In addition, we see `ModifyInitialProperties(self)` modifies the property `KratosMultiphysics.HEAT_FLUX` of our PDE.

The problem is run with four different algorithms:

* Synchronous Monte Carlo,
* Asynchronous Monte Carlo,
* Synchronous Multilevel Monte Carlo,
* Asynchronous Multilevel Monte Carlo.

Apart from the scheduling, similar settings are employed for synchronous and their asynchronous counterparts. We refer, for example, to: number of samples estimation, number of indices estimation, maximum number of iterations, tolerance, confidence, etc. Such settings can be observed in the corresponding configuration file of each algorithm, located inside the `problem_settings` folder.

## Results

The expected result is to observe statistical accuracy and scheduling parallelism for the asynchronous algorithms.



[diffusion-eq]: https://latex.codecogs.com/svg.latex?\nabla\cdot(K\nabla~u)=\varepsilon~f\qquad~u\in\Omega
[boundary-cond]: https://latex.codecogs.com/svg.latex?u=0\qquad~u\in\partial(\Omega)
[domain]: https://latex.codecogs.com/svg.latex?\Omega=[0,1]^{2}
[rand-variable-distribution]:  https://latex.codecogs.com/svg.latex?\varepsilon\sim~Beta(2,6)
[qoi]:  https://latex.codecogs.com/svg.latex?QoI=\int_{\Omega}u(x,y)dx~dy
[forcing]:  https://latex.codecogs.com/svg.latex?f=-432(x^2+y^2-x-y)
[rand-variable-symbol]:  https://latex.codecogs.com/svg.latex?\varepsilon
[thermal-diffusivity-value]:  https://latex.codecogs.com/svg.latex?K=1
[temperature-symbol]: https://latex.codecogs.com/svg.latex?u