# Cavity remeshing

**Author:** Vicente Mataix Ferrándiz

**Kratos version:** 5.2

**Source files:** [Cavity](https://github.com/KratosMultiphysics/Examples/tree/master/mmg_remeshing_examples/use_cases/cavity2D/source)

## Case Specification

In this test case, 

The following applications of Kratos are used:
- *FluidDynamicsApplication*
- *MeshingApplication* with the *MMG* module

This is a very simple remeshing test, where we remesh a cavity 1x1 using the distance to the center as test function.
<p align="center">
  <img src="data/original.png" alt="Original." style="width: 600px;"/>
</p>

## Results

The results obtained after remeshing can be see in the following figures:

<p align="center">
  <img src="data/remesh.png" alt="Solution" style="width: 600px;"/>
</p>

The color map of the distance:

<p align="center">
  <img src="data/distance.png" alt="Distance" style="width: 600px;"/>
</p>

The variation of the element size:

<p align="center">
  <img src="data/nodalh.png" alt="Nodal h" style="width: 600px;"/>
</p>


## References
*Frédéric Alauzet*. Metric-Based Anisotropic Mesh Adaptation. Course material, CEA-EDF-INRIA Schools. Numerical Analysis Summer School.  [https://www.rocq.inria.fr/gamma/Frederic.Alauzet/cours/cirm.pdf](https://www.rocq.inria.fr/gamma/Frederic.Alauzet/cours/cirm.pdf)

*Pascal Tremblay* 2-D, 3-D and 4-D Anisotropic Mesh Adaptation for the Time-Continuous Space-Time Finite Element Method with Applications to the Incompressible Navier-Stokes Equations. PhD thesis Ottawa-Carleton Institute for Mechanical and Aerospace Engineering, Department of Mechanical Engineering, University of Ottawa. 2007. [http://aix1.uottawa.ca/~ybourg/thesis/PhDThesis_Pascal_Tremblay_Final.pdf](http://aix1.uottawa.ca/~ybourg/thesis/PhDThesis_Pascal_Tremblay_Final.pdf)

