"""Stage 2 - the encoding ladder on a shape none of the models saw.

A new hole position and radius, generated and solved the same way; each
encoding's net predicts the temperature field from its features alone.
The geometry-blind net still predicts the field of "some average shape"
(its hole never moved); the SDF encodings follow the geometry.

The close: the predicted field is turned into a heat-flux magnitude by
calculus_bridge.ComputeNodalDerivatives (least-squares gradient on the
generated triangles, no solver assembly) and compared against the same
diagnostic on the solver's field - a physics quantity, computed the same
way for both, on a mesh that started as five lines of SDF math.

Run time: well under a minute.
"""

import json
import pathlib

import numpy
import torch
from matplotlib import pyplot

import KratosMultiphysics as Kratos
from KratosMultiphysics.PhysicsNeMoApplication.bridges import calculus_bridge
import thermal_hole_case

OUTPUT = pathlib.Path("output")
DATA = pathlib.Path("..") / "data"

UNSEEN = {"center": (0.58, 0.42), "radius": 0.17}   # not in the training family
ENCODINGS = {"blind (x, y)": 2, "+ phi": 3, "+ grad phi": 5, "+ laplacian": 6}


def FluxMagnitude(part, field_location):
    """|grad T| per node via the calculus bridge's lsq gradient."""
    calculus_bridge.ComputeNodalDerivatives(part, Kratos.Parameters("""{
        "operations": [{
            "field"           : "TEMPERATURE",
            "field_location"  : "%s",
            "operation"       : "gradient",
            "output_variable" : "TEMPERATURE_GRADIENT",
            "output_location" : "node_non_historical"
        }]
    }""" % field_location))
    gradients = numpy.array([node.GetValue(Kratos.TEMPERATURE_GRADIENT)
                             for node in part.Nodes])
    return numpy.linalg.norm(gradients[:, :2], axis=1)


def main():
    OUTPUT.mkdir(exist_ok=True)
    DATA.mkdir(exist_ok=True)
    Kratos.Logger.GetDefaultOutput().SetSeverity(Kratos.Logger.Severity.WARNING)

    model = Kratos.Model()
    part = thermal_hole_case.GenerateAndSolve(model, UNSEEN["center"], UNSEEN["radius"])
    truth = thermal_hole_case.Temperatures(part)
    ladder = torch.tensor(thermal_hole_case.FeatureLadder(
        part, UNSEEN["center"], UNSEEN["radius"]), dtype=torch.float64)
    print(f"unseen shape {UNSEEN}: {part.NumberOfNodes()} nodes")

    predictions, errors = {}, {}
    for name, columns in ENCODINGS.items():
        net = torch.jit.load(str(OUTPUT / f"encoding_{columns}.pt")).eval()
        with torch.no_grad():
            predicted = net(ladder[:, :columns]).numpy()[:, 0]
        predictions[name] = predicted
        errors[name] = float(numpy.sqrt(((predicted - truth) ** 2).mean()))
        print(f"  {name:14s}: unseen-shape RMSE {errors[name]:.2e}")

    best_name = min(errors, key=errors.get)
    best = predictions[best_name]

    # ---- flux diagnostic on solver field and best prediction ---------------
    flux_truth = FluxMagnitude(part, "node_historical")
    # the same diagnostic on the PREDICTED field: swap it into TEMPERATURE,
    # differentiate, swap the solver's field back
    saved = truth.copy()
    for node, value in zip(part.Nodes, best):
        node.SetSolutionStepValue(Kratos.TEMPERATURE, float(value))
    flux_predicted = FluxMagnitude(part, "node_historical")
    for node, value in zip(part.Nodes, saved):
        node.SetSolutionStepValue(Kratos.TEMPERATURE, float(value))
    flux_rmse = float(numpy.sqrt(((flux_predicted - flux_truth) ** 2).mean()))
    print(f"flux-magnitude RMSE ({best_name}): {flux_rmse:.2e} "
          f"(field range {flux_truth.min():.2f}..{flux_truth.max():.2f})")

    # ---- figures -----------------------------------------------------------
    points, triangles = thermal_hole_case.Triangulation(part)

    figure, axes = pyplot.subplots(1, 3, figsize=(12.6, 3.9))
    panels = [(truth, "solver (generated mesh)"),
              (best, f"surrogate: {best_name}"),
              (numpy.abs(best - truth), "absolute error")]
    for axis, (field, title) in zip(axes, panels):
        cmap = "inferno" if "error" not in title else "viridis"
        plot = axis.tricontourf(points[:, 0], points[:, 1], triangles, field,
                                levels=21, cmap=cmap)
        figure.colorbar(plot, ax=axis, shrink=0.9)
        axis.set_title(title, fontsize=10)
        axis.set_aspect("equal")
        axis.set_xticks([])
        axis.set_yticks([])
    figure.suptitle(f"Unseen shape: hole {UNSEEN['center']}, r = {UNSEEN['radius']}")
    figure.tight_layout()
    figure.savefig(DATA / "unseen_shape_prediction.png", dpi=130)

    figure, (left, right) = pyplot.subplots(
        1, 2, figsize=(11.6, 4.0), gridspec_kw={"width_ratios": [1.0, 1.35]})
    names = list(ENCODINGS)
    train_summary = json.load(open(OUTPUT / "training_summary.json"))
    train_rmse = [train_summary["encodings"][name]["train_rmse"] for name in names]
    positions = numpy.arange(len(names))
    left.bar(positions - 0.18, train_rmse, 0.36, label="training shapes")
    left.bar(positions + 0.18, [errors[name] for name in names], 0.36,
             label="unseen shape")
    left.set_yscale("log")
    left.set_xticks(positions)
    left.set_xticklabels(names, rotation=12, fontsize=9)
    left.set_ylabel("temperature RMSE")
    left.set_title("The geometry-encoding ladder")
    left.legend()
    left.grid(True, axis="y", which="both", alpha=0.3)

    plot = right.tricontourf(points[:, 0], points[:, 1], triangles, flux_predicted,
                             levels=21, cmap="magma")
    figure.colorbar(plot, ax=right, shrink=0.9, label="|grad T| (calculus bridge)")
    right.set_title(f"Heat-flux magnitude of the predicted field", fontsize=10)
    right.set_aspect("equal")
    right.set_xticks([])
    right.set_yticks([])
    figure.tight_layout()
    figure.savefig(DATA / "encoding_ladder.png", dpi=130)

    with open(OUTPUT / "deploy_summary.json", "w") as handle:
        json.dump({"unseen": {"center": list(UNSEEN["center"]),
                              "radius": UNSEEN["radius"],
                              "nodes": part.NumberOfNodes()},
                   "errors": errors, "best": best_name, "flux_rmse": flux_rmse,
                   "flux_range": [float(flux_truth.min()), float(flux_truth.max())]},
                  handle, indent=1)
    print(f"figures: {DATA / 'unseen_shape_prediction.png'}, {DATA / 'encoding_ladder.png'}")


if __name__ == "__main__":
    main()
