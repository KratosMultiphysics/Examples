# 3D Toyota SBM Example

This use case demonstrates a 3D immersed-body fluid analysis with the Surrogate Boundary Method (SBM) in the Kratos IGA Application. The Toyota body is not discretized with a body-fitted fluid mesh. Instead, the car surface is provided as an immersed skin in `toyota_immersed_surface_sbm.mdpa`, while the fluid is solved on a structured Cartesian background NURBS volume generated in the JSON settings.

## SBM Philosophy

The main idea of SBM is to decouple the geometry description from the analysis mesh:

- the immersed body is described only by a surface mesh
- the analysis domain is a simple Cartesian background volume
- boundary conditions are imposed on a surrogate boundary built from the background mesh, rather than on a body-fitted mesh

For this kind of problem, that is useful because the geometry can come from an external triangulated surface, for example an STL-like workflow prepared outside Kratos and then exported to `.mdpa`. The analysis mesh can then be changed independently by editing the background box and its resolution directly in the parameter files.

In this example, the no-slip condition on the immersed Toyota surface is imposed weakly on `IgaModelPart.SBM_Support_inner` with `SbmFluidConditionDirichlet`. The formulation includes skew-symmetric Nitsche terms, and the example is configured in penalty-free mode on the immersed surrogate boundary through `PENALTY_FACTOR: 0.0` in `FluidMaterials.json`.

## Geometry and Modelers

Both `ProjectParameters_3D_fluid.json` and `ProjectParameters_3D_fluid_steady_state.json` follow the same three-step geometry pipeline:

1. `import_mdpa_modeler` imports `toyota_immersed_surface_sbm.mdpa` into `initial_skin_model_part_in`.
2. `NurbsGeometryModelerSbm` creates the background 3D Cartesian NURBS volume.
3. `IgaModelerSbm` builds the fluid domain and the fitted/surrogate support conditions needed by the SBM formulation.

The main model parts created by the setup are:

- `IgaModelPart.FluidDomain`: background fluid volume
- `IgaModelPart.SBM_Support_inner`: surrogate boundary associated with the immersed Toyota body
- `IgaModelPart.SBM_Support_outer`: outer wall support surfaces of the background box
- `IgaModelPart.Support_inlet`: inlet support surface
- `IgaModelPart.SupportOuterPressure`: outlet pressure support surface

## What You Can Change in the JSON

The most important SBM geometry controls are in the `NurbsGeometryModelerSbm` block:

- `input_filename`: selects the immersed surface mesh to import
- `lower_point_xyz` and `upper_point_xyz`: define the background Cartesian box
- `polynomial_order`: defines the polynomial degree of the background NURBS volume
- `number_of_knot_spans`: defines the Cartesian resolution in each direction
- `lambda_outer`, `lambda_inner`, `number_of_inner_loops`: control the SBM surrogate-boundary construction

In practice, if you want to analyze another immersed geometry, the usual workflow is:

1. generate or export a triangulated surface externally
2. convert it to an `.mdpa` skin mesh
3. replace `toyota_immersed_surface_sbm.mdpa`
4. adapt the background box and the number of knot spans in the JSON files

## Physics in This Folder

This folder contains two related fluid setups:

- `ProjectParameters_3D_fluid.json`: transient monolithic 3D Navier-Stokes case with `NavierStokesElement` and a ramped inlet velocity
- `ProjectParameters_3D_fluid_steady_state.json`: steady-state-style 3D case using `StokesElement` and a constant inlet velocity

The boundary treatment is:

- inlet velocity prescribed on `IgaModelPart.Support_inlet`
- zero outlet pressure prescribed on `IgaModelPart.SupportOuterPressure`
- outer-box support conditions imposed weakly on `IgaModelPart.SBM_Support_outer`
- immersed no-slip condition imposed weakly on `IgaModelPart.SBM_Support_inner`

The material file uses a 3D Newtonian constitutive law. In the current setup:

- `IgaModelPart` uses `DENSITY = 1.0`, `DYNAMIC_VISCOSITY = 1e-3`, and `PENALTY_FACTOR = 1e3` for the fitted support terms on the background box
- `IgaModelPart.SBM_Support_inner` uses `PENALTY_FACTOR = 0.0` for the penalty-free immersed-boundary configuration

## Files

- `ProjectParameters_3D_fluid.json`: transient fluid setup
- `ProjectParameters_3D_fluid_steady_state.json`: steady-state fluid setup
- `FluidMaterials.json`: 3D Newtonian material data and SBM penalty settings
- `toyota_immersed_surface_sbm.mdpa`: immersed Toyota skin used by the SBM modeler
- `run_and_post_nurbs_time.py`: runs the transient case and generates postprocessed GIFs
- `run_and_post_nurbs_steady_state.py`: runs the steady case and generates final plots
- `plot_conditions.py`: visualizes the surrogate faces created by the geometry/modeler setup

## Python Dependencies

The post-processing scripts use:

- `numpy`
- `matplotlib`
- `imageio` for GIF writing in the transient script

If a `latex` executable is available, the plotting scripts can use Computer Modern style math text. Otherwise they fall back to standard matplotlib text rendering.

## Run

Transient case:

```bash
cd /home/nantonelli/Examples/iga/use_cases/toyota_3d_sbm
python3 run_and_post_nurbs_time.py
```

Steady-state case:

```bash
cd /home/nantonelli/Examples/iga/use_cases/toyota_3d_sbm
python3 run_and_post_nurbs_steady_state.py
```

Geometry / surrogate-condition plot:

```bash
cd /home/nantonelli/Examples/iga/use_cases/toyota_3d_sbm
python3 plot_conditions.py
```

## Outputs

Transient script:

- `particles_trails.gif`
- `cut_contour_x_lt_0.gif`
- `plane_x_eq_0_contour.gif`

Steady-state script:

- `steady_3d_velocity_pressure.png`
- `steady_plane_x0_velocity.png`
- `steady_plane_x0_pressure.png`

Geometry helper:

- `surrogate_faces_plot.png`
