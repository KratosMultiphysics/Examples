### This is a "How to?" example for using a MPI Randomized Singular Value Decomposition (rSVD).
To test the rSVD, it is needed to compile the [RomApplication](https://github.com/KratosMultiphysics/Kratos/tree/master/applications/RomApplication) of Kratos.

This tool can be tested through two options:
* Using Kratos Multiphysics.
  * Build and write the snapshots matrix with Kratos Multiphysics capabilities ([FluidDynamicsApplication (https://github.com/KratosMultiphysics/Kratos/tree/master/applications/FluidDynamicsApplication)). 
  * Read the snapshots matrix.
  * Perform the rSVD.
* As a blackbox.
  * Read the snapshots matrix.
  * Perform the rSVD.
#### The toy model used for this example:

Flow pass a cylinder in 2D (for more details [Body-fitted 100 Re cylinder](https://github.com/KratosMultiphysics/Examples/blob/master/fluid_dynamics/validation/body_fitted_cylinder_100Re/README.md))

<p align="center">
  <img src="https://github.com/KratosMultiphysics/Examples/blob/master/fluid_dynamics/validation/body_fitted_cylinder_100Re/data/body_fitted_cylinder_100Re_v.gif" alt="Body-fitted 100 Re cylinder velocity field [m/s]." style="width: 600px;"/>
</p>

## How to launch the example
### Using Kratos Multiphysics

The goal of the ROM is to cheaply and fastly evaluate the solution for a given parameter of interest $\boldsymbol{\mu}$ (in this example, the inlet velocity of the fluid) 

<p align=center><img height="72.125%" width="72.125%" src="./data/surrogate.png"></p>

To obtain such a ROM, a costly Full Order Model FOM simulation campaign should be launched, and the collected data should be analyzed using a Singular Value Decomposition. The models can be found in a high-dimensional space, requiring the use of HPC (High Performance Computing) tools such as the MPI version of the Randomized Singular Value Decomposition.

To test this tool, first it is needed to build the data from the full order model.

### Requirements

#### Kratos

This example requires the RomApplication and the FluidDynamicsApplication.

If you compiled Kratos, add both these application to the Kratos configure file. 

Linux:
```shell
add_app ${KRATOS_APP_DIR}/FluidDynamicsApplication
add_app ${KRATOS_APP_DIR}/RomApplication
```

Windows:
```shell
CALL :add_app %KRATOS_APP_DIR%/FluidDynamicsApplication
CALL :add_app %KRATOS_APP_DIR%/RomApplication
```

If on the other hand, you are using the precompiled version of Kratos, do

pip:
```shell
pip install KratosRomApplication KratosFluidDynamicsApplication
```
For more details, please refear to [Kratos Multiphysics Installation](https://github.com/KratosMultiphysics/Kratos/blob/master/INSTALL.md).

The files needed to launch the simulations are the following:
* MainKratos.py (Import Kratos, run simulation, and write snapshots matrix).
* ProjectParameters.json (Configuration settings for solvers, processes or utilities).
* FluidMaterials.json (Material properties).
* Flow_past_a_cylinder.mdpa (Mesh and geometry properties).

To launch simulation, do

```shell
python3 MainKratos.py
```
The simulation must generate "SnapshotsMatrix.npy" files containing the solution of all degrees of freedom's velocity and pressure for all time steps.

### Fixed Rank rSVD

Let us refer to the "SnapshotsMatrix.npy" as $A\in\mathbb{R}^{n\times m}$. The fixed rank SVD is already incorporated into the HPC workflow, and the workflow is presented next.
#### STEP 1 (DISTRIBUTED): The first step is to build a random test matrix  to sample the column space of $A$:
$$Y=A\Omega$$
#### STEP 2 (DISTRIBUTED): For this step, a distributed tall and skinny QR described in (Citar a Demmel) and developed by the BSC group, was coupled with the randomized SVD algorithm. A brief summary of the algorithm is explained here:
For instance, let us consider the matrix $Y$ partitioned into 4 tasks:

$$
Y=
\begin{bmatrix}
Y_1\\
Y_2\\
Y_3\\
Y_4
\end{bmatrix}
$$

Compute the serial QR decomposition on each task:

$$
Y=
\begin{bmatrix}
Q_{11} & 0 & 0 & 0 \\
0 & Q_{21} & 0 & 0 \\
0 & 0 & Q_{31} & 0 \\
0 & 0 & 0 & Q_{41} 
\end{bmatrix}
\begin{bmatrix}
R_1\\
R_2\\
R_3\\
R_4
\end{bmatrix}
$$

Collect into a single task the R factors and perform a serial QR decomposition:

$$
\begin{bmatrix}
R_1\\
R_2\\
R_3\\
R_4
\end{bmatrix}=
\begin{bmatrix}
Q_{12}\\
Q_{22}\\
Q_{32}\\
Q_{42}
\end{bmatrix}
\tilde{R}
$$

Scatter the $Q_{i2}$ factors to the different tasks and multiply them to emit the final $Q$:

$$
Q=
\begin{bmatrix}
Q_{11} & 0 & 0 & 0 \\
0 & Q_{21} & 0 & 0 \\
0 & 0 & Q_{31} & 0 \\
0 & 0 & 0 & Q_{41} 
\end{bmatrix}
\begin{bmatrix}
Q_{12}\\
Q_{22}\\
Q_{32}\\
Q_{42}
\end{bmatrix}=
\begin{bmatrix}
Q_{11} & Q_{12}\\
Q_{21} & Q_{22}\\
Q_{31} & Q_{12}\\
Q_{41} & Q_{42}
\end{bmatrix}
$$


#### STEP 3 (DISTRIBUTED): It is now possible to project $A$ into a much smaller space with the help of $Q$:
$$Y=Q\tilde{R}$$

#### STEP 4 (SERIAL): Obtain the economy SVD on $B$ and truncate the desired rank r:

$$
B=Q^TA
$$

#### STEP 5 (DISTRIBUTED): Obtain the left singular vectors of $A$ of the desired rank $r$ by projecting $\tilde{U}_B$ into $Q$:
$$B=U_B\Sigma_B V^T_B\approx \tilde{U}_b \tilde{\Sigma}_B \tilde{V}^T_B$$

### Fixed Precision rSVD
The fixed precision SVD is already implemented to be used as a blackbox for data in MPI. However, it is not yet incorporated into the PyCOMPSs workflow. The crucial difference is that the random test matrix is now incremental $\Omega => \Delta \Omega$, such that in step 3, one can check for a given error tolerance $\epsilon_u$, if the following condition is satisfied:
$$\|A-QQ^TA\|_F\leq \epsilon_u \|A\|_F$$
Note that $\|A-QQ^TA\|_F\leq \epsilon_u \|A\|_F$ is an expensive computation, and therefore, this check is only performed on the increments (orthogonal complements). 


### Read the snapshots matrix and run the rSVD with MPI
Once the simulation was performed (or a given "SnapshotsMatrix.npy" files is given), an MPI Randomized Singular Value Decomposition can be applied.
The file that calls the implementation is:
* test_rsvd_mpi.py

To run with 4 processors, do
```shell
mpirun -n 4 python3 test_rsvd_mpi.py
```
The console should print something similar to:
```shell
 |  /           |
 ' /   __| _` | __|  _ \   __|
 . \  |   (   | |   (   |\__ \
_|\_\_|  \__,_|\__|\___/ ____/
           Multi-Physics 9.1."3"-f669edb4d6-Release
Compiled with threading and MPI support.
Maximum number of threads: 2.
MPI world size:         2.
Importing    KratosRomApplication 
Initializing KratosRomApplication...
iter =  1  nC =  714.323228197348  dR =  1  R =  1
iter =  2  nC =  9.623625390346358  dR =  20  R =  21
iter =  3  nC =  0.3828880350912341  dR =  41  R =  62
iter =  4  nC =  0.012828323622548663  dR =  72  R =  134
iter =  5  nC =  0.002350716215624348  dR =  47  R =  181
iter =  6  nC =  0.002344995353217843  dR =  20  R =  201
iter =  7  nC =  7.641184106737887e-05  dR =  100  R =  301
The error or reconstruction is:  9.960262742467666e-07
```
And a file called "LeftSingularVectors.npy" must apper. This is the matrix $U$.



