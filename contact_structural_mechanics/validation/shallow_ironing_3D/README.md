# Shallow ironing

**Author:** Vicente Mataix Ferrándiz

**Kratos version:** Current head

**Source files:** [Shallow ironing](https://github.com/KratosMultiphysics/Examples/tree/master/contact_structural_mechanics/use_cases/shallow_ironing_3D/source)

## Case Specification

The problem consists in an ironing problem. We run two simulations, as etup that is considered along the literature a custom setup with a 20% more vertical displacement (so even more complex). This one is un by default, the one in the literature needs to run the ProjectParameters_literature.json

The contacting bodies exhibit neo-Hookean material behavior with Young’s moduli equal to 68.96e8 Pa and 68.96e7 Pa for the indenter and the block respectively and Poisson’s ratio of 0.32 for both parts.

For the literature case, and although the performed simulation is quasi-static, load steps are defined as a function of time for the sake of presentation of the results. From 0 to 1 second, the indenter is moved vertically towards the block by a total amount of 1 mm in 10 equal steps. From 1 to 2 seconds, the indenter is displaced horizontally by a total distance of 10 mm in 500 equal steps.

- **Setup**:

<p align="center">
  <img src="data/setup.png" alt="Mesh1" style="width: 600px;"/>
</p>

- **Mesh**:

<p align="center">
  <img src="data/mesh.png" alt="Mesh1" style="width: 600px;"/>
</p>

## Results

### Literature setup:

Comparing the results with the reference:

<p align="center">
  <img src="data/solution_frictionless.png" alt="Mesh1" style="width: 600px;"/>
</p>


### Custom setup:

The displacement evolution is:

![](data/animation.gif)

## References

- An unconstrained integral approximation of large sliding frictional contact between deformable solids. Poulios, Konstantinos
