"""Example: lift coefficients for a parametric space of NACA 4-digit airfoils.

The user defines the parametric space, Mach, angle of attack, and meshes to use.
The library evaluates each profile and returns Cl, solve time and, the
surface pressure coefficient distribution of the profile.
"""

from kratos_lib.MainKratos import AsAirfoil, EvaluateAirfoils
import matplotlib.pyplot as plt
import numpy as np
import itertools


# User-defined parametric space
def GenerateDesignSpace():
    """Build the parametric space of airfoils to be evaluated.
    
    Returns:
        List of (max_camber, camber_position, thickness) as fractions of chord.
        For symmetric airfoils (max_camber=0), camber_position is ignored (fixed to 0.4).
    """

    m_range = np.arange(0.00, 0.07, 0.01)  # 0% to 6%
    p_range = np.arange(0.20, 0.70, 0.10)  # 20% to 60%
    t_range = np.arange(0.08, 0.16, 0.01)  # 8% to 15%

    valid_profiles = []
    for m, p, t in itertools.product(m_range, p_range, t_range):
        m, p, t = round(m, 2), round(p, 1), round(t, 2)
        # Filter duplicates: symmetric airfoils (m=0) don't depend on p
        if m == 0.0 and p != 0.4:
            continue
        valid_profiles.append((m, p, t))
    return valid_profiles


def PlotPressureAndProfile(coarse_results, medium_results, fine_results, names, 
                           mach_number, alpha, file_name):
    """Plot the pressure coefficient distribution and the shape of every profile."""

    columns = len(names)
    figure, axes = plt.subplots(2, columns, figsize=(4.2 * columns, 7.0), squeeze=False)

    for column, name in enumerate(names):
        pressure_axis, profile_axis = axes[0][column], axes[1][column]

        for label, results, color in (("coarse", coarse_results, "tab:blue"),
                                      ("medium", medium_results, "tab:orange"),
                                      ("fine", fine_results, "tab:red")):
            surface = results[column].surface_pressure
            upper_x, upper_cp, lower_x, lower_cp = surface.upper_and_lower()
            pressure_axis.plot(upper_x, upper_cp, color=color, linewidth=1.2,
                               label=f"{label} mesh")
            pressure_axis.plot(lower_x, lower_cp, color=color, linewidth=1.2)
            contour_x, contour_y = surface.ordered_contour()
            profile_axis.plot(contour_x, contour_y, color=color, linewidth=1.0,
                              label=f"{label} mesh")
            profile_axis.fill(contour_x, contour_y, color=color, alpha=0.15)

        pressure_axis.set_title(f"NACA {name}", fontsize=11)
        pressure_axis.set_xlabel("x/c")
        pressure_axis.set_ylabel("$c_p$")
        pressure_axis.invert_yaxis()
        pressure_axis.grid(True, linestyle=":", alpha=0.6)
        pressure_axis.legend(fontsize=8, loc="upper right")

        profile_axis.set_xlabel("x/c")
        profile_axis.set_ylabel("y/c")
        profile_axis.set_aspect("equal", adjustable="datalim")
        profile_axis.grid(True, linestyle=":", alpha=0.6)
        profile_axis.legend(fontsize=8, loc="upper right")

    figure.suptitle(f"Mach {mach_number} - Alpha {alpha} deg", fontsize=13)
    figure.tight_layout(rect=(0.0, 0.0, 1.0, 0.96))
    figure.savefig(file_name, dpi=250)
    plt.close(figure)
    print(f"\nFigure written to {file_name}")


if __name__ == "__main__":

    # Freestream conditions
    mach_number = 0.2
    alpha       = 1.0  # angle of attack in degrees

    # Mesh to use
    coarse_mesh = "baseline_coarse"
    medium_mesh = "baseline_medium"
    fine_mesh = "baseline_fine"

    # Output flags
    gid_output = False
    vtk_output = False

    design_space = GenerateDesignSpace()
    
    # Random subset of 4 airfoils for testing
    rng = np.random.default_rng(42)  # fixed seed for reproducibility
    design_space = list(rng.choice(design_space, size=4, replace=False))

    coarse_results = EvaluateAirfoils(design_space, coarse_mesh, mach_number, alpha,
                                      gid_output=gid_output, vtk_output=vtk_output,
                                      pressure_coefficient=True)
    
    medium_results = EvaluateAirfoils(design_space, medium_mesh, mach_number, alpha,
                                      gid_output=gid_output, vtk_output=vtk_output,
                                      pressure_coefficient=True)

    fine_results = EvaluateAirfoils(design_space, fine_mesh, mach_number, alpha,
                                    gid_output=gid_output, vtk_output=vtk_output,
                                    pressure_coefficient=True)

    names = [AsAirfoil(profile).name for profile in design_space]

    cl_coarse = np.array([r.lift_coefficient for r in coarse_results])
    cl_medium = np.array([r.lift_coefficient for r in medium_results])
    cl_fine   = np.array([r.lift_coefficient for r in fine_results])

    time_coarse = np.array([r.solve_time for r in coarse_results])
    time_medium = np.array([r.solve_time for r in medium_results])
    time_fine   = np.array([r.solve_time for r in fine_results])
    
    error_coarse_fine = np.abs(100.0 * (cl_coarse - cl_fine) / cl_fine)
    error_coarse_medium = np.abs(100.0 * (cl_coarse - cl_medium) / cl_medium)
    error_medium_fine = np.abs(100.0 * (cl_medium - cl_fine) / cl_fine)
    
    print("\nNACA 4-Digit Profiles - Coarse / Medium / Fine Comparison:")
    header = (f"{'Airfoil':>10}  {'Cl coarse':>10}  {'Cl medium':>10}  {'Cl fine':>10}  {'error coarse-fine [%]':>10}  {'error coarse-medium [%]':>10}  {'error medium-fine [%]':>10}"
              f"  {'t coarse [s]':>10}  {'t medium [s]':>10}  {'t fine [s]':>10}")
    print(header)
    for i, name in enumerate(names):
        print(f"{name:>10}  {cl_coarse[i]:10.8f}  {cl_medium[i]:10.8f}  {cl_fine[i]:10.8f}"
              f"  {error_coarse_fine[i]:10.3f}  {error_coarse_medium[i]:10.3f}  {error_medium_fine[i]:10.3f}"
              f"  {time_coarse[i]:10.2f}  {time_medium[i]:10.2f}  {time_fine[i]:10.2f}")
    
    print(f"\nMean error: {np.mean([error_coarse_fine, error_coarse_medium, error_medium_fine]):.3f} %, worst error: {np.max([error_coarse_fine, error_coarse_medium, error_medium_fine]):.3f} %")

    PlotPressureAndProfile(coarse_results, medium_results, fine_results, names, mach_number, alpha, "data/run_example_cp_profile.png")
