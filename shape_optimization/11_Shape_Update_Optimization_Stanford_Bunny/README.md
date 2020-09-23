# Shape Optimization
Shape update of a wrapping surface to generate a smooth representation of a complex object, which in this example is a Stanford bunny.

> **Author**: Armin Geiser
>
> **Kratos version**: 9.0

## Optimization Problem

### Objective
- Shape update maximization

### Constraints
- No penetration of packaging (bounding) mesh (*standford bunny*)

  <p align="center">
    <img src="images/bunny_opt_setup.png" height="500">
  </p>

## Optimization settings
- Algorithm type : `gradient_projection`
- Number of steps : `150`
- Step size : `0.001`
- Filter radius : `0.015`
- Mesh motion : `False`

## Results

### Shape Evolution
The below image shows the evolution (shape) of the wrapping surface during the optimization iterations. Although the small details like the ears of the bunny are not captured, the mesh quality is not compromised during shape update.

<p align="center">
    <img src="images/bunny_results_smallSphere.gif" height="400">
</p>

When using a small sphere the surface *grows* in order to wrap around the object. Alternatively, a large sphere can be used and with minor modifications in the [`optimization_parameters.json`](shrink) the surface can be made to *shrink* and wrap around the bunny object. 

  <p align="center">
    <img src="images/bunny_results_largeSphere.gif" height="500">
  </p>

