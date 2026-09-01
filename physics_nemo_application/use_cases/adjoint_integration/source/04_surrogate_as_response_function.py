"""Stage 4 - the other direction: a surrogate WHERE a response function goes.

Stages 1-3 read Kratos's gradients. This one hands gradients back.
SurrogateResponseFunction implements the core ResponseFunctionInterface, with
the same CreateResponseFunction(response_id, response_settings, model)
signature the applications' own factories use, so a driver that resolves
responses by module path takes it with no special case - the mirror of
cosim_surrogate_solver_wrapper putting a model where a SOLVER goes.

The surrogate is a FIELD surrogate over the same FFD design family:

    (x, y, z, heat flux, theta_0, theta_1, 0)  ->  T

The design parameters ride in an ordinary nodal variable (VELOCITY, constant
over the mesh) because without them the map is genuinely ambiguous - the same
physical point belongs to differently-sized domains in different designs, and
a coordinates-only fit plateaus around 25 % relative error. With them it
reaches a few percent.

J is the total nodal temperature, and the two gradient modes are then
compared against the FEM adjoint around the TRUE solved state at a design
the surrogate never saw:

    "exact"        the FEM adjoint around the state the surrogate WROTE. The
                   surrogate replaces the SOLVE, not the sensitivity
                   analysis, so the gradient is discretely exact for the
                   state it is given - and only as trustworthy as that state.
    "surrogate"    autograd through the model's forward. One backward pass,
                   no assembly. For a POINTWISE model this is a pointwise
                   quantity and the FEM adjoint is not: dJ/dX_i couples
                   through the PDE, which a per-node map cannot represent.
                   The gap below is that structural limitation, measured
                   rather than asserted - not a bug in either mode.

Run time: about two minutes.
"""

import json
import pathlib

import numpy
import torch
from matplotlib import pyplot

import KratosMultiphysics as Kratos
from KratosMultiphysics.PhysicsNeMoApplication.deployment import surrogate_response_function
from KratosMultiphysics.PhysicsNeMoApplication.training import training_utils

from adjoint_common import (ControlFromTheta, Quiet, ReferenceCoordinates,
                            ShapeSensitivityField, SolveThermal, TotalTemperature)

OUTPUT = pathlib.Path("output")
DATA = pathlib.Path("..") / "data"

CHECKPOINT = OUTPUT / "field_surrogate.pt"
DESIGN_RANGE = 0.15
N_DESIGNS = 12
HELD_OUT = numpy.array([0.08, -0.06])

TRAINING = """{
    "epochs"        : 2500,
    "batch_size"    : 256,
    "learning_rate" : 0.01,
    "device"        : "cpu",
    "seed"          : 0
}"""

OBJECTIVE = """{ "type" : "weighted_sum", "variable_name" : "TEMPERATURE" }"""


class FieldSurrogate(torch.nn.Module):
    """(1, N, 7) -> (1, N, 1) temperature, in physical units.

    The point-cloud "generic" interface PREPENDS the coordinates to the
    features and adds a batch axis, so the input is [x, y, z] followed by
    the input_fields in order. The output scale is baked in rather than
    inverted afterwards: the response function writes what the model
    returns straight onto TEMPERATURE.
    """

    def __init__(self, scale):
        super().__init__()
        self.scale = scale
        self.net = torch.nn.Sequential(
            torch.nn.Linear(7, 64), torch.nn.Tanh(),
            torch.nn.Linear(64, 64), torch.nn.Tanh(),
            torch.nn.Linear(64, 1)).double()

    def forward(self, x):
        return self.net(x) * self.scale


def TagDesign(model_part, theta):
    """The design parameters as a constant nodal field the model can read."""
    for node in model_part.Nodes:
        node.SetSolutionStepValue(Kratos.VELOCITY,
                                  [float(theta[0]), float(theta[1]), 0.0])


def SolvedModelPart(theta, reference):
    """A solved case at one design, Dirichlet DOFs still fixed.

    The adjoint needs the CONSTRAINED operator. thermal_case fixes the
    boundary itself and no BC process releases it, so nothing extra is
    needed here - unlike a case driven by Kratos' standard BC processes,
    where analysis.Finalize() would leave a singular tangent and
    sensitivities wrong by orders of magnitude.
    """
    model, model_part = SolveThermal(theta, reference)
    TagDesign(model_part, theta)
    return model, model_part


def CollectFieldSamples(reference, thetas):
    rows, targets = [], []
    for theta in thetas:
        _, model_part = SolvedModelPart(theta, reference)
        for node in model_part.Nodes:
            rows.append([node.X, node.Y, node.Z,
                         node.GetSolutionStepValue(Kratos.HEAT_FLUX),
                         float(theta[0]), float(theta[1]), 0.0])
            targets.append([node.GetSolutionStepValue(Kratos.TEMPERATURE)])
    return (torch.tensor(rows, dtype=torch.float64),
            torch.tensor(targets, dtype=torch.float64))


def ResponseSettings(gradient_mode):
    settings = Kratos.Parameters("""{
        "model_part_name"       : "ThermalModelPart",
        "model_settings"        : { "checkpoint_file" : "", "device" : "cpu" },
        "input_fields"          : [
            { "variable_name" : "HEAT_FLUX",   "data_location" : "node_historical" },
            { "variable_name" : "VELOCITY",    "data_location" : "node_historical" } ],
        "output_fields"         : [
            { "variable_name" : "TEMPERATURE", "data_location" : "node_historical" } ],
        "dof_fields"            : [
            { "variable_name" : "TEMPERATURE", "data_location" : "node_historical" } ],
        "objective"             : { },
        "gradient_mode"         : "exact",
        "model_interface"       : "generic",
        "normalize_coordinates" : false
    }""")
    settings["model_settings"]["checkpoint_file"].SetString(str(CHECKPOINT))
    settings["objective"] = Kratos.Parameters(OBJECTIVE)
    settings["gradient_mode"].SetString(gradient_mode)
    return settings


def RunResponse(gradient_mode, theta, reference):
    model, model_part = SolvedModelPart(theta, reference)
    # wipe the solved field: the response must produce it, not inherit it
    for node in model_part.Nodes:
        if not node.IsFixed(Kratos.TEMPERATURE):
            node.SetSolutionStepValue(Kratos.TEMPERATURE, 0.0)

    response = surrogate_response_function.CreateResponseFunction(
        "total_temperature", ResponseSettings(gradient_mode), model)
    with Quiet():
        response.RunCalculation(calculate_gradient=True)
    gradient = response.GetNodalGradient(Kratos.SHAPE_SENSITIVITY)
    field = numpy.array([gradient[node.Id] for node in model_part.Nodes])
    return response.GetValue(), field


def RelativeError(candidate, reference):
    return float(numpy.linalg.norm(candidate - reference) / numpy.linalg.norm(reference))


def main():
    OUTPUT.mkdir(exist_ok=True)

    _, base_part = SolveThermal()
    reference = ReferenceCoordinates(base_part)

    generator = numpy.random.default_rng(3)
    thetas = generator.uniform(-DESIGN_RANGE, DESIGN_RANGE, size=(N_DESIGNS, 2))
    inputs, targets = CollectFieldSamples(reference, thetas)
    scale = float(targets.abs().max())
    print(f"field dataset: {tuple(inputs.shape)} -> {tuple(targets.shape)} "
          f"({N_DESIGNS} designs), max |T| = {scale:.4f}")

    model = FieldSurrogate(scale)
    # the model emits PHYSICAL units (the scale is baked into its forward),
    # so it is fitted against the physical targets; the internal factor only
    # conditions the last layer, whose own output stays O(1)
    history = training_utils.TrainModel(
        model, torch.utils.data.TensorDataset(inputs, targets),
        Kratos.Parameters(TRAINING))
    with torch.no_grad():
        field_error = float((model(inputs) - targets).norm() / targets.norm())
    print(f"training loss {history[0]:.3e} -> {history[-1]:.3e}, "
          f"relative field error on the training designs {field_error:.2%}")
    torch.jit.script(model).save(str(CHECKPOINT))

    # the reference: J and dJ/dX of the REAL solved state at a design the
    # surrogate never saw
    _, solved_part = SolvedModelPart(HELD_OUT, reference)
    true_value = TotalTemperature(solved_part)
    true_field = ShapeSensitivityField(solved_part)

    exact_value, exact_field = RunResponse("exact", HELD_OUT, reference)
    surrogate_value, surrogate_field = RunResponse("surrogate", HELD_OUT, reference)

    value_error = abs(exact_value - true_value) / abs(true_value)
    exact_error = RelativeError(exact_field, true_field)
    surrogate_error = RelativeError(surrogate_field, true_field)

    print(f"held-out design theta = {HELD_OUT}")
    print(f"{'':26} {'J':>10} {'rel. J err':>11} {'rel. dJ/dX err':>15}")
    print(f"{'solved state (reference)':26} {true_value:10.6f} {'-':>11} {'-':>15}")
    print(f"{'surrogate + FEM adjoint':26} {exact_value:10.6f} {value_error:11.2e} "
          f"{exact_error:15.2e}")
    print(f"{'surrogate autograd':26} {surrogate_value:10.6f} {value_error:11.2e} "
          f"{surrogate_error:15.2e}")

    assert value_error < 0.05, f"the field surrogate is not accurate enough: {value_error:.2e}"
    assert exact_error < 0.25, f"exact mode drifted too far: {exact_error:.2e}"
    # the pointwise autograd gradient is a DIFFERENT quantity - the honest
    # half of this comparison
    assert surrogate_error > exact_error

    figure, (left, right) = pyplot.subplots(1, 2, figsize=(9.6, 3.9))
    left.scatter(true_field.ravel(), exact_field.ravel(), s=16,
                 label='"exact": surrogate state + FEM adjoint', zorder=3)
    left.scatter(true_field.ravel(), surrogate_field.ravel(), s=16, marker="x",
                 label='"surrogate": autograd through the model', zorder=4)
    limits = [true_field.min() * 1.08, true_field.max() * 1.08]
    left.plot(limits, limits, "k--", linewidth=0.8, zorder=2)
    left.set_xlabel(r"FEM adjoint at the solved state, $dJ/dX$")
    left.set_ylabel(r"response function's $dJ/dX$")
    left.set_title("the two gradient modes", fontsize=10)
    left.grid(True, alpha=0.3)
    left.legend(fontsize=7)

    points = numpy.array([[node.X, node.Y] for node in solved_part.Nodes])
    magnitude = numpy.hypot(exact_field[:, 0], exact_field[:, 1])
    right.quiver(points[:, 0], points[:, 1], exact_field[:, 0], exact_field[:, 1],
                 magnitude, cmap="viridis", scale=4.0)
    right.set_aspect("equal")
    right.set_title(r'"exact" mode $dJ/dX$ - no solve performed', fontsize=10)
    figure.suptitle("A trained model serving as a Kratos response function")
    figure.tight_layout()
    figure.savefig(DATA / "surrogate_response_function.png", dpi=130)

    with open(OUTPUT / "response_function.json", "w") as handle:
        json.dump({"training_field_error": field_error,
                   "true_value": true_value, "response_value": exact_value,
                   "value_error": value_error, "exact_gradient_error": exact_error,
                   "surrogate_gradient_error": surrogate_error}, handle, indent=1)
    print(f"figure: {DATA / 'surrogate_response_function.png'}")


if __name__ == "__main__":
    main()
