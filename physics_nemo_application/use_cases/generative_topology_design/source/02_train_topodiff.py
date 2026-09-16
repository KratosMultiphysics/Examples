"""TopoDiff trained on the optima Kratos computed in script 01.

The model is conditional. It receives three channels describing the
problem - where the structure is held, where it is loaded, and how much
material it may use - and learns the distribution of good designs given
those. That is why `in_channels` is 4 and `out_channels` is 1: three
conditioning channels concatenated with the one density channel being
denoised.

`model_channels` cannot be dropped to 32 to save time. TopoDiff derives
its attention head count from the channel width, and 32 produces
`num_heads = 0` and a division error rather than a small model. Sixty-four
is the floor that works.

The checkpoint is saved as the RAW `TopoDiff`, not the wrapper. That is a
measured choice: `LoadModel` returns a `TopoDiff`, which script 03 then
passes through `WrapDiffusionModel` again. A seeded ensemble drawn before
saving and after reloading agrees to 9.3e-10, which is float32
serialization noise and not a functional difference - but the wrapper does
have to be reapplied, because what comes back is the bare model.

Run from this directory:  python3 02_train_topodiff.py
Outputs: ../data/topodiff_training.png, output/topodiff_design.mdlus
"""

import json
import pathlib
import sys
import warnings

import numpy
import torch

import KratosMultiphysics as Kratos
import KratosMultiphysics.PhysicsNeMoApplication  # registers the application  # noqa: F401

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import compliance_case  # noqa: E402

from KratosMultiphysics.PhysicsNeMoApplication.training import diffusion_utils  # noqa: E402
from KratosMultiphysics.PhysicsNeMoApplication.training import training_utils  # noqa: E402

HERE = pathlib.Path(__file__).parent
DATA = HERE.parent / "data"
OUTPUT = HERE / "output"

DIVISIONS = 16
EPOCHS = 300
BATCH_SIZE = 8
LEARNING_RATE = 1e-4


def LoadTrainingSet():
    archive = OUTPUT / "training_designs.npz"
    if not archive.is_file():
        raise SystemExit("run 01_optimize_training_designs.py first (it writes the designs)")
    stored = numpy.load(archive)
    conditions = stored["conditions"].astype(numpy.float32)   # (N, 3, 16, 16)
    targets = stored["designs"][:, None].astype(numpy.float32)  # (N, 1, 16, 16)
    print(f"[data] {len(targets)} designs, conditions {conditions.shape[1:]}, "
          f"densities in [{targets.min():.2f}, {targets.max():.2f}]")
    return conditions, targets


def MakeModel():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        from physicsnemo.models.topodiff import TopoDiff

    torch.manual_seed(0)
    model = TopoDiff(img_resolution=DIVISIONS, in_channels=4, out_channels=1,
                     model_channels=64, channel_mult=[1, 1], num_blocks=1,
                     attn_resolutions=[])
    return model, diffusion_utils.WrapDiffusionModel(model, "topodiff", out_channels=1)


def Render(history, conditions, targets):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure = plt.figure(figsize=(12.6, 4.0), constrained_layout=True)
    grid = figure.add_gridspec(1, 5)

    axis = figure.add_subplot(grid[0, 0:2])
    axis.semilogy(history)
    axis.set_xlabel("epoch"), axis.set_ylabel("diffusion loss")
    axis.set_title(f"TopoDiff on {len(targets)} Kratos optima", fontsize=9)
    axis.grid(alpha=0.3)

    # one training pair, shown as what the model actually receives
    panels = (("condition 0\nsupports", conditions[0][0]),
              ("condition 1\nload", conditions[0][1]),
              ("target\ndensity", targets[0][0]))
    for offset, (name, values) in enumerate(panels):
        axis = figure.add_subplot(grid[0, 2 + offset])
        axis.imshow(values.T, origin="lower",
                    cmap="gray_r" if "density" in name else "magma")
        axis.set_title(name, fontsize=8)
        axis.set_xticks([]), axis.set_yticks([])

    figure.suptitle("Learning the distribution of good designs, given the problem")
    figure.savefig(DATA / "topodiff_training.png", dpi=130)


if __name__ == "__main__":
    DATA.mkdir(exist_ok=True)
    OUTPUT.mkdir(exist_ok=True)
    Kratos.Logger.GetDefaultOutput().SetSeverity(Kratos.Logger.Severity.WARNING)

    conditions, targets = LoadTrainingSet()
    dataset = torch.utils.data.TensorDataset(
        torch.tensor(conditions), torch.tensor(targets))

    model, wrapped = MakeModel()
    parameters = sum(p.numel() for p in model.parameters())
    print(f"[train] TopoDiff with {parameters / 1e6:.2f}M parameters")

    history = diffusion_utils.TrainDiffusionModel(wrapped, dataset, Kratos.Parameters("""{
        "epochs"             : %d,
        "batch_size"         : %d,
        "learning_rate"      : %g,
        "device"             : "auto",
        "seed"               : 0,
        "denoiser_interface" : "protocol",
        "echo_interval"      : 50
    }""" % (EPOCHS, BATCH_SIZE, LEARNING_RATE)))

    checkpoint = OUTPUT / "topodiff_design.mdlus"
    training_utils.SaveTrainedModel(model, checkpoint)
    print(f"[train] loss {history[0]:.4f} -> {history[-1]:.4f}; checkpoint at "
          f"{checkpoint.name}")

    Render(history, conditions, targets)
    with open(OUTPUT / "topodiff_summary.json", "w") as handle:
        json.dump({"first_loss": history[0], "last_loss": history[-1],
                   "best_loss": float(min(history)), "epochs": EPOCHS,
                   "designs": int(len(targets)), "parameters": int(parameters)},
                  handle, indent=1)

    # Diffusion training is noise-stochastic: which sigma each batch draws
    # changes the loss between epochs regardless of the model. So the
    # honest claim is that the loss came down at all, not that the last
    # epoch is the lowest one.
    assert numpy.isfinite(history).all(), "the diffusion loss went non-finite"
    assert min(history[1:]) < history[0], (history[0], min(history[1:]))
    print("[done] figure at data/topodiff_training.png")
