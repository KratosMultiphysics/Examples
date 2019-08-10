# Gears

**Author:** Vicente Mataix Ferrándiz

**Kratos version:** Current head

**Source files:** [Gears](https://github.com/KratosMultiphysics/Examples/tree/master/contact_structural_mechanics/use_cases/gears/source)

## Case Specification

The problem consists in two gears, one is fixed, the other has a rotational movement imposed.

*The mesh*:

<p align="center">
  <img src="data/mesh.png" alt="Mesh1" style="width: 600px;"/>
</p>

The displacement imposed is ux= x0 - R cos(atan(y0/x0) - w*t) uy = y0 - R sin(atan(y0/x0) - w*t) 

Two different combinations of materials has been tested:

- *Linear elastic*:
	- Gear1:
		- LinearElastic3DLaw
		- E: 68.96e8
		- &nu; 0.32
	- Gear2:
		- LinearElastic3DLaw
		- E: 68.96e7
		- &nu; 0.32
- *Elastic-plastic*:
	**TODO**
		
## Results

### Linear elastic

- **Displacement**:

	- *General*:
<p align="center">
  <img src="data/linear_disp.gif" alt="Mesh1" style="width: 600px;"/>
</p>

	- *Detail*:
<p align="center">
  <img src="data/detail_linear_disp.gif" alt="Mesh1" style="width: 600px;"/>
</p>

- **VM**:

	- *General*:
<p align="center">
  <img src="data/linear_vm.gif" alt="Mesh1" style="width: 600px;"/>
</p>

	- *Detail*:
<p align="center">
  <img src="data/detail_linear_vm.gif" alt="Mesh1" style="width: 600px;"/>
</p>


### Elastic-plastic

**TODO**

## References

