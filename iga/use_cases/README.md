# Use Case IGA – External Boundary Circle (NURBS)

Short description
This example runs a 2D IGA structural model whose outer boundary is a NURBS circle. A manufactured solution is enforced to validate the setup.

Files
- ProjectParameters.json
- materials.json
- nurbs_files/circle_nurbs.json
- run_and_post.py (optional)

Geometry
- ImportNurbsSbmModeler loads the circle NURBS into “initial_skin_model_part_out”.
- NurbsGeometryModelerSbm builds the analysis surface (order [2,2], knot spans [20,20]) and creates “skin_model_part”.
- IgaModelerSbm creates:
  • SolidElement on IgaModelPart.StructuralAnalysisDomain
  • SbmSolidCondition on SurfaceEdge (brep_ids: [2]) → IgaModelPart.SBM_Support_outer

Manufactured BCs and loads
- Displacement on outer boundary:
  u = [ -cos(x)*sinh(y),  sin(x)*cosh(y), 0.0 ]
- Body force in the domain (consistent with the above):
  BODY_FORCE = [
    -1000*(1+0.3)/(1-0.3*0.3)*cos(x)*sinh(y),
    -1000*(1+0.3)/(1-0.3*0.3)*sin(x)*cosh(y),
    0.0
  ]

Solver (key settings)
- Static, nonlinear; OpenMP
- Single time step: dt = 0.1, end_time = 0.1
- Linear solver: LinearSolversApplication.sparse_lu

Minimal materials.json (example)
Use plane strain (or plane stress) linear elastic; keep it consistent with ν=0.3:
{
  "properties": [{
    "model_part_name": "IgaModelPart.StructuralAnalysisDomain",
    "properties_id": 1,
    "Material": {
      "constitutive_law": { "name": "LinearElasticPlaneStrain2DLaw" },
      "Variables": {
        "YOUNG_MODULUS": 1000.0,
        "POISSON_RATIO": 0.3,
        "DENSITY": 1.0
      }
    }
  }]
}

Run:
  python3 run_and_post.py        # to reproduce the error
  python3 convergence.py         # for the convergence analysis
  python3 plot_surrogate_boundaries.py  # to visualize the surrogate and true boundaries

<img width="999" height="786" alt="image" src="https://github.com/user-attachments/assets/ea1c01a6-806c-486a-b11e-d3846bac3b85" />

<img width="588" height="430" alt="image" src="https://github.com/user-attachments/assets/9401a33e-4c81-47de-bc9b-a0323fdb89a9" />

results of the convergence:

 h =  [1.0, 0.5, 0.25, 0.125, 0.0625]
 
 L2_error = [0.04245443538478202, 0.00612519522524315, 0.0006828403386498715, 7.033648516213708e-05, 1.0075704685614167e-05]


