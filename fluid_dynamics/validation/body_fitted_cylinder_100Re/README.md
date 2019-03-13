# Body-fitted 100 Re cylinder

**Author:** [Rubén Zorrilla](https://github.com/rubenzorrilla)

**Kratos version:** 7.0

**Source files:** [Body-fitted 100 Re cylinder](https://github.com/KratosMultiphysics/Examples/tree/master/fluid_dynamics/validation/body_fitted_cylinder_100Re/source)

## Case Specification
This is a 2D CFD simulation of the well-known 100 Re cylinder flow benchmark. 

The problem geometry consists in a 5 x 1 m channel inside which a cylinder is placed. The center of the cylinder is placed in (1.25,0.5) coordinates and its radius is 0.1 m. The cylinder as well as top and bottom walls are considered to be no-slip. The pressure is fixed along the right edge. A parabolic inlet function, which maximum is 1.5 m/s, is set in the left edge. A sinusoidal ramp-up is applied to such inlet function from 0.0 to 1.0 s.

Concerning the material properties, a Newtonian constitutive law is used. Considering that the cylinder diameter is 0.2 m and the average velocity is 1 m/s, the fluid characteristic parameters to obtain a 100 Re flow are:
* Density (&rho;): 1 _Kg/m<sup>3</sup>_
* Dynamic viscosity (&mu;): 1E-02 _m<sup>2</sup>/s_

The time step is 0.1 seconds, while the total simulation time is 45.0 seconds. 

## Results
The above stated problem has been solved using an incompressible Navier-Stokes formulation with ASGS stabilization. The mesh is made up of around 6.1K linear triangular elements. The obtained velocity and pressure fields are shown in the animations below. As can be observed, the expected Von Karman vortex street is developed in the downstream region. Also note that if the source files are run, a *.dat file containing the cylinder drag and lift time evolution is generated. The obtained values have very good agreement with the theoretical expected ones.

<p align="center">
  <img src="data/body_fitted_cylinder_100Re_v.gif" alt="Body-fitted 100 Re cylinder velocity field [m/s]." style="width: 600px;"/>
</p>

<p align="center">
  <img src="data/body_fitted_cylinder_100Re_p.gif" alt="Body-fitted 100 Re cylinder pressure field [Pa]." style="width: 600px;"/>
</p>
