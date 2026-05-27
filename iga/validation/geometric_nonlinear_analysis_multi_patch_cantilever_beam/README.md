# Geometric Non-Linear Analysis - Multi Patch - Cantilever Beam

**Author:** Aakash Ravichandran

**Kratos version:** 10.4

**Source files:** [Geometric Non-Linear Analysis - Multi Patch - Cantilever Beam](https://github.com/KratosMultiphysics/Examples/tree/master/iga/validation/geometric_nonlinear_analysis_multi_patch_cantilever_beam/source)

## Problem definition

This example presents the validation of geometric non-linear analysis of a cantilever beam subjected to a end shear force [1].

<div align="center">
<img src="data/Reference_Model.png" alt="Displacement" width="600">

*Structural System [1]*
</div>


The cantilever beam is modeled using two connected NURBS patches with the Shell3pElement. The CAD model of both the patches is constructed with single span B-spline surfaces. The first patch has an curve degree of 2 in both axes and the second patch has an curve degree of 3 in the longitudinal direction and 2 in the transverse direction. Additional refinement is applied in Kratos by increasing the curve degree by 1 in both directions for both patches. Furthermore, h-refinement is applied by inserting 4 knots longitudinally and 3 knots transversely in the first patch, alongside 12 knots longitudinally and 4 knots transversely in the second patch. Hence on the edge where two surfaces gets connected, in the first patch number of elements is 4 and in 2nd patch the number of elements is 5. Therefore they are nonconforming patches. 

## Results

The load-displacement curve obtained at the free end is shown in [figure](data/LoadStep_vs_Displacement_XZ.png). This shows a good agreement with the reference [1] - Figure 2a and Table 2. 

<div align="center">
<img src="data/Model.png" alt="Displacement" width="600">

*Displacement Result*
</div>


<div align="center">

| Reference Force vs Displacement [1] | Force vs Displacement - From Kratos |
| :---: | :---: |
| <img src="data/Reference_LoadStep_vs_Displacement_XZ.png" height="400"> | <img src="data/LoadStep_vs_Displacement_XZ.png" height="400"> |

</div>



## References

1. Sze, K. Y., Liu, X. H., & Lo, S. H. (2004). Popular benchmark problems for geometric nonlinear analysis of shells. *Finite Elements in Analysis and Design*, 40(11), 1551–1569. https://doi.org/10.1016/j.finel.2003.11.001