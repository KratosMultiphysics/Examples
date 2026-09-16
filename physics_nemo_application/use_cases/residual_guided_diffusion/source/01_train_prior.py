"""A weak diffusion prior over a family of thermal fields.

This is the first half of a case about steering a generator at SAMPLING
time. A conditional diffusion model is trained on solved temperature
fields, conditioned on the HEAT-SOURCE field: it is told where the heat
goes in, but not how well the plate conducts it. The shape of the answer
is therefore determined and its MAGNITUDE is not - a real, stateable gap
for guidance to fill. Script 02 then steers that same trained checkpoint
two ways, with no retraining:

* toward sparse sensor readings (`"data_consistency"`), and
* toward the exact discrete FEM residual of the case
  (`"model_consistency"` with `MakeKratosResidualObservationOperator`),
  which is the solver's own physics grading the generator.

The de-normalization lesson applies in the TRAINING direction here, and it
is not optional. EDM's loss and sampler assume the data's standard
deviation is `sigma_data` (0.5). These thermal fields have a standard
deviation three orders of magnitude smaller; fed raw, the sampler's own
noise drowns them and every sample is noise. The fields are therefore
scaled to the EDM contract before training, and the SAME factor travels in
the model card's "output_normalization" so that everything reported - and
everything the residual operator sees - is back in physical units.

Run from this directory:  python3 01_train_prior.py
Outputs: ../data/dps_training.png, output/thermal_prior.mdlus
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
import thermal_plate  # noqa: E402

from KratosMultiphysics.PhysicsNeMoApplication.bridges import grid_bridge  # noqa: E402
from KratosMultiphysics.PhysicsNeMoApplication.deployment import model_registry  # noqa: E402
from KratosMultiphysics.PhysicsNeMoApplication.training import diffusion_utils  # noqa: E402
from KratosMultiphysics.PhysicsNeMoApplication.training import training_utils  # noqa: E402

HERE = pathlib.Path(__file__).parent
DATA = HERE.parent / "data"
OUTPUT = HERE / "output"

GRID_SHAPE = (16, 16, 2)        # planar case: the thin axis is squeezed away
SQUEEZE_AXIS = 2
BOUNDING_BOX = (numpy.zeros(3), numpy.array([1.0, 1.0, 0.0]))
DIVISIONS = 16
TRAIN_CASES, TEST_CASES = 64, 4
SIGMA_DATA = 0.5


def SampleGrid(model_part, variable):
    """One (16, 16) plane of a solved case, thin axis squeezed."""
    grid, _ = grid_bridge.SampleFieldsOnGrid(
        model_part, [(variable, "node_historical")], GRID_SHAPE, BOUNDING_BOX)
    return grid.mean(axis=SQUEEZE_AXIS + 1)[0]      # (C, H, W, D) -> (H, W)


def BuildDataset():
    """Solve the family; condition on the heat source, target the temperature.

    The condition is the source field rather than the conductivity for a
    measured reason: `thermal_plate` gives each case ONE scalar
    conductivity, so its sampled plane is flat to machine epsilon (spread
    4.4e-16) and carries a single number. Conditioning on that is barely
    conditioning at all, and it would make the guided-versus-unguided
    comparison in script 02 look good for the wrong reason. The heat-source
    plane genuinely varies - [0, 1.3] within a case, and up to 1.29 between
    cases - so the prior is given real information and still lacks the
    conductivity that sets the field's scale.
    """
    cases = thermal_plate.SampleCases(TRAIN_CASES + TEST_CASES, seed=7)
    kept, conditions, targets = [], [], []
    for index, case in enumerate(cases):
        model, model_part = thermal_plate.Solve(divisions=DIVISIONS, **case)
        kept.append(model)
        conditions.append(SampleGrid(model_part, "HEAT_FLUX")[None])
        targets.append(SampleGrid(model_part, "TEMPERATURE")[None])
        if (index + 1) % 20 == 0:
            print(f"[data] solved {index + 1}/{len(cases)} thermal cases")
    conditions = numpy.stack(conditions).astype(numpy.float32)
    targets = numpy.stack(targets).astype(numpy.float32)

    # EDM assumes std == sigma_data; a field three orders of magnitude
    # smaller is drowned by the sampler's own noise
    scale = SIGMA_DATA / float(targets[:TRAIN_CASES].std())
    print(f"[data] temperature std {targets[:TRAIN_CASES].std():.3e}; scaling by "
          f"{scale:.1f} to meet sigma_data = {SIGMA_DATA}")
    return (conditions[:TRAIN_CASES], targets[:TRAIN_CASES] * scale,
            conditions[TRAIN_CASES:], targets[TRAIN_CASES:], scale, kept)


def MakeDenoiser():
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        from physicsnemo.diffusion.preconditioners import EDMPrecondSuperResolution

    torch.manual_seed(0)
    # note: attn_resolutions is NOT a parameter of EDMPrecondSuperResolution -
    # passing it lands in **model_kwargs and is silently ignored rather than
    # rejected, so it is left out here instead of reading as if it did something
    return EDMPrecondSuperResolution(
        img_resolution=GRID_SHAPE[0], img_in_channels=1, img_out_channels=1,
        model_type="SongUNet", model_channels=16, channel_mult=[1, 2],
        num_blocks=1)


def Train(model, conditions, targets):
    dataset = torch.utils.data.TensorDataset(
        torch.tensor(conditions), torch.tensor(targets))
    return diffusion_utils.TrainDiffusionModel(model, dataset, Kratos.Parameters("""{
        "epochs"        : 400,
        "batch_size"    : 16,
        "learning_rate" : 2e-4,
        "device"        : "auto",
        "seed"          : 0,
        "echo_interval" : 100
    }"""))


def Render(history, conditions, targets, scale):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure, axes = plt.subplots(1, 3, figsize=(11.4, 3.4), constrained_layout=True)
    axes[0].semilogy(history)
    axes[0].set_xlabel("epoch"), axes[0].set_ylabel("EDM loss")
    axes[0].set_title("training the prior", fontsize=9), axes[0].grid(alpha=0.3)

    image = axes[1].imshow(conditions[0][0].T, origin="lower", cmap="viridis")
    figure.colorbar(image, ax=axes[1], shrink=0.8)
    axes[1].set_title("condition: heat source (the prior is told where,\n"
                      "not how well the plate conducts)", fontsize=8)
    axes[1].set_xticks([]), axes[1].set_yticks([])

    image = axes[2].imshow((targets[0][0] / scale).T, origin="lower", cmap="inferno")
    figure.colorbar(image, ax=axes[2], shrink=0.8)
    axes[2].set_title("target: temperature (physical units)", fontsize=9)
    axes[2].set_xticks([]), axes[2].set_yticks([])

    figure.suptitle("An informative but incomplete prior: the source is given, "
                    "the conductivity is not")
    figure.savefig(DATA / "dps_training.png", dpi=130)


if __name__ == "__main__":
    DATA.mkdir(exist_ok=True)
    OUTPUT.mkdir(exist_ok=True)
    Kratos.Logger.GetDefaultOutput().SetSeverity(Kratos.Logger.Severity.WARNING)

    conditions, targets, test_conditions, test_targets, scale, _kept = BuildDataset()
    model = MakeDenoiser()
    history = Train(model, conditions, targets)

    # the card carries the scaling back out, so the residual operator in
    # script 02 sees physical values rather than EDM-scaled ones
    checkpoint = OUTPUT / "thermal_prior.mdlus"
    training_utils.SaveTrainedModel(model, checkpoint, card={
        "input_fields":  [{"variable_name": "HEAT_FLUX",
                           "data_location": "node_historical"}],
        "output_fields": [{"variable_name": "TEMPERATURE",
                           "data_location": "node_historical"}],
        "output_normalization": model_registry.MakeMeanStdNormalization(
            [0.0], [1.0 / scale])})
    print(f"[train] loss {history[0]:.4f} -> {history[-1]:.4f}; checkpoint at "
          f"{checkpoint.name} carrying the 1/{scale:.1f} de-normalization")

    Render(history, conditions, targets, scale)
    with open(OUTPUT / "prior_summary.json", "w") as handle:
        json.dump({"scale": scale, "first_loss": history[0],
                   "last_loss": history[-1], "train_cases": TRAIN_CASES}, handle, indent=1)

    # EDM training is sigma-stochastic, so the honest claim is that the loss
    # came down at all - not that the last epoch is the lowest
    assert numpy.isfinite(history).all(), "the EDM loss went non-finite"
    assert min(history[1:]) < history[0], (history[0], min(history[1:]))
    print("[done] figure at data/dps_training.png")
