# Contact Hertz Hessian 2D

**Author:** Vicente Mataix Ferrándiz

**Kratos version:** Current head

**Source files:** [Contact Hertz Hessian 2D](https://github.com/KratosMultiphysics/Examples/tree/master/mmg_remeshing_examples/use_cases/hertz_hessian/source)

## Case Specification

In this test case, 

The following applications of Kratos are used:
- *StructuralMechanicsApplication*
- *ContactStructuralMechanicsApplication*
- *MeshingApplication* with the *MMG* module

## Case Specification

The problem consists in a Hertz contact problem remeshing considering the Hessian of the VM stress and the contact pressure. There are 11 steps, and the remesh is executed each 3 steps starting in the 4th.

*The original mesh*:

<p align="center">
  <img src="data/mesh0.png" alt="Mesh1" style="width: 600px;"/>
</p>

		
## Results

The evolution and reduction of the error can be appretiated in the following remeshing steps:

- Step 1:

*Displacement*:

<p align="center">
  <img src="data/step1.png" alt="Mesh1" style="width: 600px;"/>
</p>

- Step 2:

*Displacement*:

<p align="center">
  <img src="data/step2.png" alt="Mesh1" style="width: 600px;"/>
</p>

- Step 3:

*Displacement*:

<p align="center">
  <img src="data/step3.png" alt="Mesh1" style="width: 600px;"/>
</p>

- Step 4:

*The resulting mesh*:

<p align="center">
  <img src="data/mesh1.png" alt="Mesh1" style="width: 600px;"/>
</p>

*Displacement*:

<p align="center">
  <img src="data/step4.png" alt="Mesh1" style="width: 600px;"/>
</p>

- Step 5:

*Displacement*:

<p align="center">
  <img src="data/step5.png" alt="Mesh1" style="width: 600px;"/>
</p>

- Step 6:

*Displacement*:

<p align="center">
  <img src="data/step6.png" alt="Mesh1" style="width: 600px;"/>
</p>

- Step 7:

*The resulting mesh*:

<p align="center">
  <img src="data/mesh2.png" alt="Mesh1" style="width: 600px;"/>
</p>

*Displacement*:

<p align="center">
  <img src="data/step7.png" alt="Mesh1" style="width: 600px;"/>
</p>

- Step 8:

*Displacement*:

<p align="center">
  <img src="data/step8.png" alt="Mesh1" style="width: 600px;"/>
</p>

- Step 9:

*Displacement*:

<p align="center">
  <img src="data/step9.png" alt="Mesh1" style="width: 600px;"/>
</p>

- Step 10:

*Displacement*:

<p align="center">
  <img src="data/step10.png" alt="Mesh1" style="width: 600px;"/>
</p>

- Step 11:

*Displacement*:

<p align="center">
  <img src="data/step11.png" alt="Mesh1" style="width: 600px;"/>
</p>

*VM stress*:

<p align="center">
  <img src="data/vm.png" alt="Mesh1" style="width: 600px;"/>
</p>