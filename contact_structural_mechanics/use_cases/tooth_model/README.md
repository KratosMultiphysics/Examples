# Tooth model

**Author:** Vicente Mataix Ferrándiz

**Kratos version:** Current head

**Source files:** [Tooth model](https://github.com/KratosMultiphysics/Examples/tree/master/contact_structural_mechanics/use_cases/tooth_model/source)

## Case Specification

The problem consists in a simplified model of a tooth with different types of layers.

The model with **enamel+composite**:

<p align="center">
  <img src="data/enamel+composite.png" alt="Mesh1" style="width: 600px;"/>
</p>

**Layers**:
- *Composite*. Color 2: density=3.2e5 E=1.03e10 &nu;=0.3
- *Enamel*. Color 3: density=3.2e5 E=8.0e10 &nu;=0.3
- *Press*. Color 4: density=7.85e3 E=2.069e11 &nu;=0.29

The model with **enamel+dentine+composite**:

<p align="center">
  <img src="data/enamel+dentine+composite.png" alt="Mesh2" style="width: 600px;"/>
</p>

**Layers**:
- *Composite*. Color 2: density=3.2e5 E=1.03e10 &nu;=0.3
- *Enamel*. Color 3: density=3.2e5 E=8.0e10 &nu;=0.3
- *Dentine*. Color 4: density=3.2e5 E=2.0e10 &nu;=0.3
- *Press*. Color 5: density=7.85e3 E=2.069e11 &nu;=0.29

## Results

### Enamel + Composite

**Displacement**:

<p align="center">
  <img src="data/enamel+composite_disp.png" alt="Mesh2" style="width: 600px;"/>
</p>

**VM**:

<p align="center">
  <img src="data/enamel+composite_vm.png" alt="Mesh2" style="width: 600px;"/>
</p>

### Enamel + Dentine + Composite

**Displacement**:

<p align="center">
  <img src="data/enamel+dentine+composite_disp.png" alt="Mesh2" style="width: 600px;"/>
</p>

**VM**:

<p align="center">
  <img src="data/enamel+dentine+composite_vm.png" alt="Mesh2" style="width: 600px;"/>
</p>

## References

