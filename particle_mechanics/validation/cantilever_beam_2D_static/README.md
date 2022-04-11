# 2D cantilever beam. Static analysis
**Author:** Ilaria Iaconeta and Laura Moreno

**Kratos version:** 

**Source files:** [cantilever_beam_2D_static](https://github.com/KratosMultiphysics/Examples/tree/master/particle_mechanics/validation/cantilever_beam_2D_static/source)

The
[Particle Mechanics Application](https://github.com/KratosMultiphysics/Kratos/tree/master/applications/ParticleMechanicsApplication) of Kratos is used to perform this example.


## Case Specification

The static analysis of a 2D cantilever beam subjected to its self-weight under the assumptions of plain strain is presented here.
The beam is modelled with a hyperelastic material:
* Density (_&rho;_): 1000 Kg/m<sup>3</sup>
* Young's modulus (_E_):  90 MPa
* Poisson ratio (_&nu;_): 0


The problem geometry as well as the boundary conditions are sketched below:

<p align="center">
  <img src="data/cantilever_scheme" alt="Geometry of the problem." width="350" />
</p>


## Results

The problem stated above has been solved with a structured mesh of quadrilateral elements with 4 material points per cell. A mehs convergence study  is carried out adopting five different mesh sizes: h=0.5, 0.25, 0.125, 0.0625 and 0.01m. The obtained numerical results are compared with the solution using other methods such as FEM, GMM-MLS and GMM-LME. An agreement between methods can be observed.

<p align="center">
  <img src="data/" alt="Obtained results and comparison." width="700" />
  

## Reference
Iaconeta, I., Larese, A., Rossi, R., & Guo, Z. (2017). Comparison of a material point method and a galerkin meshfree method for the simulation of cohesive-frictional materials. Materials, 10(10), 1150.
