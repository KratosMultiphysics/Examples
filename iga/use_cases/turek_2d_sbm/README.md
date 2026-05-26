# 2D Turek SBM Example

Single-patch SBM/IGA version of the 2D Turek benchmark.

This example uses:
- the unordered Turek NURBS skin for the immersed cylinder
- a single Cartesian background patch generated with `NurbsGeometryModelerSbm`
- Turek-style boundary conditions: ramped parabolic inlet, no-slip walls and immersed object, zero outlet pressure

## Files

- `ProjectParameters_2D_fluid.json`: fluid setup and boundary conditions
- `FluidMaterials.json`: 2D Newtonian material
- `turek_nurbs.json`: immersed object skin
- `run_and_post_nurbs.py`: run the case and create the plots and GIFs
- `plot_geometry.py`: plot the background mesh, skin boundary, and surrogate boundary

## Python Dependencies

The post-processing scripts require:
- `numpy`
- `matplotlib`
- `imageio`

To plot only the geometry:

```bash
cd /home/nantonelli/Examples/iga/use_cases/turek_2d_sbm
python3 plot_geometry.py
```
"number_of_knot_spans": [200, 33], -> "Mesh3"
<img width="1620" height="864" alt="geometry_plot" src="https://github.com/user-attachments/assets/f586d1fb-9c1c-4121-95a8-9e20d6e6f758" />

"number_of_knot_spans": [400, 66], -> "Mesh4"
<img width="1620" height="864" alt="geometry_plot" src="https://github.com/user-attachments/assets/1abcd585-90e0-415d-ac3e-f4e5af456f98" />


## Run

```bash
cd /home/nantonelli/Examples/iga/use_cases/turek_2d_sbm
python3 run_and_post_nurbs.py
```




## Outputs

- `final_step_fields.png`
- `velocity.gif`
- `pressure.gif`
- `geometry_plot.png`

Internal frame caches are written into:
- `frames_velocity`
- `frames_pressure`
