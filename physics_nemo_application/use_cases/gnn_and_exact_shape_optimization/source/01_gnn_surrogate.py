"""Stage 1 - a MeshGraphNet surrogate on the solver's own mesh graph.

Grid models (see the thermal_surrogate_lifecycle example) need the fields
resampled onto a voxel grid. A graph neural network skips that: the graph
bridge extracts the mesh's true element-edge graph - bidirectional edges
with relative-position features, MeshGraphNet's convention - and the model
predicts directly on the nodes. The same machinery applies unchanged to
unstructured meshes where no sensible grid exists.

Sweeps the conductivity, trains a small MeshGraphNet, and deploys it on an
unseen conductivity through GraphInferenceProcess - the same
gather/predict/scatter loop a solver-coupled deployment uses.

Run time: ~2 minutes.
"""

import json
import pathlib

import numpy
import torch
from matplotlib import pyplot, tri
from physicsnemo.models.meshgraphnet import MeshGraphNet

import KratosMultiphysics as Kratos
from KratosMultiphysics.PhysicsNeMoApplication import graph_bridge
from KratosMultiphysics.PhysicsNeMoApplication import graph_inference_process

import thermal_case

OUTPUT = pathlib.Path("output")
DATA = pathlib.Path("..") / "data"

TRAIN_CONDUCTIVITIES = numpy.linspace(0.5, 2.0, 12)
TEST_CONDUCTIVITY = 1.15   # not in the sweep
DIVISIONS = 15
EPOCHS = 700


def SolveCase(conductivity: float):
    model = Kratos.Model()
    analysis = thermal_case.CreateThermalAnalysis(
        model, conductivity=float(conductivity), heat_flux=1.0, divisions=DIVISIONS)
    analysis.Run()
    return model, model["ThermalModelPart"]


def MeshArrays(model_part):
    points = numpy.array([[node.X, node.Y] for node in model_part.Nodes])
    rows = {node.Id: index for index, node in enumerate(model_part.Nodes)}
    triangles = numpy.array([[rows[element.GetGeometry()[i].Id] for i in range(3)]
                             for element in model_part.Elements])
    return points, triangles


def main():
    OUTPUT.mkdir(exist_ok=True)
    DATA.mkdir(exist_ok=True)
    Kratos.Logger.GetDefaultOutput().SetSeverity(Kratos.Logger.Severity.WARNING)

    # ---- training data: one solve per conductivity, graphs via the bridge --
    samples = []
    graph_object = edge_tensor = None
    for conductivity in TRAIN_CONDUCTIVITIES:
        model, model_part = SolveCase(conductivity)
        node_features, edge_index, edge_features, node_ids = graph_bridge.BuildGraph(
            model_part,
            (("CONDUCTIVITY", "node_historical"), ("HEAT_FLUX", "node_historical")))
        target = numpy.array([[model_part.GetNode(int(node_id)).GetSolutionStepValue(
            Kratos.TEMPERATURE)] for node_id in node_ids])
        samples.append((torch.from_numpy(node_features).float(),
                        torch.from_numpy(target).float()))
        if graph_object is None:  # topology is identical across the sweep
            graph_object = graph_bridge.ToPyGGraph(edge_index, len(node_ids))
            edge_tensor = torch.from_numpy(edge_features).float()
    print(f"{len(samples)} solved cases, {samples[0][0].shape[0]} nodes each")

    # ---- train ------------------------------------------------------------
    torch.manual_seed(0)
    mgn = MeshGraphNet(input_dim_nodes=2, input_dim_edges=4, output_dim=1,
                       processor_size=4, hidden_dim_processor=32,
                       hidden_dim_node_encoder=32, hidden_dim_edge_encoder=32,
                       hidden_dim_node_decoder=32)
    optimizer = torch.optim.Adam(mgn.parameters(), lr=2e-3)
    losses = []
    for epoch in range(EPOCHS):
        epoch_loss = 0.0
        for node_features, target in samples:
            optimizer.zero_grad()
            loss = torch.nn.functional.mse_loss(
                mgn(node_features, edge_tensor, graph_object), target)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
        losses.append(epoch_loss / len(samples))
    mgn.save(str(OUTPUT / "thermal_mgn.mdlus"))
    print(f"final loss: {losses[-1]:.3e}")

    # ---- deploy on an unseen conductivity through the process -------------
    model, model_part = SolveCase(TEST_CONDUCTIVITY)
    reference = numpy.array([node.GetSolutionStepValue(Kratos.TEMPERATURE)
                             for node in model_part.Nodes])
    for node in model_part.Nodes:
        node.SetValue(Kratos.NODAL_PAUX, 0.0)

    process = graph_inference_process.Factory(Kratos.Parameters("""{
        "Parameters": {
            "model_part_name" : "ThermalModelPart",
            "model_settings"  : {
                "checkpoint_file" : "output/thermal_mgn.mdlus",
                "checkpoint_type" : "physicsnemo",
                "device"          : "cpu"
            },
            "input_fields"    : [ { "variable_name" : "CONDUCTIVITY", "data_location" : "node_historical" },
                                  { "variable_name" : "HEAT_FLUX",    "data_location" : "node_historical" } ],
            "output_fields"   : [ { "variable_name" : "NODAL_PAUX",   "data_location" : "node_non_historical" } ]
        }
    }"""), model)
    model_part.ProcessInfo[Kratos.STEP] = 1
    process.ExecuteFinalizeSolutionStep()
    predicted = numpy.array([node.GetValue(Kratos.NODAL_PAUX)
                             for node in model_part.Nodes])
    rmse = float(numpy.sqrt(numpy.mean((predicted - reference) ** 2)))
    print(f"unseen k={TEST_CONDUCTIVITY}: rmse {rmse:.2e} "
          f"(field max {numpy.abs(reference).max():.2e})")

    # ---- figures ----------------------------------------------------------
    points, triangles = MeshArrays(model_part)
    triangulation = tri.Triangulation(points[:, 0], points[:, 1], triangles)
    figure, axes = pyplot.subplots(1, 3, figsize=(13.2, 3.9))
    shared = {"levels": 20, "cmap": "viridis",
              "vmin": float(reference.min()), "vmax": float(reference.max())}
    for axis, (values, title) in zip(axes[:2], [(reference, "solver"),
                                                (predicted, "MeshGraphNet")]):
        mappable = axis.tricontourf(triangulation, values, **shared)
        axis.triplot(triangulation, color="w", linewidth=0.25, alpha=0.5)
        axis.set_aspect("equal")
        axis.set_title(f"TEMPERATURE ({title}), unseen k = {TEST_CONDUCTIVITY}")
        figure.colorbar(mappable, ax=axis, shrink=0.85)
    error_map = axes[2].tricontourf(triangulation, numpy.abs(predicted - reference),
                                    levels=20, cmap="magma")
    axes[2].set_aspect("equal")
    axes[2].set_title("absolute error")
    figure.colorbar(error_map, ax=axes[2], shrink=0.85)
    figure.tight_layout()
    figure.savefig(DATA / "gnn_fields.png", dpi=130)

    figure, axes = pyplot.subplots(1, 2, figsize=(10.4, 4.0))
    axes[0].semilogy(losses)
    axes[0].set_xlabel("epoch")
    axes[0].set_ylabel("MSE")
    axes[0].set_title("MeshGraphNet training")
    axes[0].grid(True, which="both", alpha=0.3)
    axes[1].plot(reference, predicted, ".", markersize=3, alpha=0.5)
    limits = [reference.min(), reference.max()]
    axes[1].plot(limits, limits, "k--", linewidth=1)
    axes[1].set_xlabel("solver TEMPERATURE")
    axes[1].set_ylabel("MeshGraphNet TEMPERATURE")
    axes[1].set_title(f"Parity, unseen k = {TEST_CONDUCTIVITY}")
    axes[1].grid(True, alpha=0.3)
    figure.tight_layout()
    figure.savefig(DATA / "gnn_training_and_parity.png", dpi=130)

    with open(OUTPUT / "gnn_summary.json", "w") as handle:
        json.dump({"rmse": rmse, "final_loss": losses[-1],
                   "field_max": float(numpy.abs(reference).max())}, handle, indent=1)
    print(f"figures: {DATA / 'gnn_fields.png'}, {DATA / 'gnn_training_and_parity.png'}")


if __name__ == "__main__":
    main()
