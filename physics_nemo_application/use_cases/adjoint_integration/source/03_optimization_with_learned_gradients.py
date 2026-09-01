"""Stage 3 - the consequence: an optimization driven by each gradient.

Stage 2 measured gradient accuracy. This stage spends it. The same
least-squares design problem is driven three ways to a target objective:

    exact         solve + adjoint at every iteration (the reference)
    + dJ/dtheta   the Sobolev-trained surrogate: NO solves at all
    values only   the same surrogate trained without gradient supervision

A descent reads only the gradient, so this is where a wrong one shows. The
true objective is re-solved at each iterate for REPORTING ONLY - none of the
surrogate-driven runs uses it.

Run time: under a minute (the exact run solves twice per iteration; the two
surrogate runs solve only for the reported curve).
"""

import json
import pathlib

import numpy
import torch
from matplotlib import pyplot

from KratosMultiphysics.PhysicsNeMoApplication.training import sobolev_training

from adjoint_common import (MakeModel, ReferenceCoordinates, Sample, SolveThermal,
                            TotalTemperature)

OUTPUT = pathlib.Path("output")
DATA = pathlib.Path("..") / "data"

ITERATIONS = 25
LEARNING_RATE = 0.35
TARGET_FACTOR = 0.85


def SurrogateValueAndGradient(model, theta):
    inputs = torch.tensor(theta, dtype=torch.float64).reshape(1, 2)
    with torch.no_grad():
        value = float(model(inputs))
    gradient = sobolev_training.SensitivityGradient(
        model, inputs, coordinate_channels=2).detach().numpy().reshape(2)
    return value, gradient


def Descend(gradient_source, reference, target):
    """Least-squares descent on (J - target)^2, reporting the TRUE J."""
    theta = numpy.zeros(2)
    trajectory, true_values = [theta.copy()], []
    for _ in range(ITERATIONS):
        value, gradient = gradient_source(theta)
        true_values.append(TotalTemperature(SolveThermal(theta, reference)[1]))
        theta = theta - LEARNING_RATE * 2.0 * (value - target) * gradient
        trajectory.append(theta.copy())
    true_values.append(TotalTemperature(SolveThermal(theta, reference)[1]))
    return numpy.array(trajectory), numpy.array(true_values)


def main():
    OUTPUT.mkdir(exist_ok=True)

    _, base_part = SolveThermal()
    reference = ReferenceCoordinates(base_part)
    initial = TotalTemperature(base_part)
    target = TARGET_FACTOR * initial
    print(f"J(0) = {initial:.6f}, target = {target:.6f}")

    plain_model, sobolev_model = MakeModel(), MakeModel()
    plain_model.load_state_dict(torch.load(OUTPUT / "plain_model.pt"))
    sobolev_model.load_state_dict(torch.load(OUTPUT / "sobolev_model.pt"))
    plain_model.eval()
    sobolev_model.eval()

    runs = {
        "exact": Descend(lambda theta: Sample(theta, reference), reference, target),
        "+ dJ/dtheta": Descend(
            lambda theta: SurrogateValueAndGradient(sobolev_model, theta),
            reference, target),
        "values only": Descend(
            lambda theta: SurrogateValueAndGradient(plain_model, theta),
            reference, target),
    }

    print(f"{'':14} {'final true J':>13} {'|J - target|':>13} {'solves used':>12}")
    errors = {}
    for name, (_, values) in runs.items():
        errors[name] = abs(values[-1] - target)
        solves = "2 per step" if name == "exact" else "none"
        print(f"{name:14} {values[-1]:13.6f} {errors[name]:13.2e} {solves:>12}")

    # the point: a surrogate that learned the gradient lands where the exact
    # run lands, without solving anything
    assert errors["+ dJ/dtheta"] < 0.25 * errors["values only"], (
        "gradient supervision did not carry through to the optimization: "
        f"{errors['+ dJ/dtheta']:.2e} vs {errors['values only']:.2e}")

    figure, (left, right) = pyplot.subplots(1, 2, figsize=(9.6, 3.9))
    styles = {"exact": dict(color="0.2", linewidth=1.8),
              "+ dJ/dtheta": dict(color="tab:blue", linewidth=1.4),
              "values only": dict(color="tab:red", linewidth=1.4, linestyle="--")}
    for name, (trajectory, values) in runs.items():
        left.plot(values, label=name, **styles[name])
        right.plot(trajectory[:, 0], trajectory[:, 1], marker="o", markersize=3,
                   label=name, **styles[name])
    left.axhline(target, color="crimson", linestyle=":", linewidth=1, label="target")
    left.set_xlabel("iteration")
    left.set_ylabel("true J (re-solved)")
    left.set_title("descent", fontsize=10)
    left.grid(True, alpha=0.3)
    left.legend(fontsize=8)

    right.set_xlabel(r"$\theta_0$ (stretch in $x$)")
    right.set_ylabel(r"$\theta_1$ (stretch in $y$)")
    right.set_title("design path", fontsize=10)
    right.grid(True, alpha=0.3)
    right.legend(fontsize=8)
    figure.suptitle("A descent reads only the gradient")
    figure.tight_layout()
    figure.savefig(DATA / "learned_gradient_descent.png", dpi=130)

    with open(OUTPUT / "descent.json", "w") as handle:
        json.dump({"initial": initial, "target": target,
                   "final": {name: float(values[-1]) for name, (_, values) in runs.items()},
                   "error": {name: float(value) for name, value in errors.items()}},
                  handle, indent=1)
    print(f"figure: {DATA / 'learned_gradient_descent.png'}")


if __name__ == "__main__":
    main()
