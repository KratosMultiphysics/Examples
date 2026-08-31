"""Stage 1 - train a 2D upsampler on matched coarse/fine transient solves.

The training pairs come from TRANSIENTS, not steady states: for each
conductivity in a sweep, the plate is heated from zero by the Gaussian
source on a coarse 8x8 mesh and on a fine 32x32 mesh, and every time step
contributes one (coarse grid -> fine grid) pair. The upsampler therefore
sees the whole heating transient - early sharp-gradient states included -
which is what lets it upscale inside a running simulation in Stage 2.

The model is bilinear interpolation plus a learned convolutional
correction (see Upsampler2D), saved as TorchScript: the deployment
process accepts any checkpoint, not just PhysicsNeMo natives.

Run time: ~2 minutes (12 transient solves + training).
"""

import json
import pathlib

import numpy
import torch
from matplotlib import pyplot

import KratosMultiphysics as Kratos
from KratosMultiphysics.PhysicsNeMoApplication.bridges import grid_bridge
import thermal_plate

OUTPUT = pathlib.Path("output")
DATA = pathlib.Path("..") / "data"

TRAIN_CONDUCTIVITIES = numpy.linspace(0.6, 1.8, 6)
COARSE_DIVISIONS, FINE_DIVISIONS = 8, 32
COARSE_GRID, FINE_GRID = (9, 9, 2), (33, 33, 2)   # node-aligned grids
BOUNDING_BOX = (numpy.array([0.0, 0.0, -0.05]), numpy.array([1.0, 1.0, 0.05]))
TIME_STEP, END_TIME = 0.005, 0.2                   # 40 steps
CASE = {"source_amplitude": 1.0, "source_center": (0.5, 0.5)}


class Upsampler2D(torch.nn.Module):
    """(C, 9, 9) -> (C, 33, 33) as bilinear + a learned correction.

    The bilinear upsample is computed first and the network learns only the
    RESIDUAL on top of it, with a zero-initialized last layer: untrained,
    the model IS the bilinear baseline, so training can only improve on it.
    What the correction learns is precisely what interpolation cannot know
    - the coarse SOLVE's own discretization error against the fine solve.
    """

    def __init__(self, channels: int = 1, width: int = 32):
        super().__init__()
        self.body = torch.nn.Sequential(
            torch.nn.Conv2d(channels, width, 3, padding=1), torch.nn.GELU(),
            torch.nn.Conv2d(width, width, 3, padding=1), torch.nn.GELU(),
            torch.nn.Conv2d(width, width, 3, padding=1), torch.nn.GELU(),
            torch.nn.Conv2d(width, channels, 3, padding=1))
        torch.nn.init.zeros_(self.body[-1].weight)
        torch.nn.init.zeros_(self.body[-1].bias)

    def forward(self, grid):
        baseline = torch.nn.functional.interpolate(
            grid, size=(33, 33), mode="bilinear", align_corners=True)
        return baseline + self.body(baseline)


def CollectTransient(conductivity, divisions, grid_shape):
    """One transient solve; returns the (T, C, H, W) squeezed grid states."""
    model = Kratos.Model()
    analysis = thermal_plate.CreateTransientAnalysis(
        model, conductivity=float(conductivity), divisions=divisions,
        time_step=TIME_STEP, end_time=END_TIME, **CASE)
    states = []

    def PerStep(model_part):
        grid, _ = grid_bridge.SampleFieldsOnGrid(
            model_part, [("TEMPERATURE", "node_historical")], grid_shape, BOUNDING_BOX)
        states.append(grid.mean(axis=3))   # squeeze the thin axis -> (C, H, W)

    thermal_plate.RunTransientAnalysis(analysis, per_step=PerStep)
    return numpy.stack(states)


def main():
    OUTPUT.mkdir(exist_ok=True)
    DATA.mkdir(exist_ok=True)
    Kratos.Logger.GetDefaultOutput().SetSeverity(Kratos.Logger.Severity.WARNING)

    coarse_states, fine_states = [], []
    for conductivity in TRAIN_CONDUCTIVITIES:
        coarse_states.append(CollectTransient(conductivity, COARSE_DIVISIONS, COARSE_GRID))
        fine_states.append(CollectTransient(conductivity, FINE_DIVISIONS, FINE_GRID))
        print(f"  k = {conductivity:.2f}: {coarse_states[-1].shape[0]} transient steps collected")
    inputs = torch.from_numpy(numpy.concatenate(coarse_states)).float()
    targets = torch.from_numpy(numpy.concatenate(fine_states)).float()
    print(f"training pairs: {inputs.shape[0]} (coarse {tuple(inputs.shape[1:])} "
          f"-> fine {tuple(targets.shape[1:])})")

    torch.manual_seed(0)
    upsampler = Upsampler2D()
    optimizer = torch.optim.Adam(upsampler.parameters(), lr=2e-3)
    losses = []
    for step in range(800):
        optimizer.zero_grad()
        loss = torch.nn.functional.mse_loss(upsampler(inputs), targets)
        loss.backward()
        optimizer.step()
        losses.append(loss.item())
    print(f"final loss: {losses[-1]:.3e}")

    upsampler.eval()
    torch.jit.script(upsampler).save(str(OUTPUT / "upsampler2d.pt"))

    figure, axis = pyplot.subplots(figsize=(6.2, 3.8))
    axis.semilogy(losses)
    axis.set_xlabel("step")
    axis.set_ylabel("MSE")
    axis.set_title("2D upsampler training (240 transient snapshots)")
    axis.grid(True, which="both", alpha=0.3)
    figure.tight_layout()
    figure.savefig(DATA / "upsampler_training.png", dpi=130)

    with open(OUTPUT / "train_summary.json", "w") as handle:
        json.dump({"pairs": int(inputs.shape[0]), "final_loss": losses[-1]}, handle, indent=1)
    print(f"figure : {DATA / 'upsampler_training.png'}")


if __name__ == "__main__":
    main()
