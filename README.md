# Kratos Multiphysics Examples

This repository contains a collection of validation and use cases showcasing different features of the [Kratos Multiphysics](https://github.com/KratosMultiphysics/Kratos) Finite Element Framework.

Each folder presents cases on a given area, organized as follows:

- **Use cases:** Complete cases showcasing a given feature or application.

- **Validation:** Benchmark problems (academic or otherwise) that can be compared to reference data from scientific literature.

Each case should be self-contained: include all input data and relevant scripts so that users can test it. It should also be accompanied by a page (a simple file such as this readme, or a full wiki page) presenting it and linking to reference results, if available in the literature.

Unit tests should *not* be uploaded to this repository. Please put them in the `tests` folder of the corresponding application.

## Fluid Dynamics

**Use cases**

- [3D Wind over Barcelona](fluid_dynamics/use_cases/barcelona_wind/README.md) 

## Fluid-Structure Interaction (FSI)

**Validation**

- [Lid-driven cavity flow benchmark](fluid_structure_interaction/validation/fsi_lid_driven_cavity/README.md) 
- [Mok benchmark](fluid_structure_interaction/validation/fsi_mok/README.md)

## Contact Structural Mechanics

**Validation**

- [Double arch contact benchmark](contact_structural_mechanics/validation/double_arch/README.md)

## MMG remeshing

**Validation**
- [Hessian2D](mmg_remeshing_examples/validation/hessian2D/README.md)
- [Hessian3D](mmg_remeshing_examples/validation/hessian3D/README.md)
- [Bunny example](mmg_remeshing_examples/validation/bunny/README.md)

**Use Cases**
- [Channel sphere 2D](mmg_remeshing_examples/use_cases/channel_sphere2D/README.md)
- [Channel sphere 3D](mmg_remeshing_examples/use_cases/channel_sphere3D/README.md)
- [Beam 2D](mmg_remeshing_examples/use_cases/beam2D/README.md)
- [Cavity 2D](mmg_remeshing_examples/use_cases/cavity2D/README.md)
- [Lamborghini example](mmg_remeshing_examples/use_cases/lamborghini/README.md)

## Dam 

**Use cases**

- [2D Thermo-mechanical Seasonal Effects](dam/use_cases/2d_dam_thermo_mechanical/README.md) 
- [2D Thermo-mechanical Including Reservoir Effects](dam/use_cases/2d_dam_thermo_mechanical_with_reservoir/README.md) 
- [2D Joint Beams](dam/use_cases/2d_joint_element/README.md) 
- [3D Construction Process](dam/use_cases/3d_dam_construction/README.md) 
- [2D Acoustic Pulse](dam/use_cases/Acoustic/README.md) 

## Poromechanics

**Validation**

- [Undrained soil column 2D test](poromechanics/validation/undrained_soil_column_2D/README.md) 

**Use cases**

- [Fluid flow in pre-existing fractures network](poromechanics/use_cases/fluid_pumping_2D/README.md)

## Structural Mechanics

**Validation**

- [Beam Eigenvalue Analysis](structural_mechanics/validation/beam_eigenvalue_analysis/README.md)
- [Beam Non-Linear Cantilever](structural_mechanics/validation/beam_nonlinear_cantilever/README.md)
- [Beam Shallow-angled Structure](structural_mechanics/validation/beam_shallow_angled_structure/README.md)
- [Beam Roll Up](structural_mechanics/validation/beam_roll_up/README.md)
- [Truss Two-Bar-Truss Snapthrough](structural_mechanics/validation/truss_snap_through/README.md)
