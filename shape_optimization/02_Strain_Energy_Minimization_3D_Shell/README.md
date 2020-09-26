# Shape Optimization
Unconstrained strain energy minimization of a 3D Shell

> **Author**: Armin Geiser
>
> **Kratos version**: 9.0

## Optimization Problem

### Objective
- Minimize strain energy

### Constraints
- no constraints

  <p align="center">
    <img src="images/3DShell_setup.svg" width="800">
  </p>

## Optimization settings
- Algorithm type : `steepest_descent`
- Number of steps : `100`
- Step size : `0.1`
- Filter radius : `3.0`
- Mesh motion : `False`

## Results

### Shape Evolution
The below image shows the evolution (shape) of the 3D Shell during the optimization iterations.

<p align="center">
    <img src="images/3DShell_results.gif" width="800">
</p>

