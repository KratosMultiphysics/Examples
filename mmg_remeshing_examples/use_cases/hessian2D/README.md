# Hessian 2D remeshing

**Author:** Vicente Mataix Ferrándiz

**Kratos version:** 5.2

**Source files:** [Hessian 2D](https://github.com/KratosMultiphysics/Examples/tree/master/mmg_remeshing_examples/use_cases/hessian2D/source)

## Case Specification

In this test case, 

The following applications of Kratos are used:
- *FluidDynamicsApplication* with the *MMG* module
- *MeshingApplication* with the *MMG* module

The problem  corresponds with the  example proposed in [reference](https://www.rocq.inria.fr/gamma/Frederic.Alauzet/cours/cirm.pdf). The  objective is to remesh the following structured mesh of a domain 1x1:
<p align="center">
  <img src="data/before_remesh.png" alt="Debore remesh" style="width: 600px;"/>
</p>

Where the size of the elements is very small and the distribution of the elements is not the optimal to represent the following test function:

<p align="center">
  <img src="data/error_function.png" alt="Error function" style="width: 600px;"/>
</p>

The challenge consists in using the Hessian function of the test function as error measure and adapt the mesh in a proper manner.

## Results

The results obtained after remeshing can be see in the following figures:

<p align="center">
  <img src="data/after_remesh.png" alt="Solution" style="width: 600px;"/>
</p>

The color map of the test function:

<p align="center">
  <img src="data/error_stimation.png" alt="Distance" style="width: 600px;"/>
</p>

The variation of the element size:

<p align="center">
  <img src="data/nodal_h.png" alt="Nodal H" style="width: 600px;"/>
</p>


## References
*Frédéric Alauzet*. Metric-Based Anisotropic Mesh Adaptation. Course material, CEA-EDF-INRIA Schools. Numerical Analysis Summer School.  [https://www.rocq.inria.fr/gamma/Frederic.Alauzet/cours/cirm.pdf](https://www.rocq.inria.fr/gamma/Frederic.Alauzet/cours/cirm.pdf)

*Pascal Tremblay* 2-D, 3-D and 4-D Anisotropic Mesh Adaptation for the Time-Continuous Space-Time Finite Element Method with Applications to the Incompressible Navier-Stokes Equations. PhD thesis Ottawa-Carleton Institute for Mechanical and Aerospace Engineering, Department of Mechanical Engineering, University of Ottawa. 2007. [http://aix1.uottawa.ca/~ybourg/thesis/PhDThesis_Pascal_Tremblay_Final.pdf](http://aix1.uottawa.ca/~ybourg/thesis/PhDThesis_Pascal_Tremblay_Final.pdf)

