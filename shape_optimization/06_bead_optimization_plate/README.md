# Bead Optimization of a Plate

A bead optimization problem to minimize the strain energy of a plate.

> **Author**: Armin Geiser
>
> **Kratos version**: 9.0

## Optimization Problem

### Objective
- Minimize strain energy

### Constraints
- No constraints

  <p align="center">
    <img src="images/beadOpt_setup.svg" height="500">
  </p>

## Optimization settings
- Algorithm type : `bead_optimization`
- Number of steps : `300`
- Step size : `0.3`
- Filter radius : `0.075`
- Mesh motion : `False`

## Results

### Shape Evolution
The below image shows the shape evolution of the plate during the bead optimization iterations.

<p align="center">
    <img src="images/beadOpt_results.gif" height="400">
</p>