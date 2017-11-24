# Kratos Multiphysics Examples

This repository contains a collection of validation and use cases showcasing different features of the [Kratos Multiphysics](https://github.com/KratosMultiphysics/Kratos) Finite Element Framework.

Each folder presents cases on a given area, organized as follows:

- **Use cases:** Complete cases showcasing a given feature or application.

- **Validation:** Benchmark problems (academic or otherwise) that can be compared to reference data from scientific literature.

Each case should be self-contained: include all input data and relevant scripts so that users can test it. It should also be accompanied by a page (a simple file such as this readme, or a full wiki page) presenting it and linking to reference results, if available in the literature.

Unit tests should *not* be uploaded to this repository. Please put them in the `tests` folder of the corresponding application.

## Fluid-Structure Interaction (FSI)

**Validation**

- [Mok benchmark](fluid_structure_interaction/validation/fsi_mok/README.md) 

## [Dam](https://github.com/KratosMultiphysics/Examples/tree/dam-examples/dam) 

**Use cases**

- [2D Thermo-mechanical Seasonal Effects](dam/use_cases/2d_dam_thermo_mechanical/README.md) 
- [2D Thermo-mechanical Including Reservoir Effects](dam/use_cases/2d_dam_thermo_mechanical_with_reservoir/README.md) 
- [2D Joint Beams](dam/use_cases/2d_joint_element/README.md) 
- [3D Construction Process](dam/use_cases/3d_dam_construction/README.md) 
- [2D Acoustic Pulse](dam/use_cases/Acoustic/README.md) 
