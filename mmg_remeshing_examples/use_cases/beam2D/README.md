# Beam 2D remeshing

**Author:** Vicente Mataix Ferrándiz

**Kratos version:** 5.2

**Source files:** [Beam 2D](https://github.com/KratosMultiphysics/Examples/tree/master/mmg_remeshing_examples/use_cases/beam2D/source)

## Case Specification

In this test case, 

The following applications of Kratos are used:
- *StructuralMechanicsApplication*
- *MeshingApplication* with the *MMG* module

The problem  corresponds th following, a steel cantilever 10x1 and considering as only load self-weight:
<p align="center">
  <img src="data/beam.png" alt="Beam." style="width: 600px;"/>
</p>

The simulation considers 100 time steps of 0.01s. The problem will be remeshed each ten steps considering the Hessian of the displacement. The initial mesh corresponds with:

<p align="center">
  <img src="data/mesh0.png" alt="Mesh0" style="width: 600px;"/>
</p>


## Results

The evolution of the mesh can be seen in the following figures:

<p align="center">
  <img src="data/mesh1.png" alt="Mesh1" style="width: 600px;"/>
</p>
<p align="center">
  <img src="data/mesh2.png" alt="Mesh2" style="width: 600px;"/>
</p>
<p align="center">
  <img src="data/mesh3.png" alt="Mesh3" style="width: 600px;"/>
</p>
<p align="center">
  <img src="data/mesh4.png" alt="Mesh4" style="width: 600px;"/>
</p>
<p align="center">
  <img src="data/mesh4.png" alt="Mesh5" style="width: 600px;"/>
</p>

Having as final result the following deformed shape:

<p align="center">
  <img src="data/result.png" alt="Result" style="width: 600px;"/>
</p>

## References
*Frédéric Alauzet*. Metric-Based Anisotropic Mesh Adaptation. Course material, CEA-EDF-INRIA Schools. Numerical Analysis Summer School.  [https://www.rocq.inria.fr/gamma/Frederic.Alauzet/cours/cirm.pdf](https://www.rocq.inria.fr/gamma/Frederic.Alauzet/cours/cirm.pdf)

*Pascal Tremblay* 2-D, 3-D and 4-D Anisotropic Mesh Adaptation for the Time-Continuous Space-Time Finite Element Method with Applications to the Incompressible Navier-Stokes Equations. PhD thesis Ottawa-Carleton Institute for Mechanical and Aerospace Engineering, Department of Mechanical Engineering, University of Ottawa. 2007. [http://aix1.uottawa.ca/~ybourg/thesis/PhDThesis_Pascal_Tremblay_Final.pdf](http://aix1.uottawa.ca/~ybourg/thesis/PhDThesis_Pascal_Tremblay_Final.pdf)

