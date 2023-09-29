# Contacting cylinders with adaptive remeshing

**Author:** Vicente Mataix Ferrándiz
**Kratos version:** Development branch. **Expected 7.1**

**Source files:** [Cylinders](https://github.com/KratosMultiphysics/Examples/tree/master/mmg_remeshing_examples/use_cases/contacting_cylinders/source)

## Case Specification

The following applications of Kratos are used:
- *StructuralMechanicsApplication*
- *ContactStructuralMechanicsApplication*
- *MeshingApplication* with the *MMG* module

The problem consists in a two cylinders with a very coarse mesh where we impose an horizontal movement in the upper cylinder. The cylinders are formulated as solids in TL with hyperelastic behaviour. The problem has been remeshed each 2.5e-2s, and the simulations is 1.5s long. The *Hessian* of the contact stress and the VM stress has been considered to define the metric.

- *Initial mesh*:

<p align="center">
  <img src="data/mesh.png" alt="Mesh1" style="width: 600px;"/>
</p>

## Results

### Displacement

<p align="center">
  <img src="data/disp.gif" alt="Mesh1" style="width: 600px;"/>
  <img src="data/disp_2d.gif" alt="Mesh1" style="width: 600px;"/>
   <img src="data/disp1.png" alt="Mesh1" style="width: 600px;"/>
   <img src="data/disp2.png" alt="Mesh1" style="width: 600px;"/>
   <img src="data/disp3.png" alt="Mesh1" style="width: 600px;"/>
   <img src="data/disp4.png" alt="Mesh1" style="width: 600px;"/>
   <img src="data/disp5.png" alt="Mesh1" style="width: 600px;"/>
</p>

### VM stress

<p align="center">
   <img src="data/vm.gif" alt="Mesh1" style="width: 600px;"/>
   <img src="data/vm_2d.gif" alt="Mesh1" style="width: 600px;"/>
   <img src="data/vm1.png" alt="Mesh1" style="width: 600px;"/>
   <img src="data/vm2.png" alt="Mesh1" style="width: 600px;"/>
   <img src="data/vm3.png" alt="Mesh1" style="width: 600px;"/>
   <img src="data/vm4.png" alt="Mesh1" style="width: 600px;"/>
   <img src="data/vm5.png" alt="Mesh1" style="width: 600px;"/>
</p>

### Element size

<p align="center">
   <img src="data/nodal_h.gif" alt="Mesh1" style="width: 600px;"/>
   <img src="data/nodal_h_2d.gif" alt="Mesh1" style="width: 600px;"/>
   <img src="data/nodal_h1.png" alt="Mesh1" style="width: 600px;"/>
   <img src="data/nodal_h2.png" alt="Mesh1" style="width: 600px;"/>
   <img src="data/nodal_h3.png" alt="Mesh1" style="width: 600px;"/>
   <img src="data/nodal_h4.png" alt="Mesh1" style="width: 600px;"/>
   <img src="data/nodal_h5.png" alt="Mesh1" style="width: 600px;"/>
</p>


## References
*Frédéric Alauzet*. Metric-Based Anisotropic Mesh Adaptation. Course material, CEA-EDF-INRIA Schools. Numerical Analysis Summer School.  [https://www.rocq.inria.fr/gamma/Frederic.Alauzet/cours/cirm.pdf](https://www.rocq.inria.fr/gamma/Frederic.Alauzet/cours/cirm.pdf)

*Pascal Tremblay* 2-D, 3-D and 4-D Anisotropic Mesh Adaptation for the Time-Continuous Space-Time Finite Element Method with Applications to the Incompressible Navier-Stokes Equations. PhD thesis Ottawa-Carleton Institute for Mechanical and Aerospace Engineering, Department of Mechanical Engineering, University of Ottawa. 2007. [http://aix1.uottawa.ca/~ybourg/thesis/PhDThesis_Pascal_Tremblay_Final.pdf](http://aix1.uottawa.ca/~ybourg/thesis/PhDThesis_Pascal_Tremblay_Final.pdf)
