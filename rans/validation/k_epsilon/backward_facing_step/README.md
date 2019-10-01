# Backward Facing Step

**Author:** [Suneth Warnakulasuriya](https://github.com/sunethwarna)

**Kratos version:** 7.0.0-11d8e3e31f

**Source files:**

## Case Specification
This is steady backward facing step problem with material parameters which corresponds to flow of Re<sub>h</sub> = 5000.

The geometry has an entry length of channel is 1.47 _m_. The step height(_h_) is 9.8 _mm_. The inlet is _10h_, and outlet is _12h_. Inlet velocity is prescribed with 7.72 _ms<sup>-1</sup>_ velocity, and outlet is prescribed with 0 _Pa_. Turbulent kinetic energy (_k_) is also prescribed at inlet with turbulent intensity of 6.1x10<sup>-4</sup>. Turbulent energy dissipation rate(_&epsilon;_) is prescribed with mixing length of 0.0588 _m_. Outlet for _k_ and _&epsilon;_ is prescribed with zero gradient boundary conditions. Wall functions are applied near wall regions with y<sup>+</sup> = 12.0

### Material Properties
* Density (&rho;): 1.0 _Kgm<sup>-3</sup>_
* Viscosity (&nu;): 1.51312x10<sup>-5</sup> _m<sup>2</sup>s<sup>-2</sup>_


## Results
The plots hereafter illustrates variation of different non-dimensioned quantities along the line at specified x.
<table style="width:100%">
  <tr>
    <th> <img src="plots/velocity_x=-3.12h.png" alt="Velocity variation at x=-3.12h" style="width: 400px;"/> </th>
    <th> <img src="plots/velocity_x=4h.png" alt="Velocity variation at x=4h" style="width: 400px;"/> </th>
    <th> <img src="plots/velocity_x=6h.png" alt="Velocity variation at x=6h" style="width: 421px;"/> </th>
  </tr>
  <tr>
    <th> <img src="plots/turbulent_kinetic_energy_x=-3.12h.png" alt="Velocity variation at x=-3.12h" style="width: 400px;"/> </th>
    <th> <img src="plots/turbulent_kinetic_energy_x=4h.png" alt="Velocity variation at x=4h" style="width: 400px;"/> </th>
    <th> <img src="plots/turbulent_kinetic_energy_x=6h.png" alt="Velocity variation at x=6h" style="width: 421px;"/> </th>
  </tr>
</table>

## References
Jovic and Driver (1994), Backward-Facing Step Measurements at Low Reynolds Number, Re_h=5000, NASA TM 108807. [Link to the publication](https://ntrs.nasa.gov/archive/nasa/casi.ntrs.nasa.gov/19940028784.pdf)

