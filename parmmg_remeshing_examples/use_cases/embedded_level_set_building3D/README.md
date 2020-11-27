# Embedded building 3D with MPI level-set based refinement

**Author:** Marc Núñez Corbacho

**Kratos version:** 8.1

**MMG version:** 5.5.2

**ParMMG version:** 1.3.0

**Source files:** [MPI Embedded building 3D](https://github.com/KratosMultiphysics/Examples/tree/master/parmmg_remeshing_examples/use_cases/embedded_level_set_building3D/source)

**Application dependencies:** `FluidDynamicsApplication`, `LinearSolversApplications`, `MeshingApplication`, `MetisApplication`, `TrilinosApplication`

To run this example execute:

    export OMP_NUM_THREADS=1
    mpirun -n nprocs python3 MainKratos.py

Where `nprocs` is the number of processors to use in the MPI run.

This example adaptively refines a background mesh according to the distance to a building. The refinement is then driven by the distance field only, and we can customize the size of the elements according to this, depending on how close/far are they from the geometry. Check the instructions below to modify these parameters.

This considerably improves the representation of the building on the mesh. It then start a a fluid dynamic analysis with a constant logarithmic inlet, with the geometry embedded and represented by a distance field.

Initial discretization
![initial](data/initial_building_cut.png)

Final discretization
![final](data/final_building_cut.png)
![final_zoom](data/final_building_cut_zoom.png)

Velocity field
![gif](data/embedded_building_gif.gif)

## How to use

In  [ProjectParameters.json](source/ProjectParameters.json):

- ["end_time"](source/ProjectParameters.json#L6) to change the total length of the simulation.
- ["time_step"](source/ProjectParameters.json#L64) to change the time step used.

In  [RemeshingParameters.json](source/RemeshingParameters.json):

- ["number_of_iterations"](source/RemeshingParameters.json#L2) to change the total number of consecutive remeshing steps.
- ["minimal_size"](source/RemeshingParameters.json#L4) to set the minimal size of the mesh. This will be the size set at `distance=0.0'.
- ["maximal_size"](source/RemeshingParameters.json#L5) to set the maximal size of the mesh. This will be the size set at `distance=boundary_layer_max_distance'.
- ["boundary_layer_max_distance"](source/RemeshingParameters.json#L8) to set the distance up to where the refinement will be performed. Elements outside this distance will keep its initial size.
- ["interpolation"](source/RemeshingParameters.json#L9) to set the interpolation set between the minimal_size and the maximal_size. Possible interpolation settings are: `constant`, `linear`, `exponential`.