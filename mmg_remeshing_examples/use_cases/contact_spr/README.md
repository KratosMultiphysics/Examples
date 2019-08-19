# Contact SPR 2D remeshing

**Author:** Vicente Mataix Ferrándiz

**Kratos version:** Current head

**Source files:** [Contact SPR 2D](https://github.com/KratosMultiphysics/Examples/tree/master/mmg_remeshing_examples/use_cases/contact_spr/source)

## Case Specification

In this test case, 

The following applications of Kratos are used:
- *StructuralMechanicsApplication*
- *ContactStructuralMechanicsApplication*
- *MeshingApplication* with the *MMG* module

## Case Specification

The problem consists in a simple patch test in plane strain. The problem is remeshed considering a SPR error.

*The original mesh*:

<p align="center">
  <img src="data/pre_remesh.png" alt="Mesh1" style="width: 600px;"/>
</p>

*Displacement*:

<p align="center">
  <img src="data/pre_remesh_displacement.png" alt="Mesh1" style="width: 600px;"/>
</p>

*Error*:

<p align="center">
  <img src="data/pre_remesh_error.png" alt="Mesh1" style="width: 600px;"/>
</p>

		
## Results

The evolution and reduction of the error can be appretiated in the following remeshing steps:

- Step 1:

*The resulting mesh*:

<p align="center">
  <img src="data/post_remesh_1.png" alt="Mesh1" style="width: 600px;"/>
</p>

*Displacement*:

<p align="center">
  <img src="data/post_remesh_displacement_1.png" alt="Mesh1" style="width: 600px;"/>
</p>

*Error*:

<p align="center">
  <img src="data/post_remesh_error_2.png" alt="Mesh1" style="width: 600px;"/>
</p>

- Step 2:

*The resulting mesh*:

<p align="center">
  <img src="data/post_remesh_2.png" alt="Mesh1" style="width: 600px;"/>
</p>

*Displacement*:

<p align="center">
  <img src="data/post_remesh_displacement_1.png" alt="Mesh1" style="width: 600px;"/>
</p>

*Error*:

<p align="center">
  <img src="data/post_remesh_error_2.png" alt="Mesh1" style="width: 600px;"/>
</p>

- Step 3:

*The resulting mesh*:

<p align="center">
  <img src="data/post_remesh_3.png" alt="Mesh1" style="width: 600px;"/>
</p>

*Displacement*:

<p align="center">
  <img src="data/post_remesh_displacement_3.png" alt="Mesh1" style="width: 600px;"/>
</p>

*Error*:

<p align="center">
  <img src="data/post_remesh_error_3.png" alt="Mesh1" style="width: 600px;"/>
</p>
