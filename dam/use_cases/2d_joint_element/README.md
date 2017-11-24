# 2D Joint Beams Example

**Author:** Lorenzo Gracia

**Kratos version:** 5.2

**Source files:** [2D Joint Beams](https://github.com/KratosMultiphysics/Examples/tree/master/dam/use_cases/2d_joint_element/source)

## Case Specification

This is a 2D mechanical problem for showing one of the several applications of the joint element. The joint element is a quasi-zero thickness element which allows to capture some discontinuities in the solution. 

The problem consist on two beams in contact thanks to the joint element. The left side is totally clamped, working as a cantilever. An incremental point load is applied at the free side.

The following applications of Kratos are used:
* SolidMechanicsApplication
* PoromechanicsApplication 
* ConvectionDifussionApplication
* DamApplication

## Results

The problem stated above has been solved with a structured mesh composed by linear quadrilateral elements. The maximum compressive stresses are presented below. In the figure it is possible to appreciate that the incremental load provokes the contact between both both beams and the joint element works as a contact element. 
<img
  src="data/2d_joint_post.png"
  width="800"
  title="Summer">