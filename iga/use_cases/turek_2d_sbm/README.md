# 2D Turek SBM Example

Single-patch SBM/IGA [1,2] version of the 2D Turek benchmark [3].

The example considers the incompressible laminar flow around an immersed circular obstacle in a 2D channel. The geometry follows the standard Turek benchmark configuration: a channel of length `L = 2.5` and height `H = 0.41`, with a circular obstacle of radius `r = 0.05` centered at `(0.2, 0.2)`.

In this example, only the fixed immersed obstacle is considered, while the elastic flag of the full FSI benchmark is not included. The flow enters from the left side of the channel, develops around the no-slip immersed obstacle, and leaves through the right outlet. For the CFD3 regime, the flow develops an unsteady wake behind the obstacle.

This example uses:

- the Turek NURBS skin for the immersed cylinder,
- a single Cartesian background patch generated with `NurbsGeometryModelerSbm`,
- SBM/IGA to impose the immersed no-slip condition on the obstacle,
- Turek-style boundary conditions:
  - ramped parabolic inlet velocity,
  - no-slip top and bottom walls,
  - no-slip immersed object,
  - zero outlet pressure.

## Physical Parameters

The fluid is modeled as an incompressible Newtonian fluid:

```json
{
  "name": "Newtonian2DLaw",
  "Variables": {
    "DENSITY": 1000.0,
    "DYNAMIC_VISCOSITY": 1.0,
    "PENALTY_FACTOR": 0.0
  }
}
```

Therefore:

- density: `rho = 1000.0 kg/m^3`,
- dynamic viscosity: `mu = 1.0 kg/(m s)`,
- kinematic viscosity: `nu = mu / rho = 1.0e-3 m^2/s`.

Setting `PENALTY_FACTOR = 0.0` activates the skew-symmetric penalty-free Nitsche formulation. In this example, this formulation is used both for the body-fitted boundary imposition and for the SBM imposition on the immersed object.

The imposed mean inlet velocity is:

```text
U_mean = 2.0 m/s
```

Using the cylinder diameter `D = 0.1`, the Reynolds number is:

```text
Re = U_mean * D / nu = 2.0 * 0.1 / 1.0e-3 = 200
```

This corresponds to the CFD3 regime of the Turek benchmark.

## Boundary Conditions

### Inlet

A time-ramped parabolic velocity profile is prescribed at the inlet:

```json
"VELOCITY": [
  "0.5*(1 - cos(3.141592653589793 * (t + 2.0 - sqrt((t - 2.0)*(t - 2.0))) / 4.0)) * (2.0 * 1.5 * 4 * y * (0.41 - y) / (0.41 * 0.41))",
  "0.0"
]
```

The spatial profile is the standard Turek parabolic inlet profile:

```text
u_x(y) = 1.5 * U_mean * 4 y (H - y) / H^2
u_y(y) = 0
```

with:

```text
H = 0.41
U_mean = 2.0
```

The maximum inlet velocity is therefore:

```text
u_max = 1.5 * U_mean = 3.0 m/s
```

The cosine factor smoothly ramps the inlet velocity from zero to the full profile during the first `2.0 s` of the simulation.

### Walls

No-slip conditions are imposed on the top and bottom channel walls:

```text
u = 0
```

### Immersed obstacle

The circular obstacle is represented by the NURBS skin in:

```text
turek_nurbs.json
```

The no-slip condition is imposed on the immersed boundary using the SBM/IGA formulation:

```text
u = 0 on the immersed object
```

### Outlet

A zero pressure condition is imposed at the outlet:

```text
p = 0
```

This fixes the pressure reference level for the incompressible flow problem.

## Initial Condition

The simulation starts from rest:

```text
u = 0
p = 0
```

The inlet velocity is then ramped smoothly during the initial transient.

## Time Integration

The actual time step and final time are set in:

```text
ProjectParameters_2D_fluid.json
```

### Mesh3

```json
"number_of_knot_spans": [200, 33]
```

Approximate background mesh size:

```text
dx = 2.5 / 200  = 0.0125
dy = 0.41 / 33 ≈ 0.0124
```

<img width="1620" height="864" alt="geometry_plot" src="https://github.com/user-attachments/assets/f586d1fb-9c1c-4121-95a8-9e20d6e6f758" />

### Mesh4

```json
"number_of_knot_spans": [400, 66]
```

Approximate background mesh size:

```text
dx = 2.5 / 400  = 0.00625
dy = 0.41 / 66 ≈ 0.00621
```

<img width="1620" height="864" alt="geometry_plot" src="https://github.com/user-attachments/assets/661ac8e1-d287-456c-b041-557c8d89086b" />

## Files

- `ProjectParameters_2D_fluid.json`: fluid setup and boundary conditions
- `FluidMaterials.json`: 2D Newtonian material
- `turek_nurbs.json`: immersed object skin
- `run_and_post_nurbs.py`: run the case and create plots and GIFs
- `plot_geometry.py`: plot the background mesh, skin boundary, and surrogate boundary

## Python Dependencies

The post-processing scripts require:

- `numpy`
- `matplotlib`
- `imageio`

To plot only the geometry:

```bash
python3 plot_geometry.py
```

## Run

```bash
python3 run_and_post_nurbs.py
```

<img width="2240" height="800" alt="final_step_fields" src="https://github.com/user-attachments/assets/cbc82205-3a2a-4c58-8547-dd2f9515ec7b" />


Velocity and pressure with a very fine mesh:

https://github.com/user-attachments/assets/b85a74d0-d801-403c-bd0a-50199e9f0eab


https://github.com/user-attachments/assets/9ff7637b-e2d8-4c65-980a-8d9cf8b28627




## Outputs

The script generates:

- `final_step_fields.png`
- `velocity.gif`
- `pressure.gif`
- `geometry_plot.png`

Internal frame caches are written into:

- `frames_velocity`
- `frames_pressure`


## Local Refinement Requirement

The present example uses globally refined Cartesian background patches. This is useful for testing and debugging the SBM/IGA formulation, but it is not the most efficient strategy for obtaining high-quality solutions around the embedded obstacle.

For the Turek benchmark, the relevant flow features are concentrated near the immersed cylinder and in the wake region. Therefore, a local refinement strategy around the embedded object is needed in order to obtain solutions that are properly comparable with body-fitted reference results, without increasing the number of degrees of freedom globally.

Possible refinement strategies include:

- adaptive refinement based on THB-splines, following the hierarchical spline approach introduced in [4];
- multipatch local refinement, where a refined patch is inserted around the embedded object and coupled to the background patch using the Gap-SBM approach [5].

The second option is particularly natural in the present framework: the refined patch can be placed only where additional resolution is needed, while the Gap-SBM coupling allows non-matching patches with different mesh sizes and parametrizations to be connected without introducing additional degrees of freedom.

## References

[1] Antonelli, N., Aristio, R., Gorgi, A., Zorrilla, R., Rossi, R., Scovazzi, G., and Wüchner, R., *The Shifted Boundary Method in Isogeometric Analysis*, Computer Methods in Applied Mechanics and Engineering, Volume 430, 2024, 117228.

[2] Antonelli, N., Gorgi, A., Zorrilla, R., and Rossi, R., *Isogeometric analysis for non-Newtonian viscoplastic fluids: challenges for non-smooth solutions*, Computer Methods in Applied Mechanics and Engineering, Volume 447, 2025, 118386.

[3] Turek, S. and Hron, J., *Proposal for numerical benchmarking of fluid-structure interaction between an elastic object and laminar incompressible flow*, 2006.

[4] Giannelli, C., Jüttler, B., and Speleers, H., *THB-splines: The truncated basis for hierarchical splines*, Computer Aided Geometric Design, Volume 29, Issue 7, 2012, pp. 485–498.

[5] Antonelli, N., Gorgi, A., Zorrilla, R., and Rossi, R., *Isogeometric multipatch coupling with arbitrary refinement and parametrization using the Gap–Shifted Boundary Method*, Computer Methods in Applied Mechanics and Engineering, Volume 456, 2026, 118913.
