"""Stage 1 - train the warm-start surrogate on a handful of solves.

Four Newton-Raphson solves at training loads provide the data: per node,
(X, Y, scaled load) -> (ux, uy). The MLP bakes its per-channel output
scales INTO the TorchScript module (temperature-vs-displacement magnitude
lessons from the transient case apply here too: uy is ~10x ux), pads the
third displacement component with zero, and is saved as a plain
checkpoint that HybridInitializationProcess loads by file name.

Trained HARD on purpose: Adam to get close, then a long LBFGS polish.
Warm starting rewards accuracy in the RESIDUAL, not in displacement
distance - stage 2's seed-quality experiment shows an Adam-only fit
(RMSE ~9e-4 m) makes Newton take MORE iterations than a cold start,
while the polished fit (~1.3e-4 m) saves iterations everywhere.

Run time: well under a minute.
"""

import json
import pathlib

import numpy
import torch
from matplotlib import pyplot

import KratosMultiphysics as Kratos
import KratosMultiphysics.PhysicsNeMoApplication  # registers the application  # noqa: F401

import structural_cantilever

OUTPUT = pathlib.Path("output")
DATA = pathlib.Path("..") / "data"

DIVISIONS = 8
LOAD_SCALE = 1.0e7                        # NODAL_VAUX carries load / LOAD_SCALE
TRAIN_LOADS = (0.5e7, 1.5e7, 2.5e7, 3.5e7)


def SolveCantilever(tip_load):
    model = Kratos.Model()
    analysis, part = structural_cantilever.CreateAnalysis(model, tip_load, DIVISIONS)
    analysis.Run()
    inputs = numpy.array([[node.X0, node.Y0, tip_load / LOAD_SCALE]
                          for node in part.Nodes])
    targets = numpy.array([[node.GetSolutionStepValue(Kratos.DISPLACEMENT_X),
                            node.GetSolutionStepValue(Kratos.DISPLACEMENT_Y)]
                           for node in part.Nodes])
    iterations = part.ProcessInfo[Kratos.NL_ITERATION_NUMBER]
    return inputs, targets, iterations, structural_cantilever.GetTipDeflection(part)


class WarmStartModel(torch.nn.Module):
    """(N, 3) NODAL_VAUX rows -> (N, 3) DISPLACEMENT rows (z = 0).

    Output scales are buffers, so the deployed forward pass is exactly
    net(x) * scale - no normalization code outside the checkpoint.
    """

    def __init__(self, scale):
        super().__init__()
        self.net = torch.nn.Sequential(
            torch.nn.Linear(3, 128), torch.nn.Tanh(),
            torch.nn.Linear(128, 128), torch.nn.Tanh(), torch.nn.Linear(128, 2))
        self.register_buffer("scale", scale)

    def forward(self, x):
        planar = self.net(x) * self.scale
        return torch.cat([planar, torch.zeros_like(planar[:, :1])], dim=1)


def main():
    OUTPUT.mkdir(exist_ok=True)
    DATA.mkdir(exist_ok=True)
    Kratos.Logger.GetDefaultOutput().SetSeverity(Kratos.Logger.Severity.WARNING)

    all_inputs, all_targets, solve_log = [], [], []
    for load in TRAIN_LOADS:
        inputs, targets, iterations, tip = SolveCantilever(load)
        all_inputs.append(inputs)
        all_targets.append(targets)
        solve_log.append({"load": load, "iterations": iterations, "tip": tip})
        print(f"  training solve load {load:.1e}: {iterations} Newton iterations, "
              f"tip {tip:+.4f} m")

    inputs = torch.tensor(numpy.concatenate(all_inputs), dtype=torch.float64)
    targets = torch.tensor(numpy.concatenate(all_targets), dtype=torch.float64)
    # per-channel scales (ux is ~10x smaller than uy - one global scale
    # would train the vertical channel only)
    scale = targets.abs().amax(dim=0)
    normalized_targets = targets / scale

    torch.manual_seed(0)
    model = WarmStartModel(scale).double()
    optimizer = torch.optim.Adam(model.parameters(), lr=2e-3)
    losses = []
    for _ in range(4000):
        optimizer.zero_grad()
        loss = torch.nn.functional.mse_loss(model.net(inputs), normalized_targets)
        loss.backward()
        optimizer.step()
        losses.append(loss.item())
    adam_steps = len(losses)

    # the polish that makes the warm start pay: LBFGS drives the small
    # dense problem 1-2 orders of magnitude below where Adam stalls
    lbfgs = torch.optim.LBFGS(model.parameters(), max_iter=800, history_size=50,
                              tolerance_grad=1e-15, tolerance_change=1e-18)

    def Closure():
        lbfgs.zero_grad()
        loss = torch.nn.functional.mse_loss(model.net(inputs), normalized_targets)
        loss.backward()
        losses.append(loss.item())
        return loss

    lbfgs.step(Closure)
    model.eval()

    with torch.no_grad():
        fit_rmse = float(torch.sqrt(
            ((model(inputs)[:, :2] - targets) ** 2).mean()))
    torch.jit.script(model).save(str(OUTPUT / "cantilever_warmstart.pt"))
    print(f"fit RMSE {fit_rmse:.2e} m on {len(inputs)} training rows")

    figure, axis = pyplot.subplots(figsize=(6.4, 3.8))
    axis.semilogy(losses)
    axis.axvline(adam_steps, color="gray", linestyle="--", linewidth=1)
    axis.text(adam_steps + 40, max(losses) / 10, "LBFGS polish", fontsize=9, color="gray")
    axis.set_xlabel("optimizer step")
    axis.set_ylabel("normalized MSE")
    axis.set_title("Warm-start surrogate training")
    axis.grid(True, which="both", alpha=0.3)
    figure.tight_layout()
    figure.savefig(DATA / "warmstart_training.png", dpi=130)

    with open(OUTPUT / "training_summary.json", "w") as handle:
        json.dump({"train_loads": list(TRAIN_LOADS), "fit_rmse": fit_rmse,
                   "solves": solve_log}, handle, indent=1)
    print(f"checkpoint: {OUTPUT / 'cantilever_warmstart.pt'}")


if __name__ == "__main__":
    main()
