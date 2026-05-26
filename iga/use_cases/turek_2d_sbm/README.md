# 2D Turek SBM Example

Single-patch SBM/IGA version of the classical 2D Turek cylinder benchmark.

This example uses:
- the unordered Turek NURBS skin for the immersed cylinder
- a single Cartesian background patch generated with `NurbsGeometryModelerSbm`
- Turek-style boundary conditions: ramped parabolic inlet, no-slip walls and cylinder, zero outlet pressure

## Files

- `ProjectParameters_2D_fluid.json`: fluid setup and boundary conditions
- `FluidMaterials.json`: 2D Newtonian material
- `turek_nurbs_unordered.json`: immersed cylinder skin
- `run_and_post_nurbs.py`: run the case and create the plots and GIFs
- `plot_geometry.py`: plot the background mesh, skin boundary, and surrogate boundary

## Python Dependencies

The post-processing scripts require:
- `numpy`
- `matplotlib`
- `imageio`

If one of them is missing, the script stops immediately with a clear error message.

If a `latex` executable is available, matplotlib uses it for text rendering. Otherwise the scripts fall back to Computer Modern mathtext.

## Run

```bash
cd /home/nantonelli/Examples/iga/use_cases/turek_2d_sbm
python3 run_and_post_nurbs.py
```

To plot only the geometry:

```bash
cd /home/nantonelli/Examples/iga/use_cases/turek_2d_sbm
python3 plot_geometry.py
```

## Outputs

- `final_step_fields.png`
- `velocity.gif`
- `pressure.gif`
- `geometry_plot.png`

Internal frame caches are written into:
- `_frame_cache`
- `frames_velocity`
- `frames_pressure`
