"""Three views of "when should I trust this surrogate?".

One surrogate family (an ensemble of (x, y, k) -> T MLPs trained on
k in [0.5, 2.0]), interrogated three ways along a sweep that walks far
outside the training range:

1. **Ensemble spread** - the epistemic error bar: small where training
   data lives, growing where the members extrapolate differently -
   compared against the ACTUAL error, which needs the reference solves
   the user of a surrogate does not have.
2. **Calibration metrics** (ComputeCalibrationMetricValues): coverage,
   calibration error, NLL and sharpness of the ensemble's error bars on
   held-out in-range cases - the question an RMSE cannot answer: are the
   stated uncertainties HONEST?
3. **The OOD guard** (trained-input calibration + per-query verdict):
   the binary tripwire that needs no ensemble at all.

Run time: ~2 minutes (training solves + a 15-point sweep of solves for
the reference error).
"""

import json
import pathlib

import numpy
import torch
from matplotlib import pyplot

import KratosMultiphysics as Kratos
from KratosMultiphysics.ConvectionDiffusionApplication.convection_diffusion_analysis import (
    ConvectionDiffusionAnalysis)
from KratosMultiphysics.PhysicsNeMoApplication import ood_guard_utils
from KratosMultiphysics.PhysicsNeMoApplication.validation_metrics_process import (
    ComputeCalibrationMetricValues)

import thermal_plate

OUTPUT = pathlib.Path("output")
DATA = pathlib.Path("..") / "data"

TRAIN_KS = numpy.linspace(0.5, 2.0, 6)
SWEEP_KS = numpy.linspace(0.2, 4.0, 15)
CALIBRATION_KS = numpy.linspace(0.55, 1.95, 8)   # held-out, in range
DIVISIONS = 16
SEEDS = (0, 1, 2, 3)


def Solve(conductivity):
    model = Kratos.Model()
    part = thermal_plate.CreateModelPart(model, DIVISIONS)
    thermal_plate.ApplyCase(part, float(conductivity), 1.0, (0.5, 0.5))
    ConvectionDiffusionAnalysis(model, thermal_plate._ProjectParameters()).Run()
    return numpy.array([node.GetSolutionStepValue(Kratos.TEMPERATURE)
                        for node in part.Nodes])


def main():
    OUTPUT.mkdir(exist_ok=True)
    DATA.mkdir(exist_ok=True)
    Kratos.Logger.GetDefaultOutput().SetSeverity(Kratos.Logger.Severity.WARNING)

    model = Kratos.Model()
    part = thermal_plate.CreateModelPart(model, DIVISIONS)
    coordinates = numpy.array([[node.X, node.Y] for node in part.Nodes])

    # ---- train the ensemble ------------------------------------------------
    fields = {float(k): Solve(k) for k in TRAIN_KS}
    inputs, targets = [], []
    for k, field in fields.items():
        for (x, y), value in zip(coordinates, field):
            inputs.append([x, y, k])
            targets.append([value])
    inputs = torch.tensor(inputs, dtype=torch.float64)
    targets = torch.tensor(targets, dtype=torch.float64)

    members = []
    for seed in SEEDS:
        torch.manual_seed(seed)
        member = torch.nn.Sequential(
            torch.nn.Linear(3, 48), torch.nn.Tanh(),
            torch.nn.Linear(48, 48), torch.nn.Tanh(),
            torch.nn.Linear(48, 1)).double()
        optimizer = torch.optim.Adam(member.parameters(), lr=2e-3)
        for _ in range(600):
            optimizer.zero_grad()
            torch.nn.functional.mse_loss(member(inputs), targets).backward()
            optimizer.step()
        members.append(member.eval())
    print(f"{len(members)}-member ensemble trained on k in "
          f"[{TRAIN_KS[0]}, {TRAIN_KS[-1]}]")

    def Predict(k):
        batch = torch.tensor(
            numpy.column_stack([coordinates, numpy.full(len(coordinates), k)]),
            dtype=torch.float64)
        with torch.no_grad():
            stack = numpy.stack([m(batch).numpy()[:, 0] for m in members])
        return stack.mean(axis=0), stack.std(axis=0, ddof=1)

    # ---- view 1: spread vs actual error along the sweep --------------------
    sweep_error, sweep_spread = [], []
    for k in SWEEP_KS:
        mean, spread = Predict(float(k))
        reference = Solve(float(k))
        sweep_error.append(float(numpy.sqrt(numpy.mean((mean - reference) ** 2))))
        sweep_spread.append(float(spread.mean()))
        print(f"  k = {k:4.2f}: rmse {sweep_error[-1]:.2e}, "
              f"ensemble spread {sweep_spread[-1]:.2e}")

    # ---- view 2: calibration on held-out IN-RANGE cases --------------------
    means, stds, references = [], [], []
    for k in CALIBRATION_KS:
        mean, spread = Predict(float(k))
        means.append(mean)
        stds.append(spread)
        references.append(Solve(float(k)))
    calibration = ComputeCalibrationMetricValues(
        torch.tensor(numpy.concatenate(means)),
        torch.tensor(numpy.concatenate(stds)),
        torch.tensor(numpy.concatenate(references)),
        ["coverage", "calibration_error", "nll", "sharpness"])
    calibration = {key: float(value) for key, value in calibration.items()}
    print("calibration (in-range, z = 1.96):",
          {key: round(value, 4) for key, value in calibration.items()})

    # ---- view 3: the OOD guard on the same sweep ---------------------------
    rows = inputs.to(torch.float32)
    guard = ood_guard_utils.CreateOODGuard(4096, 3, 10, 6.0)
    for start in range(0, rows.shape[0], 1024):
        chunk = rows[start:start + 1024]
        guard.collect(chunk, chunk.mean(dim=0, keepdim=True))
    verdicts = []
    for k in SWEEP_KS:
        features = torch.tensor(
            numpy.column_stack([coordinates, numpy.full(len(coordinates), k)]),
            dtype=torch.float32)
        verdicts.append(bool(ood_guard_utils.CheckFeatures(guard, features)))

    # ---- figures -----------------------------------------------------------
    figure, axis = pyplot.subplots(figsize=(8.2, 4.4))
    axis.semilogy(SWEEP_KS, sweep_error, "k-o", markersize=4,
                  label="actual RMSE (needs reference solves)")
    axis.semilogy(SWEEP_KS, sweep_spread, "b--s", markersize=4,
                  label="ensemble spread (available at deployment)")
    axis.axvspan(TRAIN_KS[0], TRAIN_KS[-1], alpha=0.12, color="#27ae60",
                 label="training range")
    axis.set_xlabel("conductivity k")
    axis.set_ylabel("temperature-field error / spread")
    axis.set_title("The epistemic error bar tracks the real error out of range")
    axis.legend()
    axis.grid(True, which="both", alpha=0.3)
    figure.tight_layout()
    figure.savefig(DATA / "uncertainty_sweep.png", dpi=130)

    figure, axes = pyplot.subplots(1, 2, figsize=(11.4, 3.9))
    names = ["coverage", "calibration_error", "nll", "sharpness"]
    axes[0].bar(names, [calibration[name] for name in names], color="#2980b9")
    axes[0].axhline(0.95, color="#27ae60", linestyle="--", linewidth=1,
                    label="nominal coverage (z = 1.96)")
    axes[0].set_title("Calibration of the in-range error bars")
    axes[0].legend()
    axes[0].grid(True, axis="y", alpha=0.3)
    colors = ["#c0392b" if flagged else "#27ae60" for flagged in verdicts]
    axes[1].scatter(SWEEP_KS, [1 if v else 0 for v in verdicts], c=colors, s=48, zorder=3)
    axes[1].axvspan(TRAIN_KS[0], TRAIN_KS[-1], alpha=0.12, color="#27ae60")
    axes[1].set_yticks([0, 1], ["in distribution", "flagged OOD"])
    axes[1].set_xlabel("conductivity k")
    axes[1].set_title("The OOD guard's verdict (no ensemble needed)")
    axes[1].grid(True, alpha=0.3)
    figure.tight_layout()
    figure.savefig(DATA / "calibration_and_guard.png", dpi=130)

    with open(OUTPUT / "trust_summary.json", "w") as handle:
        json.dump({"sweep_ks": SWEEP_KS.tolist(), "error": sweep_error,
                   "spread": sweep_spread, "calibration": calibration,
                   "ood_flagged": verdicts}, handle, indent=1)
    print(f"figures: {DATA / 'uncertainty_sweep.png'}, {DATA / 'calibration_and_guard.png'}")


if __name__ == "__main__":
    main()
