# Isosurface box remeshing

**Author:** Vicente Mataix Ferrándiz

**Kratos version:** 7.1

**Source files:** [Box](https://github.com/KratosMultiphysics/Examples/tree/master/mmg_remeshing_examples/use_cases/test_box/source)

## Case Specification

In this test case we want to remesh anisotropically the geometry of two boxes which represent buildings.

The following applications of Kratos are used:
- *MeshingApplication* with the *MMG* module

The problem  corresponds with the figures:

<p align="center">
  <img src="data/before_remesh.png" alt="Boxes" style="width: 600px;"/>
</p>

<p align="center">
  <img src="data/non_empty_volumes.png" alt="Nonempty" style="width: 600px;"/>
</p>

The challenge consists in meshing anisotropically the geometry using as error measure the gradient of the distance. The initial mesh has a large number of elements, we want to reduce them.  Additionally the remesher will consider the isosurface and we will remove the elements with a negative distance.

## Results

The results obtained after remeshing can be see in the following figure:

<p align="center">
  <img src="data/after_remesh.png" alt="Solution" style="width: 600px;"/>
</p>

In detail the empty region:

<p align="center">
  <img src="data/empty_volumes.png" alt="Empty detail" style="width: 600px;"/>
</p>

## References
*Frédéric Alauzet*. Metric-Based Anisotropic Mesh Adaptation. Course material, CEA-EDF-INRIA Schools. Numerical Analysis Summer School.  [https://www.rocq.inria.fr/gamma/Frederic.Alauzet/cours/cirm.pdf](https://www.rocq.inria.fr/gamma/Frederic.Alauzet/cours/cirm.pdf)

*Pascal Tremblay* 2-D, 3-D and 4-D Anisotropic Mesh Adaptation for the Time-Continuous Space-Time Finite Element Method with Applications to the Incompressible Navier-Stokes Equations. PhD thesis Ottawa-Carleton Institute for Mechanical and Aerospace Engineering, Department of Mechanical Engineering, University of Ottawa. 2007. [http://aix1.uottawa.ca/~ybourg/thesis/PhDThesis_Pascal_Tremblay_Final.pdf](http://aix1.uottawa.ca/~ybourg/thesis/PhDThesis_Pascal_Tremblay_Final.pdf)

