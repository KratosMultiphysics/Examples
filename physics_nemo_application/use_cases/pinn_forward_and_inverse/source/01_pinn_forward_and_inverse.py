"""PINN solves against the real FEM solution - forward and inverse.

PinnSolveProcess solves the PDE with a neural network and NO mesh
assembly: collocation points are the model part's nodes, boundary data its
fixed DOFs. Two demonstrations against ConvectionDiffusion ground truth:

1. **Forward**: -k lap(u) = f on the unit plate from its Dirichlet data
   alone, compared against the FEM solution of the same BVP. The PDE is
   declared 2D ("dim": 2, a setting this example motivated): with the 3D
   operator on a planar cloud, u_zz is unconstrained and the PINN cancels
   the source with z-curvature - converged loss, half the amplitude.
2. **Inverse**: the conductivity k is recovered from the FEM temperature
   field as a trainable scalar ("mode": "inverse", inverse_parameters),
   starting from a 4x-wrong guess. Joint optimization of network and
   coefficient is genuinely sensitive to the data/physics weighting; the
   settings here recover k within ~10%.

Run time: ~2 minutes.
"""

import json
import pathlib

import numpy
from matplotlib import pyplot, tri

import KratosMultiphysics as Kratos
from KratosMultiphysics.PhysicsNeMoApplication.processes.inference import pinn_solve_process
import thermal_case

OUTPUT = pathlib.Path("output")
DATA = pathlib.Path("..") / "data"

CONDUCTIVITY = 1.5
HEAT_FLUX = 1.0
DIVISIONS = 20


def MeshArrays(model_part):
    points = numpy.array([[node.X, node.Y] for node in model_part.Nodes])
    rows = {node.Id: index for index, node in enumerate(model_part.Nodes)}
    triangles = numpy.array([[rows[element.GetGeometry()[i].Id] for i in range(3)]
                             for element in model_part.Elements])
    return points, triangles


def PinnForwardSettings(part_name, normalize, source=0.0, conductivity=1.0):
    return Kratos.Parameters("""{
        "Parameters": {
            "model_part_name" : "%s",
            "mode"            : "forward",
            "physics"         : { "pde" : "builtin:diffusion",
                                  "pde_arguments" : { "D" : %f, "source" : %f, "dim" : 2 } },
            "solution_fields" : [ { "variable_name" : "TEMPERATURE", "data_location" : "node_historical" } ],
            "output_fields"   : [ { "variable_name" : "TEMPERATURE", "data_location" : "node_historical" } ],
            "network"         : { "layer_size" : 48, "num_layers" : 4 },
            "training"        : { "epochs" : 1500, "learning_rate" : 4e-3,
                                  "boundary_weight" : 10.0, "seed" : 0 },
            "device"          : "cpu",
            "normalize_coordinates" : %s
        }
    }""" % (part_name, conductivity, source, "true" if normalize else "false"))


def main():
    OUTPUT.mkdir(exist_ok=True)
    DATA.mkdir(exist_ok=True)
    Kratos.Logger.GetDefaultOutput().SetSeverity(Kratos.Logger.Severity.WARNING)

    # ---- 1. forward PINN vs FEM on the unit plate --------------------------
    model = Kratos.Model()
    analysis = thermal_case.CreateThermalAnalysis(
        model, conductivity=CONDUCTIVITY, heat_flux=HEAT_FLUX, divisions=DIVISIONS)
    analysis.Run()
    model_part = model["ThermalModelPart"]
    fem = numpy.array([node.GetSolutionStepValue(Kratos.TEMPERATURE)
                       for node in model_part.Nodes])

    # the PINN gets ONLY the Dirichlet data (already fixed on the boundary
    # nodes); the interior values it must find from the PDE. Note the sign
    # convention of builtin:diffusion: residual = D*lap(u) + source, so the
    # plate's -k lap(u) = f becomes D = k with source = +f.
    forward = pinn_solve_process.Factory(
        PinnForwardSettings("ThermalModelPart", normalize=True,
                            source=HEAT_FLUX, conductivity=CONDUCTIVITY), model)
    forward.ExecuteBeforeSolutionLoop()
    pinn = numpy.array([node.GetSolutionStepValue(Kratos.TEMPERATURE)
                        for node in model_part.Nodes])
    forward_rmse = float(numpy.sqrt(numpy.mean((pinn - fem) ** 2)))
    print(f"forward: PINN vs FEM rmse {forward_rmse:.2e} "
          f"(field max {numpy.abs(fem).max():.2e})")

    points, triangles = MeshArrays(model_part)
    triangulation = tri.Triangulation(points[:, 0], points[:, 1], triangles)
    figure, axes = pyplot.subplots(1, 3, figsize=(13.2, 3.9))
    limits = dict(levels=20, cmap="viridis", vmin=float(fem.min()), vmax=float(fem.max()))
    for axis, (values, title) in zip(axes[:2], [(fem, "FEM"), (pinn, "PINN (mesh-free)")]):
        mappable = axis.tricontourf(triangulation, values, **limits)
        axis.set_aspect("equal")
        axis.set_title(f"TEMPERATURE ({title})")
        figure.colorbar(mappable, ax=axis, shrink=0.85)
    error_map = axes[2].tricontourf(triangulation, numpy.abs(pinn - fem),
                                    levels=20, cmap="magma")
    axes[2].set_aspect("equal")
    axes[2].set_title("absolute difference")
    figure.colorbar(error_map, ax=axes[2], shrink=0.85)
    figure.tight_layout()
    figure.savefig(DATA / "pinn_forward.png", dpi=130)


    # ---- 2. inverse: recover k from the FEM field --------------------------
    # restore the FEM field (the forward PINN overwrote TEMPERATURE) and use
    # it as the observation; k becomes a trainable scalar
    for node, value in zip(model_part.Nodes, fem):
        node.SetSolutionStepValue(Kratos.TEMPERATURE, value)
        node.SetValue(Kratos.NODAL_PAUX, value)
    inverse = pinn_solve_process.Factory(Kratos.Parameters("""{
        "Parameters": {
            "model_part_name"    : "ThermalModelPart",
            "mode"               : "inverse",
            "physics"            : { "pde" : "builtin:diffusion",
                                     "pde_arguments" : { "D" : null, "source" : %f, "dim" : 2 } },
            "inverse_parameters" : { "D" : 0.4 },
            "observation_fields" : [ { "variable_name" : "NODAL_PAUX", "data_location" : "node_non_historical" } ],
            "network"            : { "layer_size" : 48, "num_layers" : 4 },
            "training"           : { "epochs" : 2500, "learning_rate" : 5e-3,
                                     "data_weight" : 500.0, "seed" : 0 },
            "device"             : "cpu",
            "normalize_coordinates" : true
        }
    }""" % HEAT_FLUX), model)
    inverse.Solve()
    recovered = float(inverse.inverse_values["D"])
    print(f"inverse: recovered k = {recovered:.4f} (true {CONDUCTIVITY}, "
          f"started from 0.4)")

    figure, axes = pyplot.subplots(1, 2, figsize=(10.2, 3.9))
    axes[0].semilogy(forward.loss_history, label="forward")
    axes[0].semilogy(inverse.loss_history, label="inverse")
    axes[0].set_xlabel("epoch")
    axes[0].set_ylabel("loss")
    axes[0].set_title("PINN training")
    axes[0].legend()
    axes[0].grid(True, which="both", alpha=0.3)
    axes[1].bar(["initial guess", "recovered", "true k"],
                [0.4, recovered, CONDUCTIVITY],
                color=["#7f8c8d", "#2980b9", "#27ae60"])
    axes[1].set_ylabel("conductivity")
    axes[1].set_title("Inverse recovery from the FEM field")
    axes[1].grid(True, axis="y", alpha=0.3)
    figure.tight_layout()
    figure.savefig(DATA / "pinn_inverse.png", dpi=130)

    with open(OUTPUT / "pinn_summary.json", "w") as handle:
        json.dump({"forward_rmse": forward_rmse,
                   "recovered_conductivity": recovered,
                   "true_conductivity": CONDUCTIVITY}, handle, indent=1)
    print(f"figures: pinn_forward.png, pinn_inverse.png")


if __name__ == "__main__":
    main()
