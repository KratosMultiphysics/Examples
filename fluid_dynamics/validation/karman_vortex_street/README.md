# Flow over a 2D cylinder benchmark (Laminar, Re = 200)

**Author:** Aditya Ghantasala 

## Case Specification
This benchmark simulates the time-periodic behaviour of a fluid in a pipe with a circular obstacle. It is set up in 2D with geometry data is provided below. 

<p align="center">
  <img src="data/karman_vortex_street_velocity.gif" alt="Geometry specification and case setup." style="width: 600px;"/>
</p>

**Source files:** [Flow over a cylinder](https://github.com/KratosMultiphysics/Examples/tree/master/fluid_dynamics/validation/karman_vortex_street/source)

The following applications of Kratos are used:
* FluidDynamicsApplication

## Results

<p align="center">
  <img src="data/karman_vortex_street_velocity.gif" alt="Vortex shedding behind the cylinder [Karman vortex street] velocity distribution." style="width: 600px;"/>
</p>

<p align="center">
  <img src="data/karman_vortex_street_pressure.gif" alt="Vortex shedding behind the cylinder [Karman vortex street] pressure distribution." style="width: 600px;"/>
</p>

The following pictures shows the drag coefficient over time, once over the complete time interval [t0,t1], once near the maximum value and comparison is drawn between the values obtained by KRATOS solver and the benchmark.:

<p align="center">
  <img src="data/karman_vortex_street.gif" alt="Evolution of coefficient of drag with time." style="width: 600px;"/>
</p>

The following pictures shows the drag coefficient over time, once over the complete time interval [t0,t1], once near the maximum value and comparison is drawn between the values obtained by KRATOS solver and the benchmark.:

<p align="center">
  <img src="data/karman_vortex_street.gif" alt="Evolution of coefficient of lift with time." style="width: 600px;"/>
</p>

## References
1. http://www.featflow.de/en/benchmarks/cfdbenchmarking/flow/dfg_benchmark2_re100.html
2. Turek, Schaefer; Benchmark computations of laminar flow around cylinder; in Flow Simulation with High-Performance Computers II, Notes on Numerical Fluid Mechanics 52, 547-566, Vieweg 1996
3. John; Higher order Finite element methods and multigrid solvers in a benchmark problem for the 3D Navier-Stokes equations; Int. J. Numer. Meth. Fluids 2002; 40: 775-798 DOI:10.1002/d.377
