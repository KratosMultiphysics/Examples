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
- [Body-fitted 100 Re cylinder](https://github.com/KratosMultiphysics/Examples/blob/master/fluid_dynamics/validation/body_fitted_cylinder_100Re/README.md)
- [Embedded moving cylinder](https://github.com/KratosMultiphysics/Examples/tree/master/fluid_dynamics/validation/embedded_moving_cylinder/README.md)
- [Transonic flow around a NACA0012 profile](https://github.com/KratosMultiphysics/Examples/tree/master/fluid_dynamics/validation/compressible_naca_0012_Ma_0.8/README.md)
- [Transonic flow around a NACA0012 profile at a 3&deg; angle](https://github.com/KratosMultiphysics/Examples/tree/master/fluid_dynamics/validation/compressible_naca_0012_Ma_0.8_aoa_3/README.md)
- [Sod Shock tube](https://github.com/KratosMultiphysics/Examples/tree/master/fluid_dynamics/validation/compressible_sod_shock_tube/README.md)
- [Supersonic flow in Woodward and Colella's Mach 3 step](https://github.com/KratosMultiphysics/Examples/tree/master/fluid_dynamics/validation/compressible_step_woodward_colella/README.md)
- [Two-fluids dam break scenario](https://github.com/KratosMultiphysics/Examples/blob/master/fluid_dynamics/validation/two_fluid_dam_break/README.md)
- [Two-fluids wave propagation](https://github.com/KratosMultiphysics/Examples/blob/master/fluid_dynamics/validation/two_fluid_wave/README.md)

## Structural Mechanics

**Use cases**
- [Disk subjected to centrifugal force - periodic boundary conditions](structural_mechanics/use_cases/periodic_bc_example/README.md)

**Validation**
- [Beam Eigenvalue Analysis](structural_mechanics/validation/beam_eigenvalue_analysis/README.md)
- [Beam Non-Linear Cantilever](structural_mechanics/validation/beam_nonlinear_cantilever/README.md)
- [Beam Non-Linear 3D Cantilever (Bathe & Bolourchi)](structural_mechanics/validation/beam_nonlinear_cantilever3D_bathe/README.md)
- [Beam Shallow-angled Structure](structural_mechanics/validation/beam_shallow_angled_structure/README.md)
- [Beam Roll Up](structural_mechanics/validation/beam_roll_up/README.md)
- [Truss Two-Bar-Truss Snapthrough](structural_mechanics/validation/truss_snap_through/README.md)
- [Two-Dimensional Circular Truss-Arch Snapthrough](structural_mechanics/validation/two_dimensional_circular_truss_arch_snapthrough/README.md)
- [Membrane Hemisphere Verification and Eigenvalue Computation](structural_mechanics/validation/membrane_hemisphere/README.md)
- [Membrane Catenoid Form-Finding](structural_mechanics/validation/catenoid_formfinding/README.md)
- [Membrane Four Point Sail Form-Finding](structural_mechanics/validation/four_point_sail_formfinding/README.md)

## Contact Structural Mechanics

**Use Cases**
- [Cylinders](contact_structural_mechanics/use_cases/cylinders/README.md)
- [Ironing with die](contact_structural_mechanics/use_cases/ironing_with_die_3D/README.md)
- [Cylinder in ring](contact_structural_mechanics/use_cases/in_ring/README.md)
- [Hyperelastic tubes contacting](contact_structural_mechanics/use_cases/hyperelastic_tubes//README.md)
- [Tooth model](contact_structural_mechanics/use_cases/tooth_model/README.md)
- [Arc block](contact_structural_mechanics/use_cases/arc_block/README.md)
- [Gears](contact_structural_mechanics/use_cases/gears/README.md)
- [Self-contact](contact_structural_mechanics/use_cases/self_contact/README.md)

**Validation**
- [Double arch contact benchmark](contact_structural_mechanics/validation/double_arch/README.md)
- [Hertz benchmark](contact_structural_mechanics/validation/hertz/README.md)
- [Full Hertz benchmark](contact_structural_mechanics/validation/hertz_full/README.md)
- [Shallow ironing](contact_structural_mechanics/validation/shallow_ironing_3D/README.md)
- [Press fit](contact_structural_mechanics/validation/press_fit/README.md)

## Conjugate Heat Transfer (CHT)

**Validation**
- [Cylinder cooling Re = 100 and Pr = 2](conjugate_heat_transfer/validation/cylinder_cooling_Re100_Pr2/README.md)

## Fluid-Structure Interaction (FSI)

**Validation**
- [FSI lid driven cavity](https://github.com/KratosMultiphysics/Examples/blob/master/fluid_structure_interaction/validation/fsi_lid_driven_cavity/README.md)
- [Mixer with flexible blades (embedded)](https://github.com/KratosMultiphysics/Examples/blob/master/fluid_structure_interaction/validation/embedded_fsi_mixer_Y/README.md)
- [Mok benchmark](https://github.com/KratosMultiphysics/Examples/blob/master/fluid_structure_interaction/validation/fsi_mok/README.md)
- [Mok benchmark (embedded)](https://github.com/KratosMultiphysics/Examples/blob/master/fluid_structure_interaction/validation/embedded_fsi_mok/README.md)
- [Turek benchmark - FSI2](https://github.com/KratosMultiphysics/Examples/blob/master/fluid_structure_interaction/validation/fsi_turek_FSI2/README.md)

## MMG remeshing

**Use Cases**
- [Beam 2D](mmg_remeshing_examples/use_cases/beam2D/README.md)
- [Beam 2D SPR](mmg_remeshing_examples/use_cases/beam_spr/README.md)
- [Beam 2D Internal interpolation](mmg_remeshing_examples/use_cases/beam2D_internal_interpolation/README.md)
- [Contact 2D SPR](mmg_remeshing_examples/use_cases/contact_spr/README.md)
- [Contact 2D Hessian](mmg_remeshing_examples/use_cases/contact_hessian/README.md)
- [Contact Hertz Hessian 2D](mmg_remeshing_examples/use_cases/hertz_hessian/README.md)
- [Contacting cylinders 3D](mmg_remeshing_examples/use_cases/contacting_cylinders/README.md)
- [Cavity 2D](mmg_remeshing_examples/use_cases/cavity2D/README.md)
- [Coarse sphere](mmg_remeshing_examples/use_cases/coarse_sphere/README.md)
- [Level-set demisphere-plane](mmg_remeshing_examples/use_cases/level_set_demisphere_plane/README.md)
- [Lamborghini example](mmg_remeshing_examples/use_cases/lamborghini/README.md)
- [Embedded2D](mmg_remeshing_examples/use_cases/embedded_2D/README.md)
- [Channel sphere 2D](mmg_remeshing_examples/use_cases/channel_sphere2D/README.md)
- [Channel sphere 3D](mmg_remeshing_examples/use_cases/channel_sphere3D/README.md)
- [Isosurface box](mmg_remeshing_examples/use_cases/test_box/README.md)

**Validation**
- [Hessian2D](mmg_remeshing_examples/validation/hessian2D/README.md)
- [Hessian3D](mmg_remeshing_examples/validation/hessian3D/README.md)
- [Bunny example](mmg_remeshing_examples/validation/bunny/README.md)


## ParMMG remeshing
**Use Cases**

- [Body-fitted cylinder 3D](parmmg_remeshing_examples/use_cases/body_fitted_hessian_cylinder3D/README.md)
- [Embedded building 3D](parmmg_remeshing_examples/use_cases/embedded_level_set_building3D/README.md)

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
- [Cylinder on inclined plane 2D](particle_mechanics/validation/cylinder_on_inclined_plane/README.md)

## PFEM2

**Use cases**
- [Dam break](pfem2/use_cases/dam_break/README.md)
- [No Newtonian 2D](pfem2/use_cases/no_newtonian_2d/README.md)
- [No Newtonian 3D](pfem2/use_cases/no_newtonian_3d/README.md)
- [Rayleigh](pfem2/use_cases/rayleigh/README.md)

## Monte Carlo & Multilevel Monte Carlo

**Use Cases**
- [Compressible potential flow problem](multilevel_monte_carlo/use_cases/compressible_potential_flow/README.md)
- [Fluid dynamics building problem](multilevel_monte_carlo/use_cases/fluid_dynamics_building)
- [Wind engineering rectangle problem](multilevel_monte_carlo/use_cases/wind_engineering_rectangle)
- [Wind engineering CAARC problem](multilevel_monte_carlo/use_cases/wind_engineering_CAARC)
    - [Steady inlet wind engineering CAARC problem](multilevel_monte_carlo/use_cases/wind_engineering_CAARC/steady_inlet_monte_carlo)
    - [Turbulent inlet wind engineering CAARC problem](multilevel_monte_carlo/use_cases/wind_engineering_CAARC/turbulent_inlet_monte_carlo)
- [Wind engineering twisted building problem with MPI parallelism](multilevel_monte_carlo/use_cases/wind_engineering_twistedbuilding_mpi)

**Validation Cases**
- [Elliptic benchmark](multilevel_monte_carlo/validation/elliptic_benchmark)

## Shape Optimization

**Use cases**
- [Multi Constraint Optimization 3D Hook](shape_optimization/use_cases/10_Multi_Constraint_Optimization_3D_Hook)
- [Smooth Surface Wrapping - Stanford Bunny](shape_optimization/use_cases/11_Shape_Update_Optimization_Stanford_Bunny)
- [Strain Energy Minimization - 3D Shell](shape_optimization/use_cases/02_Strain_Energy_Minimization_3D_Shell)
- [Bead Optimization Plate](shape_optimization/use_cases/06_bead_optimization_plate)

## Convection Diffusion
**Validation**
- [Convection gaussian hill problem](convection_diffusion/validation/gaussian_hill_explicit)
- [Convection-Diffusion gaussian hill problem](convection_diffusion/validation/gaussian_hill_with_diffusion_explicit)
- [Rotating pulse problem](convection_diffusion/validation/rotating_pulse_explicit)
- [Space and time convergence tests](convection_diffusion/validation/space_time_convergence_test)
