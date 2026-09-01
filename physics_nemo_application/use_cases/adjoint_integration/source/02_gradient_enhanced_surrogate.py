"""Stage 2 - a surrogate trained on the adjoint's gradients, not only its values.

A surrogate fitted on values alone is graded on values alone, and its
derivatives are whatever the fit left behind. That matters the moment the
surrogate is used for anything gradient-driven, because those workflows read
dJ/dtheta - a quantity the training objective never looked at.

The design family is the unit square deformed by an FFD lattice with two
parameters (stretch in x, stretch in y); the objective is the total nodal
temperature of the stationary heat solve. Each sample therefore costs one
solve plus one element-local adjoint pass, and carries

    theta (2)  ->  [ J, dJ/dtheta_0, dJ/dtheta_1 ]  (3)

Two runs follow: same architecture, same seed, same sixteen designs, the
only difference being one extra loss term. Two settings carry the mechanism:

    "target_channels" : [0]    keeps the DATA loss on the column the model
                               predicts. Without it torch does not reject a
                               1-channel prediction against a 3-column
                               target - it BROADCASTS, and silently trains
                               against the mean of J and its derivatives.
    MakeSensitivityLossTerm    declares a fourth argument, so TrainModel
                               hands it the batch targets. Three-argument
                               terms are called exactly as before; the arity
                               is resolved once, before training starts.

Run time: about a minute (40 small solves plus two short trainings on CPU).
"""

import json
import pathlib

import numpy
import torch
from matplotlib import pyplot

import KratosMultiphysics as Kratos
from KratosMultiphysics.PhysicsNeMoApplication.training import sobolev_training
from KratosMultiphysics.PhysicsNeMoApplication.training import training_utils

from adjoint_common import (BuildDataset, MakeModel, ReferenceCoordinates, Sample,
                            SolveThermal, TotalTemperature)

OUTPUT = pathlib.Path("output")
DATA = pathlib.Path("..") / "data"

DESIGN_RANGE = 0.15
N_TRAIN, N_TEST = 16, 24

TRAINING = """{
    "epochs"          : 600,
    "batch_size"      : 8,
    "learning_rate"   : 0.01,
    "device"          : "cpu",
    "seed"            : 0,
    "target_channels" : [0]
}"""

SENSITIVITY_TERM = """{
    "coordinate_channels" : 2,
    "gradient_columns"    : [1, 2],
    "reduction"           : "relative",
    "weight"              : 1.0
}"""


def Train(train_inputs, train_targets, extra_loss_terms):
    model = MakeModel()
    dataset = torch.utils.data.TensorDataset(train_inputs, train_targets)
    history = training_utils.TrainModel(
        model, dataset, Kratos.Parameters(TRAINING), extra_loss_terms=extra_loss_terms)
    return model, history


def Errors(model, test_inputs, test_targets):
    """RMSE of J and of dJ/dtheta, at designs never trained on."""
    with torch.no_grad():
        value = float((model(test_inputs) - test_targets[:, :1]).square().mean().sqrt())
    gradient = sobolev_training.SensitivityGradient(
        model, test_inputs, coordinate_channels=2)
    return value, float((gradient - test_targets[:, 1:]).square().mean().sqrt())


def main():
    OUTPUT.mkdir(exist_ok=True)

    _, base_part = SolveThermal()
    reference = ReferenceCoordinates(base_part)
    print(f"{base_part.NumberOfNodes()} nodes, {base_part.NumberOfElements()} elements, "
          f"J(0) = {TotalTemperature(base_part):.6f}")

    # the adjoint gradient is exact, not merely plausible: two more full
    # solves say so
    probe = numpy.array([0.10, -0.05])
    _, adjoint_gradient = Sample(probe, reference)
    step = 1e-5
    finite_difference = []
    for k in range(2):
        plus, minus = probe.copy(), probe.copy()
        plus[k] += step
        minus[k] -= step
        finite_difference.append(
            (TotalTemperature(SolveThermal(plus, reference)[1])
             - TotalTemperature(SolveThermal(minus, reference)[1])) / (2.0 * step))
    finite_difference = numpy.array(finite_difference)
    relative = numpy.abs((adjoint_gradient - finite_difference) / finite_difference)
    print(f"adjoint dJ/dtheta {adjoint_gradient}  vs re-solve FD {finite_difference}"
          f"  (relative {relative.max():.1e})")
    assert relative.max() < 1e-6

    generator = numpy.random.default_rng(0)
    train_thetas = generator.uniform(-DESIGN_RANGE, DESIGN_RANGE, size=(N_TRAIN, 2))
    test_thetas = generator.uniform(-DESIGN_RANGE, DESIGN_RANGE, size=(N_TEST, 2))
    train_inputs, train_targets = BuildDataset(train_thetas, reference)
    test_inputs, test_targets = BuildDataset(test_thetas, reference)

    plain_model, plain_history = Train(train_inputs, train_targets, None)
    term = sobolev_training.MakeSensitivityLossTerm(Kratos.Parameters(SENSITIVITY_TERM))
    sobolev_model, sobolev_history = Train(train_inputs, train_targets, [term])

    plain_value, plain_gradient = Errors(plain_model, test_inputs, test_targets)
    sobolev_value, sobolev_gradient = Errors(sobolev_model, test_inputs, test_targets)
    ratio = plain_gradient / sobolev_gradient

    print(f"{'':12} {'value RMSE':>12} {'gradient RMSE':>15}")
    print(f"{'values only':12} {plain_value:12.5f} {plain_gradient:15.5f}")
    print(f"{'+ dJ/dtheta':12} {sobolev_value:12.5f} {sobolev_gradient:15.5f}")
    print(f"gradient error improved {ratio:.1f}x")
    assert plain_value < 0.05 and sobolev_value < 0.05, "both must be real fits"
    assert sobolev_gradient < 0.5 * plain_gradient

    torch.save(plain_model.state_dict(), OUTPUT / "plain_model.pt")
    torch.save(sobolev_model.state_dict(), OUTPUT / "sobolev_model.pt")
    numpy.save(OUTPUT / "reference_coordinates.npy", reference)

    plain_g = sobolev_training.SensitivityGradient(
        plain_model, test_inputs, coordinate_channels=2).detach().numpy()
    sobolev_g = sobolev_training.SensitivityGradient(
        sobolev_model, test_inputs, coordinate_channels=2).detach().numpy()
    exact_g = test_targets[:, 1:].numpy()

    figure, (left, right) = pyplot.subplots(1, 2, figsize=(9.6, 3.9))
    left.semilogy(plain_history, linewidth=1, label="values only")
    left.semilogy(sobolev_history, linewidth=1, label=r"+ $dJ/d\theta$")
    left.set_xlabel("epoch")
    left.set_ylabel("training loss")
    left.set_title("training", fontsize=10)
    left.grid(True, which="both", alpha=0.3)
    left.legend(fontsize=8)

    right.scatter(exact_g.ravel(), plain_g.ravel(), s=20, label="values only", zorder=3)
    right.scatter(exact_g.ravel(), sobolev_g.ravel(), s=26, marker="x",
                  label=r"+ $dJ/d\theta$", zorder=4)
    limits = [exact_g.min() * 0.9, exact_g.max() * 1.1]
    right.plot(limits, limits, "k--", linewidth=0.8, zorder=2)
    right.set_xlabel(r"exact $dJ/d\theta$ (Kratos adjoint)")
    right.set_ylabel(r"surrogate $dJ/d\theta$")
    right.set_title(f"held-out designs: {ratio:.1f}x better", fontsize=10)
    right.grid(True, alpha=0.3)
    right.legend(fontsize=8)
    figure.suptitle("Gradient supervision buys gradient accuracy")
    figure.tight_layout()
    figure.savefig(DATA / "gradient_enhanced_surrogate.png", dpi=130)

    with open(OUTPUT / "surrogate_errors.json", "w") as handle:
        json.dump({"plain_value": plain_value, "plain_gradient": plain_gradient,
                   "sobolev_value": sobolev_value, "sobolev_gradient": sobolev_gradient,
                   "ratio": float(ratio)}, handle, indent=1)
    print(f"figure: {DATA / 'gradient_enhanced_surrogate.png'}")


if __name__ == "__main__":
    main()
