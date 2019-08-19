# Beam  SPR 2D remeshing

**Author:** Vicente Mataix Ferrándiz

**Kratos version:** Current head

**Source files:** [Beam SPR 2D](https://github.com/KratosMultiphysics/Examples/tree/master/mmg_remeshing_examples/use_cases/beam_spr/source)

## Case Specification

In this test case, 

The following applications of Kratos are used:
- *StructuralMechanicsApplication*
- *MeshingApplication* with the *MMG* module

## Case Specification

The problem consists in a cantilever beam 1x0.1 m in plane strain. The beam is remeshed considering a SPR error.

*The original mesh*:

<p align="center">
  <img src="data/mesh.png" alt="Mesh1" style="width: 600px;"/>
</p>

*Displacement*:

<p align="center">
  <img src="data/disp.png" alt="Mesh1" style="width: 600px;"/>
</p>

*Error*:

<p align="center">
  <img src="data/error.png" alt="Mesh1" style="width: 600px;"/>
</p>

		
## Results

*The resulting mesh*:

<p align="center">
  <img src="data/mesh_solution.png" alt="Mesh1" style="width: 600px;"/>
</p>

*Displacement*:

<p align="center">
  <img src="data/disp_solution.png" alt="Mesh1" style="width: 600px;"/>
</p>

*Error*:

<p align="center">
  <img src="data/error_solution.png" alt="Mesh1" style="width: 600px;"/>
</p>

## References