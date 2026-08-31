"""Stage 2 - rollout at an unseen conductivity, reconstructed to full space.

The trained sequence model is prompted with the first four projected
states of a k = 1.2 transient (a conductivity between training samples),
told the conductivity as context, and rolled out for the remaining 36
steps in the 8-dimensional reduced space. rom_bridge reconstructs any
step back to the full 289-node field.

Two comparisons keep the claim honest:

* against the PROJECTED truth (the best any model in this basis can do)
  - isolates the dynamics error from the truncation error;
* against the full solver field - what a user of the reconstruction sees.

Run time: under a minute (one transient solve + a reduced-space rollout).
"""

import json
import pathlib

import numpy
from matplotlib import pyplot

import KratosMultiphysics as Kratos
from KratosMultiphysics.PhysicsNeMoApplication.bridges import rom_bridge
from KratosMultiphysics.PhysicsNeMoApplication.training import rom_temporal
import importlib
stage1 = importlib.import_module("01_basis_and_dynamics")
import thermal_plate

OUTPUT = pathlib.Path("output")
DATA = pathlib.Path("..") / "data"

UNSEEN_CONDUCTIVITY = 1.2
PROMPT_STEPS = 4


def main():
    OUTPUT.mkdir(exist_ok=True)
    DATA.mkdir(exist_ok=True)
    Kratos.Logger.GetDefaultOutput().SetSeverity(Kratos.Logger.Severity.WARNING)

    truth = stage1.CollectTrajectory(UNSEEN_CONDUCTIVITY)      # (40, 289)
    basis = rom_bridge.LoadRomBasis(stage1.BASIS)
    q_truth = numpy.stack([rom_bridge.ProjectToReducedSpace(basis, state)
                           for state in truth])                # (40, 8)

    model, _ = rom_temporal.LoadRomTemporalModel(str(OUTPUT / "rom_dynamics.pt"))
    # the model lives in per-mode-normalized coordinates (stage 1)
    mode_scales = numpy.load(OUTPUT / "mode_scales.npy")
    q_predicted = rom_temporal.PredictRomTrajectory(
        model, q_truth[:PROMPT_STEPS] / mode_scales,
        steps=len(truth) - PROMPT_STEPS,
        context=numpy.array([UNSEEN_CONDUCTIVITY])) * mode_scales   # (40, 8)

    reconstructed = numpy.stack([rom_bridge.ReconstructFromReducedSpace(basis, q)
                                 for q in q_predicted])        # (40, 289)
    projected = numpy.stack([rom_bridge.ReconstructFromReducedSpace(basis, q)
                             for q in q_truth])

    scale = float(numpy.abs(truth[-1]).max())
    dynamics_rmse = float(numpy.sqrt(((reconstructed - projected) ** 2).mean()))
    total_rmse = float(numpy.sqrt(((reconstructed - truth) ** 2).mean()))
    truncation_rmse = float(numpy.sqrt(((projected - truth) ** 2).mean()))
    final_error = float(numpy.abs(reconstructed[-1] - truth[-1]).max())
    print(f"k = {UNSEEN_CONDUCTIVITY} (unseen): rollout-vs-projected RMSE {dynamics_rmse:.2e}, "
          f"truncation RMSE {truncation_rmse:.2e}, total {total_rmse:.2e} "
          f"(final field max {scale:.4f}, max final error {final_error:.2e})")

    # ---- coefficient trajectories ------------------------------------------
    time = (numpy.arange(len(truth)) + 1) * stage1.TIME_STEP
    n_show = min(4, basis.n_modes)
    figure, axes = pyplot.subplots(1, n_show, figsize=(3.3 * n_show, 3.2), sharex=True)
    for mode, axis in enumerate(axes):
        axis.plot(time, q_truth[:, mode], label="projected truth", linewidth=1.8)
        axis.plot(time, q_predicted[:, mode], "--", label="rollout", linewidth=1.8)
        axis.axvline(time[PROMPT_STEPS - 1], color="gray", linewidth=0.9, linestyle=":")
        axis.set_title(f"q{mode + 1}(t)", fontsize=10)
        axis.set_xlabel("time [s]")
        axis.grid(True, alpha=0.3)
    axes[0].legend(fontsize=8)
    figure.suptitle(f"Reduced coordinates at unseen k = {UNSEEN_CONDUCTIVITY} "
                    "(prompt left of the dotted line)")
    figure.tight_layout()
    figure.savefig(DATA / "coefficient_rollout.png", dpi=130)

    # ---- final-time fields --------------------------------------------------
    grid = int(numpy.sqrt(basis.n_nodes))
    figure, axes = pyplot.subplots(1, 3, figsize=(11.4, 3.5))
    limits = dict(vmin=0.0, vmax=float(truth[-1].max()))
    panels = [(truth[-1], "solver, final step", "inferno", limits),
              (reconstructed[-1], "ROM rollout, reconstructed", "inferno", limits),
              (numpy.abs(reconstructed[-1] - truth[-1]), "absolute error", "viridis", {})]
    for axis, (field, title, cmap, kwargs) in zip(axes, panels):
        plot = axis.imshow(field.reshape(grid, grid).T, origin="lower", cmap=cmap, **kwargs)
        figure.colorbar(plot, ax=axis, shrink=0.85)
        axis.set_title(title, fontsize=10)
        axis.set_xticks([])
        axis.set_yticks([])
    figure.suptitle(f"Full-space reconstruction after 36 generated steps, k = {UNSEEN_CONDUCTIVITY}")
    figure.tight_layout()
    figure.savefig(DATA / "rom_reconstruction.png", dpi=130)

    with open(OUTPUT / "rollout_summary.json", "w") as handle:
        json.dump({"unseen_conductivity": UNSEEN_CONDUCTIVITY,
                   "prompt_steps": PROMPT_STEPS,
                   "dynamics_rmse": dynamics_rmse, "truncation_rmse": truncation_rmse,
                   "total_rmse": total_rmse, "final_max_error": final_error,
                   "field_scale": scale}, handle, indent=1)
    print(f"figures: {DATA / 'coefficient_rollout.png'}, {DATA / 'rom_reconstruction.png'}")


if __name__ == "__main__":
    main()
