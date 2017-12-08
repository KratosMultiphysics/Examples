# Lamborghini remeshing

**Author:** Vicente Mataix Ferrándiz

**Kratos version:** 5.2

**Source files:** [Lamborghini](https://github.com/KratosMultiphysics/Examples/tree/master/mmg_remeshing_examples/use_cases/lamborghini/source) (Please  decompress the mdpa file)

## Case Specification

In this test case we want to remesh anisotropically the geometry of *Lamborghini*, more complex that the previous bunny.

The following applications of Kratos are used:
- *FluidDynamicsApplication*
- *MeshingApplication* with the *MMG* module

The problem  corresponds with the figures:

<p align="center">
  <img src="data/stl_gid1.png" alt="Lamborghini" style="width: 600px;"/>
</p>

<p align="center">
  <img src="data/stl_gid2.png" alt="Lamborghini" style="width: 600px;"/>
</p>

The challenge consists in meshing anisotropically the geometry using as error measure the gradient of the distance, measured previously with an octree mesher ([GiD](https://www.gidhome.com/)). The *STL* file used can be found [here](https://github.com/KratosMultiphysics/Examples/tree/master/mmg_remeshing_examples/use_cases/lamborghini/source/lamborghini_car.stl)
 
The mesh corresponding before remeshing corresponds with:

<p align="center">
  <img src="data/lamborghini_noremesh.png" alt="Octree" style="width: 600px;"/>
</p>

<p align="center">
  <img src="data/detail_noremesh.png" alt="Octree" style="width: 600px;"/>
</p>


## Results

The results obtained after remeshing can be see in the following figure:

<p align="center">
  <img src="data/lamborghini_ani1.png" alt="Solution" style="width: 600px;"/>
</p>

In detail:

<p align="center">
  <img src="data/detail_ani1.png" alt="Distance detail" style="width: 600px;"/>
</p>

## References
*Frédéric Alauzet*. Metric-Based Anisotropic Mesh Adaptation. Course material, CEA-EDF-INRIA Schools. Numerical Analysis Summer School.  [https://www.rocq.inria.fr/gamma/Frederic.Alauzet/cours/cirm.pdf](https://www.rocq.inria.fr/gamma/Frederic.Alauzet/cours/cirm.pdf)

*Pascal Tremblay* 2-D, 3-D and 4-D Anisotropic Mesh Adaptation for the Time-Continuous Space-Time Finite Element Method with Applications to the Incompressible Navier-Stokes Equations. PhD thesis Ottawa-Carleton Institute for Mechanical and Aerospace Engineering, Department of Mechanical Engineering, University of Ottawa. 2007. [http://aix1.uottawa.ca/~ybourg/thesis/PhDThesis_Pascal_Tremblay_Final.pdf](http://aix1.uottawa.ca/~ybourg/thesis/PhDThesis_Pascal_Tremblay_Final.pdf)

