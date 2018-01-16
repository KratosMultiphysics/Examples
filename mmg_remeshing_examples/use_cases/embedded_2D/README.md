# Embedded sphere 2D remeshing

**Author:** Vicente Mataix Ferrándiz

**Kratos version:** 5.2

**Source files:** [Embedded sphere 2D](https://github.com/KratosMultiphysics/Examples/tree/master/mmg_remeshing_examples/use_cases/embedded_2D/source)

## Case Specification

In this test case, 

The following applications of Kratos are used:
- *FluidDynamicsApplication* with the *MMG* module
- *MeshingApplication* with the *MMG* module

Adaptative anisotropic remeshing of 2D fluid channel with sphere using as level set the distance function. The problem is solved using an embedded formulation. It consists in a channel 5x1, a sphere of 0.3 m diameter and with a velocity of 1 m/s in the inlet an zero pressure in the outlet. The total time of simulation is *10s* with a time step of *0.1s*. 

The remeshing is before start the simulation, where we start with a very refined mesh of 40000 nodes and it is simplified to a mesh of just 2500 nodes, centered around the sphere of interest.

<p align="center">
  <img src="data/geometry.png" alt="Geometry." style="width: 600px;"/>
</p>
 
The mesh corresponding before remeshing corresponds with:

<p align="center">
  <img src="data/mesh0.png" alt="Mesh0" style="width: 600px;"/>
</p>

The mesh corresponding after remesh:

<p align="center">
  <img src="data/mesh1.png" alt="Mesh1" style="width: 600px;"/>
</p>

## Results

The results obtained corresponds with the following:

<p align="center">
  <img src="data/velocity.gif" alt="Solution" style="width: 600px;"/>
</p>

<p align="center">
  <img src="data/pressure.gif" alt="Solution" style="width: 600px;"/>
</p>

## References
*Frédéric Alauzet*. Metric-Based Anisotropic Mesh Adaptation. Course material, CEA-EDF-INRIA Schools. Numerical Analysis Summer School.  [https://www.rocq.inria.fr/gamma/Frederic.Alauzet/cours/cirm.pdf](https://www.rocq.inria.fr/gamma/Frederic.Alauzet/cours/cirm.pdf)

*Pascal Tremblay* 2-D, 3-D and 4-D Anisotropic Mesh Adaptation for the Time-Continuous Space-Time Finite Element Method with Applications to the Incompressible Navier-Stokes Equations. PhD thesis Ottawa-Carleton Institute for Mechanical and Aerospace Engineering, Department of Mechanical Engineering, University of Ottawa. 2007. [http://aix1.uottawa.ca/~ybourg/thesis/PhDThesis_Pascal_Tremblay_Final.pdf](http://aix1.uottawa.ca/~ybourg/thesis/PhDThesis_Pascal_Tremblay_Final.pdf)

