"""Validation of the potential flow solver against XFOIL.

One case is launched with the parameters of the proposed airfoil: a NACA 4412 at
Mach 0.2 and 1 degree of angle of attack. The same case is solved with the coarse
medium and the fine mesh and the lift coefficients, the times of both and their surface
pressure distributions are compared.

The validation reference is a file of measured pressures but XFOIL, which is called
from Python to obtain the pressure coefficient distribution of the very same profile.
Everything XFOIL needs is implemented in this script, so it is self-contained: the
panel contour, the inviscid setup, the Karman-Tsien correction of the pressure
coefficient and the comparison of both distributions. The library only carries what
the solver itself returns, namely the nodal pressure coefficient distribution and the
lift coefficient computed by Kratos.

XFOIL is an incompressible code, so it is solved at zero Mach and its pressure
coefficient is lifted to the Mach number of the case with the Karman-Tsien
correction, which is the very formula XFOIL applies to report ``cp`` at a
compressible Mach number. The lift coefficient of the reference is the one XFOIL
reports for the case, not an integration of that corrected distribution.

Note that XFOIL is inviscid only when its Reynolds number is set to zero, which is
what ``XFOIL_REYNOLDS = 0`` selects: that is the only reference that matches a
potential flow solver. Any other Reynolds number brings in a boundary layer, and the
lift coefficient of the reference then drops accordingly.
"""

from dataclasses import dataclass

import numpy as np
import matplotlib.pyplot as plt

from kratos_lib.MainKratos import AsAirfoil, EvaluateAirfoils, SurfacePressure

try:
    from xfoil import XFoil
    from xfoil.model import Airfoil
except ImportError as error:
    raise ImportError(
        "The 'xfoil' module is required to run this validation but it is not "
        "installed. It is a compiled Fortran binding, so a Fortran compiler, cmake "
        "and the sources of https://github.com/DARcorporation/xfoil-python are "
        "needed. Install it in a virtual environment, otherwise the PEP 668 "
        "restriction of the system interpreter rejects the install:\n"
        "    python3 -m venv --system-site-packages venv\n"
        "    ./venv/bin/pip install https://github.com/DARcorporation/xfoil-python\n"
        "    ./venv/bin/python validation.py\n"
        "The build must drop the '-fbounds-check' and '-ffpe-trap=invalid,zero' "
        "flags of the CMakeLists.txt, which abort XFOIL on its own internal array "
        "indexing, and the total number of panel nodes must stay below the 640 "
        "compiled into XFOIL."
    ) from error

# Case to validate: NACA 4412 (max camber, camber position, thickness)
AIRFOIL = (0.04, 0.4, 0.12)
MACH_NUMBER = 0.2
ANGLE_OF_ATTACK = 1.0  # degrees

# Meshes to compare
COARSE_MESH = "baseline_coarse"
MEDIUM_MESH = "baseline_medium"
FINE_MESH = "baseline_fine"

# Settings of the XFOIL reference. Zero Reynolds selects the inviscid panel method
XFOIL_REYNOLDS = 0.0
XFOIL_PANELS = 201  # points per surface, so 2 * XFOIL_PANELS - 1 in the closed contour
XFOIL_MAX_ITERATIONS = 200

FIGURE_FILE = "data/validation_naca4412.png"

# Output flags
GID_OUTPUT = False
VTK_OUTPUT = False


# ─── XFOIL reference ─────────────────────────────────────────────────────
@dataclass(frozen=True)
class XfoilSurface:
    """Pressure coefficient distribution of a profile as computed by XFOIL.

    ``x`` and ``y`` are the coordinates of the panel nodes of the closed contour in
    chord units and ``cp`` the pressure coefficient read at every one of them, already
    corrected to the Mach number of the case. ``lift_coefficient`` is the value XFOIL
    reports for the angle of attack of the case.
    """

    x: np.ndarray
    y: np.ndarray
    cp: np.ndarray
    lift_coefficient: float


def KarmanTsien(pressure_coefficient, mach_number: float):
    """Lift the pressure coefficient from zero Mach to ``mach_number``.

    XFOIL applies this very correction in ``get_cp`` to report the compressible
    pressure coefficient of an incompressible solution. It is reproduced here because
    the Mach number cannot be handed over to the solver itself: the ``M`` setter of
    the Python binding writes ``MINf``, which ``mrcl`` overwrites with ``MINf1`` at
    every iteration, so the solve always runs at zero Mach.
    """

    if mach_number == 0.0:
        return pressure_coefficient

    beta = np.sqrt(1.0 - mach_number ** 2)
    b_factor = 0.5 * mach_number ** 2 / (1.0 + beta)
    return pressure_coefficient / (beta + b_factor * pressure_coefficient)


def ReferencePressure(airfoil_profile, mach_number: float, angle_of_attack: float,
                      reynolds_number: float = XFOIL_REYNOLDS,
                      panels: int = XFOIL_PANELS) -> XfoilSurface:
    """Return the pressure coefficient distribution of a profile as computed by XFOIL.

    The profile is sampled with cosine spacing, which resolves the leading edge, and
    handed over to XFOIL as a closed contour.
    """

    airfoil = AsAirfoil(airfoil_profile)

    chord_positions = 0.5 * (1.0 - np.cos(np.linspace(0.0, np.pi, panels)))
    upper = [airfoil.surface_point(position, True) for position in chord_positions]
    lower = [airfoil.surface_point(position, False) for position in chord_positions]

    # Traverse the contour from the trailing edge along the upper surface to the
    # leading edge, then back to the trailing edge along the lower surface. XFOIL
    # accepts either orientation.
    x = np.array([point[0] for point in upper[::-1]] + [point[0] for point in lower[1:]])
    y = np.array([point[1] for point in upper[::-1]] + [point[1] for point in lower[1:]])

    solver = XFoil()
    solver.print = False
    solver.airfoil = Airfoil(x, y)
    solver.Re = reynolds_number
    solver.M = 0.0
    solver.max_iter = XFOIL_MAX_ITERATIONS

    lift_coefficient, drag_coefficient, moment, _ = solver.a(angle_of_attack)
    if not np.isfinite(lift_coefficient):
        raise RuntimeError("XFOIL returned a non finite lift coefficient. The inviscid "
                           "solver does not converge past the lift coefficient it can "
                           "carry, so either lower the angle of attack, raise XFOIL_PANELS "
                           "or check that the Reynolds number is not too low to sustain "
                           "attached flow.")

    # The ordinates are read back from XFOIL, where the panel nodes may have been
    # reordered, so they are taken from the solved airfoil and not from the input
    x_pressure, pressure = solver.get_cp_distribution()
    solved_airfoil = solver.airfoil

    return XfoilSurface(x=x_pressure,
                        y=np.array(solved_airfoil.y, dtype=float),
                        cp=KarmanTsien(pressure, mach_number),
                        lift_coefficient=float(lift_coefficient))


def UpperAndLower(surface):
    """Split a pressure coefficient distribution into upper and lower surface by ``y``.

    Only used for the XFOIL reference, which carries no submodel part information.
    The Kratos distributions are split with the ``UpperSurface``/``LowerSurface``
    submodel parts in ``SurfacePressure.upper_and_lower``.
    """

    is_upper = np.asarray(surface.y) > 0.0
    x, cp = np.asarray(surface.x), np.asarray(surface.cp)
    upper, lower = x[is_upper], x[~is_upper]
    return (np.sort(upper), cp[is_upper][np.argsort(upper)],
            np.sort(lower), cp[~is_upper][np.argsort(lower)])


# ─── Solving ────────────────────────────────────────────
def SolveMesh(mesh_name: str):
    """Solve the validation case over the given mesh and return its result."""
    
    results = EvaluateAirfoils([AIRFOIL], mesh_name, MACH_NUMBER, ANGLE_OF_ATTACK,
                               gid_output=GID_OUTPUT, vtk_output=VTK_OUTPUT,
                               pressure_coefficient=True)    
    return results[0]


def CompareResults(reference: XfoilSurface, coarse, medium, fine):
    """Compare the lift coefficients of both meshes and their error against XFOIL."""

    meshes = ((COARSE_MESH, coarse), (MEDIUM_MESH, medium), (FINE_MESH, fine))
    inviscid = XFOIL_REYNOLDS == 0.0

    print(f"\nXFOIL reference over {len(reference.cp)} surface points "
          f"(Re = {XFOIL_REYNOLDS:.3g}, {XFOIL_PANELS} points per surface, "
          f"{'inviscid' if inviscid else 'viscous'}):")
    print(f"  Cl = {reference.lift_coefficient:.6f}")

    print(f"\nNACA {coarse.airfoil.name}, Mach {MACH_NUMBER}, alpha {ANGLE_OF_ATTACK} deg "
          f"- coarse / medium / fine comparison:")
    header = (f"{'Mesh':>16}  {'Cl':>12}  {'t solve [s]':>12}")
    print(header)
    for name, result in meshes:
        print(f"{name:>16}  {result.lift_coefficient:12.6f}  {result.solve_time:12.2f}")


def PlotPressureCoefficient(reference: XfoilSurface, coarse, medium, fine):
    """Plot the computed pressure coefficient distributions against XFOIL."""

    figure, (pressure_axis, profile_axis) = plt.subplots(
        2, 1, figsize=(9.0, 7.5), gridspec_kw={"height_ratios": [3.0, 1.0]})

    distributions = ((COARSE_MESH, coarse.surface_pressure, "tab:blue"),
                     (MEDIUM_MESH, medium.surface_pressure, "tab:orange"),
                     (FINE_MESH, fine.surface_pressure, "tab:red"))
    reference_x, reference_cp, reference_lower_x, reference_lower_cp = UpperAndLower(reference)
    pressure_axis.plot(reference_x, reference_cp, color="black", linestyle="-",
                       label="XFOIL")
    pressure_axis.plot(reference_lower_x, reference_lower_cp, color="black", linestyle="-")
    for label, surface, color in distributions:
        upper_x, upper_cp, lower_x, lower_cp = surface.upper_and_lower()
        pressure_axis.plot(upper_x, upper_cp, color=color, linestyle="-", label=f"{label}")
        pressure_axis.plot(lower_x, lower_cp, color=color, linestyle="-")

    all_cp = np.concatenate([reference.cp, coarse.surface_pressure.cp, medium.surface_pressure.cp, fine.surface_pressure.cp])
    pressure_axis.set_xlabel("x/c")
    pressure_axis.set_ylabel("$c_p$")
    pressure_axis.set_ylim(all_cp.min() - 0.5, all_cp.max() + 0.5)
    pressure_axis.invert_yaxis()
    pressure_axis.grid(True, linestyle=":", alpha=0.6)
    pressure_axis.legend(fontsize=9, loc="upper right")
    inviscid = XFOIL_REYNOLDS == 0.0
    pressure_axis.set_title(f"NACA {coarse.airfoil.name}, Mach {MACH_NUMBER}, alpha {ANGLE_OF_ATTACK} deg "
                            f"- pressure coefficient against XFOIL "
                            f"(Re = {XFOIL_REYNOLDS:.3g}, "
                            f"{'inviscid' if inviscid else 'viscous'})")

    surface_fine = fine.surface_pressure
    surface_medium = medium.surface_pressure
    surface_coarse = coarse.surface_pressure
    contour_x, contour_y = surface_coarse.ordered_contour()
    profile_axis.plot(contour_x, contour_y, color="0.4", linewidth=0.8, label=f"{COARSE_MESH}")
    profile_axis.fill(contour_x, contour_y, color="tab:blue", alpha=0.25)
    contour_x, contour_y = surface_medium.ordered_contour()
    profile_axis.plot(contour_x, contour_y, color="0.4", linestyle="-.", linewidth=0.8, label=f"{MEDIUM_MESH}")
    profile_axis.fill(contour_x, contour_y, color="tab:orange", alpha=0.25)
    contour_x, contour_y = surface_fine.ordered_contour()
    profile_axis.plot(contour_x, contour_y, color="0.4", linestyle="--", linewidth=0.8, label=f"{FINE_MESH}")
    profile_axis.fill(contour_x, contour_y, color="tab:red", alpha=0.25)
    profile_axis.plot(reference.x, reference.y, color="black", linestyle=":", linewidth=0.8, label="XFOIL")
    profile_axis.set_xlabel("x/c")
    profile_axis.set_ylabel("y/c")
    profile_axis.set_ylim(-0.08, 0.2)
    profile_axis.set_aspect("equal", adjustable="datalim")
    profile_axis.legend(fontsize=9, loc="upper right")
    profile_axis.grid(True, linestyle=":", alpha=0.6)
    figure.tight_layout()
    figure.savefig(FIGURE_FILE, dpi=250)
    plt.close(figure)


if __name__ == "__main__":

    reference = ReferencePressure(AIRFOIL, MACH_NUMBER, ANGLE_OF_ATTACK)

    coarse = SolveMesh(COARSE_MESH)

    medium = SolveMesh(MEDIUM_MESH)

    fine = SolveMesh(FINE_MESH)

    CompareResults(reference, coarse, medium, fine)
    PlotPressureCoefficient(reference, coarse, medium, fine)
    print(f"\nFigure written to {FIGURE_FILE}")
