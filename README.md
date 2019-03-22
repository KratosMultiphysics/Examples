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
- [Kelvin-Helmholtz instability - periodic boundary conditions](fluid_dynamics/use_cases/kelvin_helmholtz_instability/README.md)

**Validation**
- [Body-fitted 100 Re cylinder](fluid_dynamics/validation/body_fitted_cylinder_100Re/README.md)
- [Two-fluids dam break scenario](fluid_dynamics/validation/two_fluid_dam_break/README.md)
- [Two-fluids wave propagation](fluid_dynamics/validation/two_fluid_wave/README.md)

## Structural Mechanics

**Use cases**
- [Disk subjected to centrifugal force - periodic boundary conditions](structural_mechanics/use_cases/periodic_bc_example/README.md)

**Validation**
- [Beam Eigenvalue Analysis](structural_mechanics/validation/beam_eigenvalue_analysis/README.md)
- [Beam Non-Linear Cantilever](structural_mechanics/validation/beam_nonlinear_cantilever/README.md)
- [Beam Shallow-angled Structure](structural_mechanics/validation/beam_shallow_angled_structure/README.md)
- [Beam Roll Up](structural_mechanics/validation/beam_roll_up/README.md)
- [Truss Two-Bar-Truss Snapthrough](structural_mechanics/validation/truss_snap_through/README.md)

## Contact Structural Mechanics

**Validation**
- [Double arch contact benchmark](contact_structural_mechanics/validation/double_arch/README.md)
- [Hertz contact benchmark](contact_structural_mechanics/validation/hertz/README.md)

## Conjugate Heat Transfer (CHT)

**Validation**
- [Cylinder cooling Re = 100 and Pr = 2](conjugate_heat_transfer/validation/cylinder_cooling_Re100_Pr2/README.md)

## Fluid-Structure Interaction (FSI)

**Validation**
- [FSI lid driven cavity](fluid_structure_interaction/validation/fsi_lid_driven_cavity/README.md)
- [Mok benchmark](fluid_structure_interaction/validation/fsi_mok/README.md)
- [Turek benchmark -FSI2](fluid_structure_interaction/validation/fsi_turek_FSI2/README.md)

## MMG remeshing

**Use Cases**
- [Beam 2D](mmg_remeshing_examples/use_cases/beam2D/README.md)
- [Beam 2D Internal interpolation](mmg_remeshing_examples/beam2D_internal_interpolation/README.md)
- [Cavity 2D](mmg_remeshing_examples/use_cases/cavity2D/README.md)
- [Coarse sphere](mmg_remeshing_examples/use_cases/coarse_sphere/README.md)
- [Lamborghini example](mmg_remeshing_examples/use_cases/lamborghini/README.md)
- [Embedded2D](mmg_remeshing_examples/use_cases/embedded_2D/README.md)
- [Channel sphere 2D](mmg_remeshing_examples/use_cases/channel_sphere2D/README.md)
- [Channel sphere 3D](mmg_remeshing_examples/use_cases/channel_sphere3D/README.md)

**Validation**
- [Hessian2D](mmg_remeshing_examples/validation/hessian2D/README.md)
- [Hessian3D](mmg_remeshing_examples/validation/hessian3D/README.md)
- [Bunny example](mmg_remeshing_examples/validation/bunny/README.md)

## Poromechanics

**Use cases**
- [Fluid flow in pre-existing fractures network](poromechanics/use_cases/fluid_pumping_2D/README.md)

**Validation**
- [Undrained soil column 2D test](poromechanics/validation/undrained_soil_column_2D/README.md) 

## Swimming DEM

**Use cases**
- [Small Box Eulerian OW](swimming_dem_fluid_interaction/use_cases/Eulerian_Fluid_Element/One_Way/Small_Box_Eulerian_OW/README.md)
- [Small Box Eulerian TW](swimming_dem_fluid_interaction/use_cases/Eulerian_Fluid_Element/Two_Way/Small_Box_Eulerian_TW/README.md)
- [Small Box Lagrangian OW](swimming_dem_fluid_interaction/use_cases/PFEMFluid_Element/One_Way/Small_Box_Eulerian_OW/README.md)
- [Small Box Lagrangian TW](swimming_dem_fluid_interaction/use_cases/PFEMFluid_Element/Two_Way/Small_Box_Eulerian_TW/README.md)

## Particle Mechanics

**Validation**
- [Granular Flow 2D](particle_mechanics/validation/granular_flow_2D/README.md)




