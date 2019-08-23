# Contact Hessian 2D remeshing

**Author:** Vicente Mataix Ferrándiz

**Kratos version:** Current head

**Source files:** [Contact Hessian 2D](https://github.com/KratosMultiphysics/Examples/tree/master/mmg_remeshing_examples/use_cases/contact_hessian/source)

## Case Specification

In this test case, 

The following applications of Kratos are used:
- *StructuralMechanicsApplication*
- *ContactStructuralMechanicsApplication*
- *MeshingApplication* with the *MMG* module

## Case Specification

The problem consists in a simple patch test in plane strain. The problem is remeshed considering an Hessian metric. The metric intersects the contact pressure, VM stress and additionally the strain energy. We will evaluate 4 steps, and we will perform the remesh each 2 steps. We will compare the solution between taking into account the strain energy and without it. As the initial mesh is very coarse it doesn't provide much information, but in the later steps we can see as the mesh is refined arround critics points.

*The original mesh*:

<p align="center">
  <img src="data/pre_remesh.png" alt="Mesh1" style="width: 600px;"/>
</p>

*Displacement*:

<p align="center">
  <img src="data/pre_remesh_displacement.png" alt="Mesh1" style="width: 600px;"/>
</p>

*VM stress*:

<p align="center">
  <img src="data/pre_remesh_vm.png" alt="Mesh1" style="width: 600px;"/>
</p>

*Strain energy*:

<p align="center">
  <img src="data/pre_remesh_strain_energy.png" alt="Mesh1" style="width: 600px;"/>
</p>
		
## Results

The evolution and reduction of the error can be appretiated in the following remeshing steps:

### Without strain enery

- Step 1:

*The resulting mesh*:

<p align="center">
  <img src="data/vm_post_1_remesh.png" alt="Mesh1" style="width: 600px;"/>
</p>

*Displacement*:

<p align="center">
  <img src="data/vm_post_1_displacement.png" alt="Mesh1" style="width: 600px;"/>
</p>

*VM stress*:

<p align="center">
  <img src="data/vm_post_1_vm.png" alt="Mesh1" style="width: 600px;"/>
</p>

*Strain energy*:

<p align="center">
  <img src="data/vm_post_1_strain_energy.png" alt="Mesh1" style="width: 600px;"/>
</p>

- Step 2:

*Displacement*:

<p align="center">
  <img src="data/vm_post_2_displacement.png" alt="Mesh1" style="width: 600px;"/>
</p>

*VM stress*:

<p align="center">
  <img src="data/vm_post_2_vm.png" alt="Mesh1" style="width: 600px;"/>
</p>

*Strain energy*:

<p align="center">
  <img src="data/vm_post_2_strain_energy.png" alt="Mesh1" style="width: 600px;"/>
</p>

- Step 3:

*The resulting mesh*:

<p align="center">
  <img src="data/vm_post_3_remesh.png" alt="Mesh1" style="width: 600px;"/>
</p>

*Displacement*:

<p align="center">
  <img src="data/vm_post_3_displacement.png" alt="Mesh1" style="width: 600px;"/>
</p>

*VM stress*:

<p align="center">
  <img src="data/vm_post_3_vm.png" alt="Mesh1" style="width: 600px;"/>
</p>

*Strain energy*:

<p align="center">
  <img src="data/vm_post_3_strain_energy.png" alt="Mesh1" style="width: 600px;"/>
</p>

### With strain enery

- Step 1:

*The resulting mesh*:

<p align="center">
  <img src="data/strain_post_1_remesh.png" alt="Mesh1" style="width: 600px;"/>
</p>

*Displacement*:

<p align="center">
  <img src="data/strain_post_1_displacement.png" alt="Mesh1" style="width: 600px;"/>
</p>

*VM stress*:

<p align="center">
  <img src="data/strain_post_1_vm.png" alt="Mesh1" style="width: 600px;"/>
</p>

*Strain energy*:

<p align="center">
  <img src="data/strain_post_1_strain_energy.png" alt="Mesh1" style="width: 600px;"/>
</p>

- Step 2:

*Displacement*:

<p align="center">
  <img src="data/strain_post_2_displacement.png" alt="Mesh1" style="width: 600px;"/>
</p>

*VM stress*:

<p align="center">
  <img src="data/strain_post_2_vm.png" alt="Mesh1" style="width: 600px;"/>
</p>

*Strain energy*:

<p align="center">
  <img src="data/strain_post_2_strain_energy.png" alt="Mesh1" style="width: 600px;"/>
</p>

- Step 3:

*The resulting mesh*:

<p align="center">
  <img src="data/strain_post_3_remesh.png" alt="Mesh1" style="width: 600px;"/>
</p>

*Displacement*:

<p align="center">
  <img src="data/strain_post_3_displacement.png" alt="Mesh1" style="width: 600px;"/>
</p>

*VM stress*:

<p align="center">
  <img src="data/strain_post_3_vm.png" alt="Mesh1" style="width: 600px;"/>
</p>

*Strain energy*:

<p align="center">
  <img src="data/strain_post_3_strain_energy.png" alt="Mesh1" style="width: 600px;"/>
</p>
