# 3D Toyota SBM Steady Stokes Example

Single-patch 3D SBM/IGA [1,2] example for a steady-state-style incompressible Stokes flow around an immersed Toyota-like car body. The body is not surrounded by a body-fitted fluid mesh. Instead, the geometry is provided through the shared immersed surface `../toyota_immersed_surface_sbm.mdpa`, while the fluid is solved on a structured Cartesian background NURBS volume generated directly from the JSON settings.

This folder contains the steady Stokes variant of the Toyota SBM example:

- steady-state-style 3D Stokes case in `ProjectParameters_3D_fluid_steady_state.json`
- post-processing driver `run_and_post_nurbs_steady_state.py`
- geometry helper `plot_conditions.py`

The example uses:

- the immersed Toyota surface mesh in `.mdpa` format
- a single Cartesian background NURBS volume created with `NurbsGeometryModelerSbm`
- `IgaModelerSbm` to generate the fluid domain and the surrogate support boundaries
- SBM/IGA to impose the immersed no-slip condition without body-fitted remeshing
- weak boundary conditions on the outer box walls, inlet, outlet, and immersed body

The aim of the example is methodological: it demonstrates how a 3D external flow problem can be solved with the SBM inside the Kratos IGA Application.

## Physical Parameters

The material model is defined in the shared file `../FluidMaterials.json`:

```json
{
  "name": "Newtonian3DLaw",
  "Variables": {
    "DENSITY": 1.0,
    "DYNAMIC_VISCOSITY": 1e-3,
    "PENALTY_FACTOR": 1e3
  }
}
```

For the immersed SBM boundary, a second property block is assigned:

```json
{
  "name": "Newtonian3DLaw",
  "Variables": {
    "PENALTY_FACTOR": 0.0
  }
}
```

Therefore:

- density: `rho = 1.0`
- dynamic viscosity: `mu = 1.0e-3`
- kinematic viscosity: `nu = mu / rho = 1.0e-3`

The role of the penalty parameters is:

- `IgaModelPart` uses `PENALTY_FACTOR = 1e3` for the fitted support conditions associated with the background box
- `IgaModelPart.SBM_Support_inner` uses `PENALTY_FACTOR = 0.0`, which activates the penalty-free skew-symmetric Nitsche-style SBM treatment on the immersed surrogate boundary [1]

## Geometry

### Immersed car surface

The immersed geometry is stored in the parent Toyota folder:

```text
../toyota_immersed_surface_sbm.mdpa
```

The imported surface contains:

- `26939` nodes
- `29860` surface conditions

From the coordinates in the `.mdpa` file, the axis-aligned extent of the immersed body is:

```text
x in [-0.111937578, 0.074097578]   -> width  = 0.186035156
y in [ 0.055194000, 0.233533669]   -> height = 0.178339669
z in [ 0.244411751, 0.699946535]   -> length = 0.455534784
```

In this setup, the imposed inlet velocity is aligned with the `z` direction, so `z` is the streamwise direction.

### Background box

The Cartesian background volume is:

```json
"lower_point_xyz": [-0.2142325, -0.04246225, 0.01640625],
"upper_point_xyz": [ 0.1763925,  0.3481627,  1.5]
```

Hence the fluid box dimensions are:

```text
Lx = 0.390625
Ly = 0.39062495
Lz = 1.48359375
```

## Background Mesh and SBM Construction

The background NURBS volume is created with `NurbsGeometryModelerSbm`. In this case the polynomial order is:

```json
"polynomial_order": [1, 1, 1]
```

Higher-order B-splines can also be used by increasing `polynomial_order`. This usually improves approximation quality, but it also increases the number of integration points required in the elements and boundary conditions, and therefore the computational cost of the analysis. For low-Reynolds-number flows, it can make good sense to use a coarser background mesh together with a higher polynomial order, since the solution is typically smoother and the additional approximation power can be more effective than refining the mesh uniformly.

The knot-span counts are:

```json
"number_of_knot_spans": [25, 25, 70]
```

This corresponds to a structured Cartesian resolution of:

```text
dx = 0.390625   / 25 = 0.015625
dy = 0.39062495 / 25 ≈ 0.015625
dz = 1.48359375 / 70 ≈ 0.0211942
```

The surrogate-boundary controls are:

- `lambda_outer = 0.5`
- `lambda_inner = 0.0`
- `number_of_inner_loops = 1`

## Geometry Pipeline and Model Parts

`ProjectParameters_3D_fluid_steady_state.json` follows this three-stage setup:

1. `import_mdpa_modeler` imports `../toyota_immersed_surface_sbm.mdpa` into `initial_skin_model_part_in`.
2. `NurbsGeometryModelerSbm` creates the background Cartesian NURBS volume and classifies the immersed geometry relative to the background mesh.
3. `IgaModelerSbm` creates the analysis elements and support conditions needed by the SBM fluid formulation.

The main model parts are:

- `IgaModelPart.FluidDomain`: background volume where the fluid equations are solved
- `IgaModelPart.SBM_Support_inner`: immersed surrogate boundary associated with the Toyota body
- `IgaModelPart.SBM_Support_outer`: outer wall support surfaces of the box
- `IgaModelPart.Support_inlet`: inlet support surface
- `IgaModelPart.SupportOuterPressure`: outlet pressure support surface

The immersed skin itself is also kept as a separate model part and its nodal velocity is fixed to zero. The actual fluid boundary condition, however, is imposed weakly on the surrogate boundary `IgaModelPart.SBM_Support_inner`, not by meshing the fluid to the true car surface.

## Governing Equations and Solver

This folder solves the Stokes variant:

- `StokesElement`
- `solver_type = monolithic_iga`
- `time_scheme = bdf2_higher_order_vms`
- `analysis_type = non_linear`

The nominal time data are:

```json
"start_time": 0.0,
"end_time": 5.0,
"time_step": 1e20
```

This is not a dedicated stationary solver. Instead, it reuses the monolithic IGA fluid infrastructure with a practically infinite time step, so the run behaves as a single-step Stokes solve for documentation and post-processing purposes.

The linear solver is:

```json
"solver_type": "bicgstab",
"preconditioner_type": "ilu0",
"tolerance": 1.0e-14,
"max_iteration": 1000,
"scaling": true
```

The nonlinear tolerances are:

- relative velocity tolerance: `1e-11`
- absolute velocity tolerance: `1e-11`
- relative pressure tolerance: `1e-9`
- absolute pressure tolerance: `1e-9`

## Boundary Conditions

The box uses six faces. In the `IgaModelerSbm` setup:

- `brep_ids [2]` define the inlet support
- `brep_ids [3]` define the outlet pressure support
- `brep_ids [4,5,6,7]` define the outer wall supports

The immersed Toyota boundary is handled by:

- `SbmFluidConditionDirichlet` on `IgaModelPart.SBM_Support_inner`

### Outer box walls

```text
u = (0, 0, 0)
```

is imposed weakly on `IgaModelPart.SBM_Support_outer` through `SupportFluidCondition`.

### Immersed Toyota body

```text
u = (0, 0, 0)
```

The true surface nodes in `skin_model_part.inner` are assigned zero velocity, and the fluid boundary condition is weakly transferred to the surrogate boundary `IgaModelPart.SBM_Support_inner`.

### Outlet

```text
p = 0
NORMAL_STRESS = (0, 0, 0)
```

is imposed on `IgaModelPart.SupportOuterPressure`.

### Inlet

The Stokes case uses a constant inlet velocity:

```text
u = (0, 0, 2.0)
```

## Reynolds Number

Using:

```text
U_ref = 2.0
nu    = 1.0e-3
L_ref = x_max - x_min = 0.186035156
```

gives the reference scale:

```text
Re_L = U_ref * L_ref / nu
     = 2.0 * 0.186035156 / 1.0e-3
     ≈ 372.07
```

For this Stokes example, that Reynolds number is only a reference scale for the chosen geometry and boundary data. Inertia is not part of the equations actually solved in this folder.

## Initial Condition

The JSON file does not prescribe a separate nonzero initial field. In practice, the analysis starts from the default rest state.

## Post-Processing Content

### `plot_conditions.py`

This helper script rebuilds the geometry/modeler setup and plots the surrogate boundary faces in 3D. It is useful to inspect which background faces have been selected by the SBM construction around the immersed vehicle and around the outer box.

Its output file is:

- `surrogate_faces_plot.png`

### `run_and_post_nurbs_steady_state.py`

The steady Stokes script writes:

- a 3D cut figure of velocity magnitude and pressure
- a plane plot of velocity magnitude at `x ≈ 0`
- a plane plot of pressure at `x ≈ 0`

The output files are:

- `steady_3d_velocity_pressure.png`
- `steady_plane_x0_velocity.png`
- `steady_plane_x0_pressure.png`

## Files

- `ProjectParameters_3D_fluid_steady_state.json`: steady-state-style 3D Stokes setup
- `../FluidMaterials.json`: shared 3D Newtonian material data and penalty settings
- `../toyota_immersed_surface_sbm.mdpa`: shared immersed Toyota surface mesh
- `run_and_post_nurbs_steady_state.py`: steady Stokes solver driver and static post-processing
- `plot_conditions.py`: surrogate-face visualization utility

## Python Dependencies

The post-processing scripts use:

- `numpy`
- `matplotlib`

## What You Can Change

The standard workflow for another immersed geometry is:

1. export or generate the external surface elsewhere
2. convert it to a Kratos `.mdpa` skin
3. replace `../toyota_immersed_surface_sbm.mdpa`
4. adapt the background box so the new body is properly enclosed
5. refine `number_of_knot_spans` to obtain adequate resolution

## Run

Steady-state-style Stokes case:

```bash
cd /home/nantonelli/Examples/iga/use_cases/toyota_3d_sbm/steady_stokes
python3 run_and_post_nurbs_steady_state.py
```

Geometry / surrogate-boundary plot:

```bash
cd /home/nantonelli/Examples/iga/use_cases/toyota_3d_sbm/steady_stokes
python3 plot_conditions.py
```

## Local Refinement Requirement

Like the 2D Turek SBM example, this case currently uses a globally structured Cartesian background mesh. This is useful for testing, debugging, and demonstrating the workflow, but it is not the most efficient strategy for serious external-aerodynamics simulations around an immersed vehicle.

More efficient options include:

- adaptive local refinement with THB-splines [3]
- local multipatch refinement around the vehicle and wake, coupled back to the background patch with Gap-SBM [4]

## References

[1] Antonelli, N., Aristio, R., Gorgi, A., Zorrilla, R., Rossi, R., Scovazzi, G., and Wüchner, R., *The Shifted Boundary Method in Isogeometric Analysis*, Computer Methods in Applied Mechanics and Engineering, Volume 430, 2024, 117228. https://doi.org/10.1016/j.cma.2024.117228

[2] Antonelli, N., Gorgi, A., Zorrilla, R., and Rossi, R., *Isogeometric analysis for non-Newtonian viscoplastic fluids: challenges for non-smooth solutions*, Computer Methods in Applied Mechanics and Engineering, Volume 447, 2025, 118386. https://doi.org/10.1016/j.cma.2025.118386

[3] Giannelli, C., Jüttler, B., and Speleers, H., *THB-splines: The truncated basis for hierarchical splines*, Computer Aided Geometric Design, Volume 29, Issue 7, 2012, pp. 485-498. https://doi.org/10.1016/j.cagd.2012.03.025

[4] Antonelli, N., Gorgi, A., Zorrilla, R., and Rossi, R., *Isogeometric multipatch coupling with arbitrary refinement and parametrization using the Gap-Shifted Boundary Method*, Computer Methods in Applied Mechanics and Engineering, Volume 456, 2026, 118913. https://doi.org/10.1016/j.cma.2026.118913
