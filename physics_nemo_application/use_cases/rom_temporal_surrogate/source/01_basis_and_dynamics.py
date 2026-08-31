"""Stage 1 - a POD basis from RomApplication, dynamics learned on it.

Interoperability is the point: the basis is written by RomApplication's
own CalculateRomBasisOutputProcess (numpy format - RightBasisMatrix.npy,
NodeIds.npy, RomParameters.json), fed one snapshot per PrintOutput() from
four transient thermal solves, exactly as a RomApplication workflow would
produce it. rom_bridge.LoadRomBasis reads those files back and the rest
of the pipeline never touches full space again until reconstruction:

    solves -> snapshots -> [RomApplication SVD] -> phi
    trajectories -> ProjectToReducedSpace -> q(t), a handful of numbers
    rom_temporal.Sequence_Model (temporal attention) learns q_t -> q_{t+1}
    conditioned on the conductivity as context.

The truncation keeps every mode above 1e-6 relative singular value; the
attention embedding runs with num_heads=1 because input_dim = n_modes is
small and must be divisible by the head count (the API validates this).

The reduced coordinates are PER-MODE normalized before training (each
mode divided by its own max |q| over the training trajectories): mode 1
carries ~10x the amplitude of mode 2 and ~100x mode 4, and on raw
coordinates the loss optimizes mode 1 only - the higher modes rolled out
in visibly wrong directions. The same lesson as the thermo-mechanical
case's temperature-vs-displacement channels, now in reduced space.

Run time: ~3 minutes (4 transients + sequence-model training on CPU).
"""

import json
import pathlib

import numpy
from matplotlib import pyplot

import KratosMultiphysics as Kratos
from KratosMultiphysics.PhysicsNeMoApplication.bridges import rom_bridge
from KratosMultiphysics.PhysicsNeMoApplication.training import rom_temporal
import thermal_plate

OUTPUT = pathlib.Path("output")
DATA = pathlib.Path("..") / "data"
BASIS = pathlib.Path("output") / "rom_basis"

DIVISIONS = 16
TIME_STEP, END_TIME = 0.005, 0.2          # 40 steps per trajectory
TRAIN_CONDUCTIVITIES = (0.7, 1.0, 1.5, 2.0)
CASE = {"source_amplitude": 1.0, "source_center": (0.5, 0.5)}


def CollectTrajectory(conductivity):
    """One transient solve; returns the (steps, n_nodes) TEMPERATURE states."""
    model = Kratos.Model()
    analysis = thermal_plate.CreateTransientAnalysis(
        model, conductivity=conductivity, divisions=DIVISIONS,
        time_step=TIME_STEP, end_time=END_TIME, **CASE)
    states = []

    def PerStep(model_part):
        states.append([node.GetSolutionStepValue(Kratos.TEMPERATURE)
                       for node in model_part.Nodes])

    thermal_plate.RunTransientAnalysis(analysis, per_step=PerStep)
    return numpy.array(states)


def WriteBasisWithRomApplication(trajectories):
    """Feeds every snapshot to the REAL CalculateRomBasisOutputProcess."""
    from KratosMultiphysics.RomApplication.calculate_rom_basis_output_process import (
        CalculateRomBasisOutputProcess)

    host_model = Kratos.Model()
    host_part = thermal_plate.CreateModelPart(host_model, DIVISIONS)
    process = CalculateRomBasisOutputProcess(host_model, Kratos.Parameters("""{
        "model_part_name"          : "ThermalModelPart",
        "nodal_unknowns"           : ["TEMPERATURE"],
        "rom_basis_output_format"  : "numpy",
        "rom_basis_output_name"    : "RomParameters",
        "rom_basis_output_folder"  : "%s",
        "svd_truncation_tolerance" : 1e-6,
        "print_singular_values"    : true
    }""" % BASIS))
    for trajectory in trajectories:
        for state in trajectory:
            Kratos.VariableUtils().SetSolutionStepValuesVector(
                host_part.Nodes, Kratos.TEMPERATURE, list(state), 0)
            process.PrintOutput()
    process.ExecuteFinalize()


def main():
    OUTPUT.mkdir(exist_ok=True)
    DATA.mkdir(exist_ok=True)
    Kratos.Logger.GetDefaultOutput().SetSeverity(Kratos.Logger.Severity.WARNING)

    trajectories = []
    for conductivity in TRAIN_CONDUCTIVITIES:
        trajectory = CollectTrajectory(conductivity)
        trajectories.append(trajectory)
        print(f"  transient k = {conductivity}: {trajectory.shape[0]} steps, "
              f"{trajectory.shape[1]} nodes")

    WriteBasisWithRomApplication(trajectories)
    basis = rom_bridge.LoadRomBasis(BASIS)
    energy = numpy.cumsum(basis.singular_values ** 2) / (basis.singular_values ** 2).sum()
    print(f"RomApplication basis: {basis.n_modes} modes over {basis.n_dofs} DOFs "
          f"(3-mode energy {energy[min(2, len(energy) - 1)]:.6f})")

    # reduced trajectories: each state becomes n_modes numbers.
    # The snapshots were collected in the part's node order, which is the
    # producer's NodeIds order here - same host part, same iteration.
    q_trajectories = [numpy.stack([rom_bridge.ProjectToReducedSpace(basis, state)
                                   for state in trajectory])
                      for trajectory in trajectories]
    contexts = [numpy.array([conductivity]) for conductivity in TRAIN_CONDUCTIVITIES]
    reconstruction_error = max(
        float(numpy.abs(rom_bridge.ReconstructFromReducedSpace(basis, q[-1])
                        - trajectory[-1]).max())
        for q, trajectory in zip(q_trajectories, trajectories))
    print(f"worst final-state projection error across training: {reconstruction_error:.2e}")

    # per-mode normalization (see the module docstring)
    mode_scales = numpy.max([numpy.abs(q).max(axis=0) for q in q_trajectories], axis=0)
    scaled_trajectories = [q / mode_scales for q in q_trajectories]

    model = rom_temporal.CreateSequenceModel(Kratos.Parameters("""{
        "input_dim"   : %d,
        "context_dim" : 1,
        "num_heads"   : 1,
        "device"      : "cpu"
    }""" % basis.n_modes))
    dataset = rom_temporal.CreateRomTrajectoryDataset(scaled_trajectories, contexts)
    history = rom_temporal.TrainRomTemporalModel(model, dataset, Kratos.Parameters("""{
        "epochs"        : 400,
        "batch_size"    : 4,
        "learning_rate" : 1e-3,
        "echo_interval" : 50,
        "device"        : "cpu",
        "seed"          : 0
    }"""))
    print(f"sequence-model loss: {history[0]:.3e} -> {history[-1]:.3e}")
    rom_temporal.SaveRomTemporalModel(model, Kratos.Parameters("""{
        "input_dim"   : %d,
        "context_dim" : 1,
        "num_heads"   : 1
    }""" % basis.n_modes), OUTPUT / "rom_dynamics.pt")

    # ---- figures: modes + spectrum + training ------------------------------
    n_show = min(4, basis.n_modes)
    figure, axes = pyplot.subplots(1, n_show + 1, figsize=(3.1 * (n_show + 1), 3.2))
    grid = int(numpy.sqrt(basis.n_nodes))
    for mode, axis in enumerate(axes[:-1]):
        shape = basis.phi[:, mode].reshape(grid, grid)
        plot = axis.imshow(shape.T, origin="lower", cmap="RdBu_r")
        figure.colorbar(plot, ax=axis, shrink=0.75)
        axis.set_title(f"mode {mode + 1}", fontsize=10)
        axis.set_xticks([])
        axis.set_yticks([])
    axes[-1].semilogy(numpy.arange(1, basis.n_modes + 1),
                      basis.singular_values / basis.singular_values[0], "o-")
    axes[-1].set_xlabel("mode")
    axes[-1].set_title("singular values (relative)", fontsize=10)
    axes[-1].grid(True, which="both", alpha=0.3)
    figure.suptitle("The POD basis, as RomApplication wrote it")
    figure.tight_layout()
    figure.savefig(DATA / "pod_basis.png", dpi=130)

    figure, axis = pyplot.subplots(figsize=(6.4, 3.6))
    axis.semilogy(history)
    axis.set_xlabel("epoch")
    axis.set_ylabel("next-step MSE in reduced space")
    axis.set_title("Temporal-attention dynamics training")
    axis.grid(True, which="both", alpha=0.3)
    figure.tight_layout()
    figure.savefig(DATA / "rom_training.png", dpi=130)

    numpy.save(OUTPUT / "mode_scales.npy", mode_scales)
    numpy.savez(OUTPUT / "trajectories.npz",
                **{f"q_{k}": q for k, q in zip(TRAIN_CONDUCTIVITIES, q_trajectories)})
    with open(OUTPUT / "basis_summary.json", "w") as handle:
        json.dump({"n_modes": basis.n_modes, "n_dofs": basis.n_dofs,
                   "energy_3": float(energy[min(2, len(energy) - 1)]),
                   "projection_error": reconstruction_error,
                   "loss_first": float(history[0]), "loss_last": float(history[-1])},
                  handle, indent=1)
    print(f"figures: {DATA / 'pod_basis.png'}, {DATA / 'rom_training.png'}")


if __name__ == "__main__":
    main()
