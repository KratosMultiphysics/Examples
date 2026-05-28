# 3D Toyota SBM Examples

This directory contains the shared geometry for the Toyota SBM examples together with two split use cases:

- [steady_stokes/README.md](/home/nantonelli/Examples/iga/use_cases/toyota_3d_sbm/steady_stokes/README.md): steady-state-style 3D Stokes example
- [transient_navier_stokes/README.md](/home/nantonelli/Examples/iga/use_cases/toyota_3d_sbm/transient_navier_stokes/README.md): transient 3D Navier-Stokes example

The shared files stored in this parent folder are:

- `toyota_immersed_surface_sbm.mdpa`: common immersed Toyota surface mesh used by both subcases
- `FluidMaterials.json`: common material definition

The split layout avoids duplicating the immersed `.mdpa` file while keeping the steady and transient examples documented separately.
