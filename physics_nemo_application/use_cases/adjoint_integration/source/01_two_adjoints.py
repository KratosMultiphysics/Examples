"""Stage 1 - Kratos's adjoint stack, read as arrays, on two physics.

adjoint_bridge consumes a CONTRACT, not an application: ResponseFunctionInterface
lives in the Kratos core, so the bridge needs whichever application owns the
response and never a compiled optimization application. Two of them are
driven here, and they could hardly be less alike:

    StructuralMechanics   AdjointFiniteDifferencing* elements, a SEPARATE
                          Kratos.Model for the adjoint part, re-reading the
                          mdpa; response "adjoint_nodal_displacement"
    ConvectionDiffusion   AdjointDiffusionElement, primal and adjoint in the
                          same model; response "point_temperature"

Both are compared node by node against sensitivity_utils' own, independently
implemented adjoint. Two implementations agreeing across two physics is a
much stronger statement than either against finite differences.

One factor is deliberately pinned rather than absorbed: Kratos's
"point_temperature" response AVERAGES the temperature over the traced part
while MakeObjectiveWeights' "weighted_sum" sums it. Two correct adjoints of
two different objectives disagree for a reason that has nothing to do with
either being wrong, and that is exactly what an unexplained factor of three
looks like.

Run time: a few seconds (both meshes are tiny - 12 and 9 nodes).
"""

import json
import pathlib

import numpy
from matplotlib import pyplot

import KratosMultiphysics as Kratos
from KratosMultiphysics.PhysicsNeMoApplication.bridges import adjoint_bridge
from KratosMultiphysics.PhysicsNeMoApplication.physics import differentiable_residual
from KratosMultiphysics.PhysicsNeMoApplication.physics import sensitivity_utils

from adjoint_common import InCaseDirectory, Quiet

OUTPUT = pathlib.Path("output")
DATA = pathlib.Path("..") / "data"

TIP_NODE = 9

CANTILEVER_RESPONSE = Kratos.Parameters("""{
    "response_id"          : "tip_displacement",
    "response_application" : "structural_mechanics",
    "response_settings"    : {
        "response_type"                    : "adjoint_nodal_displacement",
        "gradient_mode"                    : "semi_analytic",
        "step_size"                        : 1e-7,
        "primal_settings"                  : "cantilever_primal.json",
        "adjoint_settings"                 : "auto",
        "primal_data_transfer_with_python" : true,
        "response_part_name"               : "Tip",
        "direction"                        : [0.0, 0.0, 1.0],
        "traced_dof"                       : "DISPLACEMENT",
        "sensitivity_settings"             : {
            "sensitivity_model_part_name"               : "Design",
            "nodal_solution_step_sensitivity_variables" : ["SHAPE_SENSITIVITY"],
            "build_mode"                                : "static"
        }
    }
}""")

CANTILEVER_OBJECTIVE = Kratos.Parameters("""{
    "type" : "traced_node", "variable_name" : "DISPLACEMENT",
    "node_id" : 9, "direction" : [0.0, 0.0, 1.0]
}""")

DIFFUSION_OBJECTIVE = Kratos.Parameters("""{
    "type" : "weighted_sum", "variable_name" : "TEMPERATURE",
    "model_part_name" : "HeatFlux2D_right"
}""")


def KratosCantileverAdjoint():
    model = Kratos.Model()
    response = adjoint_bridge.CreateResponseFunction(CANTILEVER_RESPONSE, model)
    # the primal part exists as soon as the response is constructed, and its
    # Nodes order is what defines the rows
    with Quiet():
        return adjoint_bridge.EvaluateResponse(response, model["Structure"])


def ShippedCantileverAdjoint():
    from KratosMultiphysics.StructuralMechanicsApplication.structural_mechanics_analysis import (
        StructuralMechanicsAnalysis)

    with open("cantilever_primal.json") as parameter_file:
        parameters = Kratos.Parameters(parameter_file.read())
    model = Kratos.Model()
    with Quiet():
        analysis = StructuralMechanicsAnalysis(model, parameters)
        analysis.Initialize()
        analysis.RunSolutionLoop()
    model_part = model["Structure"]

    # The boundary-condition process releases the DOFs it fixed in its
    # ExecuteFinalizeSolutionStep, and the adjoint needs the CONSTRAINED
    # operator. Skipping this gives finite sensitivities wrong by about six
    # orders of magnitude - the quietest trap in the whole workflow.
    for node in model_part.GetSubModelPart("Support").Nodes:
        for component in (Kratos.DISPLACEMENT_X, Kratos.DISPLACEMENT_Y,
                          Kratos.DISPLACEMENT_Z):
            node.Fix(component)

    return _ShippedField(model_part, CANTILEVER_OBJECTIVE, Kratos.DISPLACEMENT,
                         "DISPLACEMENT")


def KratosDiffusionAdjoint():
    import KratosMultiphysics.ConvectionDiffusionApplication  # noqa: F401

    with open("diffusion_response.json") as parameter_file:
        response_settings = Kratos.Parameters(parameter_file.read())["response_settings"]
    settings = Kratos.Parameters("""{
        "response_id" : "point_temperature", "response_application" : "convection_diffusion"
    }""")
    settings.AddValue("response_settings", response_settings)

    model = Kratos.Model()
    response = adjoint_bridge.CreateResponseFunction(settings, model)
    model_part = model["ThermalModelPart"]
    with Quiet():
        fields = adjoint_bridge.EvaluateResponse(response, model_part)
    return fields, model_part.GetSubModelPart("HeatFlux2D_right").NumberOfNodes()


def ShippedDiffusionAdjoint():
    import KratosMultiphysics.ConvectionDiffusionApplication  # noqa: F401
    from KratosMultiphysics.ConvectionDiffusionApplication.convection_diffusion_analysis import (
        ConvectionDiffusionAnalysis)

    with open("diffusion_primal.json") as parameter_file:
        parameters = Kratos.Parameters(parameter_file.read())
    model = Kratos.Model()
    with Quiet():
        analysis = ConvectionDiffusionAnalysis(model, parameters)
        analysis.Initialize()
        analysis.RunSolutionLoop()
    model_part = model["ThermalModelPart"]
    for node in model_part.GetSubModelPart("ImposedTemperature2D_left").Nodes:
        node.Fix(Kratos.TEMPERATURE)

    return _ShippedField(model_part, DIFFUSION_OBJECTIVE, Kratos.TEMPERATURE,
                         "TEMPERATURE")


def _ShippedField(model_part, objective, variable, dof_name):
    assembler = differentiable_residual.TangentAssembler(model_part)
    dof_map = differentiable_residual.DofFieldMap(
        assembler, [(dof_name, "node_historical")])
    weights = adjoint_bridge.MakeObjectiveWeights(objective, model_part)
    value = adjoint_bridge.EvaluateObjective(model_part, weights, variable)
    field = sensitivity_utils.ComputeShapeSensitivityField(
        assembler, dof_map, dof_map.FieldsToDofVector(weights), fd_step=1e-6)
    return value, field


def Compare(name, kratos_value, kratos_field, shipped_value, shipped_field, tolerance):
    scale = numpy.abs(shipped_field).max()
    relative = numpy.abs(kratos_field - shipped_field).max() / scale
    print(f"  {name}")
    print(f"    J        Kratos {kratos_value:+.10e}   shipped {shipped_value:+.10e}")
    print(f"    |dJ/dX|max                              {scale:.4e}")
    print(f"    largest disagreement                    {relative:.2e}")
    assert relative < tolerance, f"{name}: the two adjoints disagree by {relative:.2e}"
    return relative


def main():
    OUTPUT.mkdir(exist_ok=True)
    print("Kratos's adjoint stack vs the shipped adjoint:")

    with InCaseDirectory():
        cantilever = KratosCantileverAdjoint()
        cantilever_value, cantilever_shipped = ShippedCantileverAdjoint()

        diffusion, n_traced = KratosDiffusionAdjoint()
        diffusion_value, diffusion_shipped = ShippedDiffusionAdjoint()

    cantilever_field = cantilever.nodal["SHAPE_SENSITIVITY"]
    # Kratos' semi_analytic gradient takes a FORWARD difference where the
    # shipped field is central, so Kratos carries the larger step error and
    # sets the bar.
    cantilever_relative = Compare(
        "cantilever (StructuralMechanics)", cantilever.value, cantilever_field,
        cantilever_value, cantilever_shipped, 1e-4)

    # "point_temperature" AVERAGES over the traced part; "weighted_sum" sums.
    diffusion_field = diffusion.nodal["SHAPE_SENSITIVITY"]
    print(f"  objective normalization: Kratos averages over {n_traced} traced node(s), "
          f"weighted_sum sums -> factor {n_traced}")
    diffusion_relative = Compare(
        "diffusion square (ConvectionDiffusion)", diffusion.value, diffusion_field,
        diffusion_value / n_traced, diffusion_shipped / n_traced, 1e-6)

    assert numpy.abs(diffusion_field[:, 2]).max() == 0.0, \
        "a 2-D case must give an EXACTLY zero out-of-plane row, not a small one"
    print("  out-of-plane row of the 2-D case: exactly zero")

    figure, axes = pyplot.subplots(1, 2, figsize=(9.6, 3.9))
    for axis, (name, kratos, shipped, relative) in zip(axes, (
            ("cantilever (StructuralMechanics)", cantilever_field,
             cantilever_shipped, cantilever_relative),
            ("diffusion square (ConvectionDiffusion)", diffusion_field,
             diffusion_shipped / n_traced, diffusion_relative))):
        axis.scatter(shipped.ravel(), kratos.ravel(), s=22, zorder=3)
        limits = [shipped.min() * 1.08, shipped.max() * 1.08]
        axis.plot(limits, limits, "k--", linewidth=0.8, zorder=2)
        axis.set_xlabel("shipped adjoint  $dJ/dX$")
        axis.set_ylabel("Kratos SHAPE_SENSITIVITY")
        axis.set_title(f"{name}\nlargest disagreement {relative:.1e}", fontsize=10)
        axis.grid(True, alpha=0.3)
    figure.suptitle("Two independent adjoint implementations, two physics")
    figure.tight_layout()
    figure.savefig(DATA / "two_adjoints.png", dpi=130)

    with open(OUTPUT / "two_adjoints.json", "w") as handle:
        json.dump({"cantilever_value": cantilever.value,
                   "cantilever_relative": float(cantilever_relative),
                   "diffusion_value": diffusion.value,
                   "diffusion_relative": float(diffusion_relative),
                   "traced_nodes": int(n_traced)}, handle, indent=1)
    print(f"figure: {DATA / 'two_adjoints.png'}")


if __name__ == "__main__":
    main()
