# Channel Flow Re<sub>&tau;</sub> = 590

**Author:** [Suneth Warnakulasuriya](https://github.com/sunethwarna)

**Kratos version:** 7.0.0-11d8e3e31f

**Source files:**

## Case Specification
This is a steady 2D channel flow problem with material parameters which corresponds to flow Re<sub>&tau;</sub>=590.

The geometry is 6.28 x 2 m channel with matching grids in the inlet and outlet. A boundary layer mesh is applied to top and bottom boundaries. For the CFD problem, top and bottom boundaries are considered as walls, but wall functions are used to model the near wall reagions, rather than resolving them. Since periodic conditions are used to avoid solving for the entry region of the flow, a body force is applied to whole domain which is calculated based on Re<sub>&tau;</sub>.

### Material Properties
* Density (&rho;): 1.0 _Kgm<sup>-3</sup>_
* Viscosity (&nu;): 1x10<sup>-2</sup> _m<sup>2</sup>s<sup>-2</sup>_



## Results
The plots hereafter illustrates variation of different non-dimensioned quantities along the line at x = 3.14 _m_ in the domain.

<p align="center">
  <img src="plots/full_channel_re_tau_590_u_plus.png" alt="Cylinder cooling Re = 100 and Pr = 2 velocity field [m/s]." style="width: 600px;"/>
</p>
<p align="center">
  <img src="plots/full_channel_re_tau_590_k_plus.png" alt="Cylinder cooling Re = 100 and Pr = 2 velocity field [m/s]." style="width: 600px;"/>
</p>

## References
Wang, Zimeng & Colin, Fabrice & Le, Guigao & Zhang, Junfeng. (2017). Counter-Extrapolation Method for Conjugate Heat and Mass Transfer with Interfacial Discontinuity. International Journal of Numerical Methods for Heat and Fluid Flow. 27. 2231-2258. 10.1108/HFF-10-2016-0422. [Link to the publication](https://www.researchgate.net/publication/311681538_Counter-Extrapolation_Method_for_Conjugate_Heat_and_Mass_Transfer_with_Interfacial_Discontinuity)
