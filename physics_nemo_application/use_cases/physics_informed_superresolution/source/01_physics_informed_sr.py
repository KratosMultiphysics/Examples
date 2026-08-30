"""Physics-refined superresolution: the PDE residual as a differentiable grader.

A learned upsampler (trilinear + a zero-initialized convolutional
correction, the residual-over-baseline design of the transient
superresolution example, here in 3D) upscales coarse-mesh thermal solves
(8^3 grids) to fine-mesh ones (16^3). Trained on pixels it beats
trilinear by RMSE - and is still mediocre *physics*: the
finite-difference residual of -k lap(u) = f on its output is orders of
magnitude above the fine solve's own, because FD second derivatives
amplify exactly the high-frequency error a pixel metric cannot see.

The fix demonstrated here is REFINEMENT, not retraining: the residual
term from physics_informed.MakePhysicsLossTerm (grad_method
"finite_difference", boundary_trim 1) is differentiable, and minimizing

    residual^2(v) + lambda * ||v - v_SR||^2

over the OUTPUT FIELD v is a nearly quadratic problem that 300 Adam steps
solve. The refined field satisfies the PDE better than the fine solve
itself, at a small RMSE cost against the (already excellent) upsampler -
the anchor weight lambda sets that trade.

(Using the same term as a training loss is a negative result, recorded
in the README: the stiff second-derivative objective conflicts with the
data fit and degrades both metrics.)

Run time: ~3 minutes (9 pairs of 3D solves + training + refinement).
"""

import json
import pathlib

import numpy
import torch
from matplotlib import pyplot

import KratosMultiphysics as Kratos
from KratosMultiphysics.PhysicsNeMoApplication import grid_bridge
from KratosMultiphysics.PhysicsNeMoApplication import physics_informed

import thermal_cube

OUTPUT = pathlib.Path("output")
DATA = pathlib.Path("..") / "data"

TRAIN_CONDUCTIVITIES = numpy.linspace(0.5, 2.0, 8)
TEST_CONDUCTIVITY = 1.1
HEAT_FLUX = 1.0
COARSE_DIVISIONS, FINE_DIVISIONS = 8, 16
COARSE_GRID, FINE_GRID = (8, 8, 8), (16, 16, 16)
FD_DX = 1.0 / 15.0            # fine-grid spacing (16 points spanning [0, 1])
EPOCHS = 600
REFINE_STEPS = 300
REFINE_ANCHOR = 1e-2          # lambda of the proximity term


class Upsampler3D(torch.nn.Module):
    """(1, 8, 8, 8) -> (1, 16, 16, 16): trilinear + a learned correction.

    Zero-initialized last layer: untrained, the model IS trilinear
    interpolation, so training can only improve on it (the plain SRResNet
    it replaces lost to trilinear in RMSE on this smooth field)."""

    def __init__(self, channels: int = 1, width: int = 24):
        super().__init__()
        self.body = torch.nn.Sequential(
            torch.nn.Conv3d(channels, width, 3, padding=1), torch.nn.GELU(),
            torch.nn.Conv3d(width, width, 3, padding=1), torch.nn.GELU(),
            torch.nn.Conv3d(width, channels, 3, padding=1))
        torch.nn.init.zeros_(self.body[-1].weight)
        torch.nn.init.zeros_(self.body[-1].bias)

    def forward(self, grid):
        baseline = torch.nn.functional.interpolate(
            grid, size=(16, 16, 16), mode="trilinear", align_corners=True)
        return baseline + self.body(baseline)


def SolveOnGrid(conductivity, divisions, grid_shape):
    model, model_part = thermal_cube.Solve(conductivity, HEAT_FLUX, divisions)
    grid, _ = grid_bridge.SampleFieldsOnGrid(
        model_part, [("TEMPERATURE", "node_historical")], grid_shape)
    return grid.astype(numpy.float32)


def ResidualTerm(conductivity):
    """-k lap(u) - f as a differentiable FD loss on 16^3 grid fields.

    boundary_trim=1 drops the one grid shell where the upstream stencils
    are wrong for non-periodic fields; without it the metric is dominated
    by a boundary artifact and grades nothing useful.
    """
    return physics_informed.MakePhysicsLossTerm(Kratos.Parameters("""{
        "pde"           : "builtin:diffusion",
        "pde_arguments" : { "D" : %.10f, "source" : %.10f },
        "grad_method"   : "finite_difference",
        "fd_dx"         : %.10f,
        "grid_shape"    : [16, 16, 16],
        "boundary_trim" : 1
    }""" % (conductivity, HEAT_FLUX, FD_DX)))


def ResidualNorm(grid, conductivity):
    term = ResidualTerm(conductivity)
    with torch.no_grad():
        value = term(None, None,
                     torch.as_tensor(grid, dtype=torch.float32).reshape(-1, 1))
    return float(value)


def Refine(field, conductivity):
    """Minimizes residual^2 + lambda ||v - field||^2 over the field itself."""
    term = ResidualTerm(conductivity)
    anchor = torch.as_tensor(field, dtype=torch.float32)
    refined = anchor.clone().requires_grad_(True)
    optimizer = torch.optim.Adam([refined], lr=2e-3)
    for _ in range(REFINE_STEPS):
        optimizer.zero_grad()
        loss = (term(None, None, refined.reshape(-1, 1))
                + REFINE_ANCHOR * torch.nn.functional.mse_loss(refined, anchor))
        loss.backward()
        optimizer.step()
    return refined.detach().numpy()


def main():
    OUTPUT.mkdir(exist_ok=True)
    DATA.mkdir(exist_ok=True)
    Kratos.Logger.GetDefaultOutput().SetSeverity(Kratos.Logger.Severity.WARNING)

    # ---- data -------------------------------------------------------------
    coarse, fine = [], []
    for conductivity in TRAIN_CONDUCTIVITIES:
        coarse.append(SolveOnGrid(conductivity, COARSE_DIVISIONS, COARSE_GRID))
        fine.append(SolveOnGrid(conductivity, FINE_DIVISIONS, FINE_GRID))
        print(f"  k = {conductivity:.2f}: coarse and fine cubes solved")
    inputs = torch.from_numpy(numpy.stack(coarse))
    targets = torch.from_numpy(numpy.stack(fine))

    # ---- train the upsampler on pixels ------------------------------------
    torch.manual_seed(0)
    upsampler = Upsampler3D()
    optimizer = torch.optim.Adam(upsampler.parameters(), lr=2e-3)
    history = []
    for epoch in range(EPOCHS):
        optimizer.zero_grad()
        loss = torch.nn.functional.mse_loss(upsampler(inputs), targets)
        loss.backward()
        optimizer.step()
        history.append(float(loss))
    print(f"final training loss: {history[-1]:.3e}")

    # ---- unseen case: SR, then physics refinement -------------------------
    test_coarse = torch.from_numpy(
        SolveOnGrid(TEST_CONDUCTIVITY, COARSE_DIVISIONS, COARSE_GRID))[None]
    test_fine = SolveOnGrid(TEST_CONDUCTIVITY, FINE_DIVISIONS, FINE_GRID)[0]
    with torch.no_grad():
        sr_field = upsampler(test_coarse).numpy()[0, 0]
    refined_field = Refine(sr_field, TEST_CONDUCTIVITY)
    trilinear = torch.nn.functional.interpolate(
        test_coarse, size=FINE_GRID, mode="trilinear",
        align_corners=True).numpy()[0, 0]

    def Rmse(field):
        return float(numpy.sqrt(numpy.mean((field - test_fine) ** 2)))

    rows = {
        "trilinear": {"rmse": Rmse(trilinear),
                      "residual": ResidualNorm(trilinear, TEST_CONDUCTIVITY)},
        "upsampler": {"rmse": Rmse(sr_field),
                     "residual": ResidualNorm(sr_field, TEST_CONDUCTIVITY)},
        "upsampler_refined": {"rmse": Rmse(refined_field),
                             "residual": ResidualNorm(refined_field, TEST_CONDUCTIVITY)},
        "fine_solve": {"rmse": 0.0,
                       "residual": ResidualNorm(test_fine, TEST_CONDUCTIVITY)},
    }
    for name, entry in rows.items():
        print(f"  {name:17s}: rmse {entry['rmse']:.2e}   PDE residual {entry['residual']:.3e}")

    # ---- figures ----------------------------------------------------------
    mid = FINE_GRID[2] // 2
    panels = [(trilinear[:, :, mid], "trilinear upsample"),
              (sr_field[:, :, mid], "learned upsampler"),
              (refined_field[:, :, mid], "upsampler + PDE refinement"),
              (test_fine[:, :, mid], "fine solve (truth)")]
    limits = dict(vmin=0.0, vmax=float(test_fine.max()))
    figure, axes = pyplot.subplots(1, 4, figsize=(15.4, 3.6))
    for axis, (plane, title) in zip(axes, panels):
        image = axis.imshow(plane.T, origin="lower", cmap="viridis", **limits)
        axis.set_title(title, fontsize=10)
        axis.set_xticks([]), axis.set_yticks([])
        figure.colorbar(image, ax=axis, shrink=0.82)
    figure.suptitle(f"Mid-plane slices, unseen k = {TEST_CONDUCTIVITY}")
    figure.tight_layout()
    figure.savefig(DATA / "pisr_slices.png", dpi=130)

    labels = ["trilinear", "upsampler", "+ refinement", "fine solve"]
    colors = ["#7f8c8d", "#e67e22", "#2980b9", "#27ae60"]
    figure, axes = pyplot.subplots(1, 2, figsize=(10.6, 3.9))
    axes[0].bar(labels[:3], [rows["trilinear"]["rmse"], rows["upsampler"]["rmse"],
                             rows["upsampler_refined"]["rmse"]], color=colors[:3])
    axes[0].set_ylabel("RMSE vs fine solve")
    axes[0].set_title("Field error, unseen k")
    axes[1].bar(labels, [rows[k]["residual"] for k in
                         ("trilinear", "upsampler", "upsampler_refined", "fine_solve")],
                color=colors)
    axes[1].set_yscale("log")
    axes[1].set_ylabel("mean squared PDE residual (interior)")
    axes[1].set_title("Does the output satisfy the PDE?")
    for axis in axes:
        axis.grid(True, axis="y", alpha=0.3)
    figure.tight_layout()
    figure.savefig(DATA / "pisr_metrics.png", dpi=130)

    with open(OUTPUT / "pisr_summary.json", "w") as handle:
        json.dump(rows | {"refine_steps": REFINE_STEPS,
                          "refine_anchor": REFINE_ANCHOR}, handle, indent=1)
    print(f"figures: {DATA / 'pisr_slices.png'}, {DATA / 'pisr_metrics.png'}")


if __name__ == "__main__":
    main()
