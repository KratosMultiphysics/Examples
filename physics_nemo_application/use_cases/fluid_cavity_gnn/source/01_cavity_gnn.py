"""A MeshGraphNet surrogate for lid-driven cavity flow.

The first fluid case of these examples: incompressible Navier-Stokes in a
unit cavity, solved by FluidDynamicsApplication's monolithic VMS solver
(a short transient to a quasi-steady state, ~2000 time steps worth of
physics compressed into 15 steps at dt = 0.1). The lid velocity is swept;
a MeshGraphNet learns the (boundary-condition field) -> (velocity field)
map on the solver's own triangle mesh via the graph bridge, and is
deployed on an unseen lid velocity through GraphInferenceProcess.

The problem is NONDIMENSIONALIZED: inputs and targets are divided by the
lid velocity, and the lid velocity rides along as a third input channel
so the Reynolds-number dependence (the viscosity is fixed) stays
learnable. Without that scaling the interior recirculation - an order of
magnitude weaker than the lid boundary layer - washes out of the MSE.

Run time: ~3 minutes (11 cavity solves + training).
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

import fluid_case

OUTPUT = pathlib.Path("output")
DATA = pathlib.Path("..") / "data"

TRAIN_LID_VELOCITIES = numpy.linspace(0.5, 2.0, 10)
TEST_LID_VELOCITY = 1.15
DIVISIONS = 12
END_TIME = 1.5          # 15 steps at dt = 0.1: quasi-steady for Re ~ 100
EPOCHS = 700


def SolveCavity(lid_velocity):
    model = Kratos.Model()
    analysis = fluid_case.CreateFluidAnalysis(
        model, lid_velocity=float(lid_velocity), divisions=DIVISIONS,
        end_time=END_TIME)
    analysis.Run()
    return model, model["FluidModelPart"]


def BoundaryConditionFeatures(model_part, node_ids, lid_velocity):
    """(N, 3): the prescribed velocity NORMALIZED by the lid velocity
    (non-zero only on the lid), plus the lid velocity itself as a uniform
    channel carrying the Reynolds-number dependence."""
    features = []
    for node_id in node_ids:
        node = model_part.GetNode(int(node_id))
        if node.IsFixed(Kratos.VELOCITY_X):
            features.append([
                node.GetSolutionStepValue(Kratos.VELOCITY_X) / lid_velocity,
                node.GetSolutionStepValue(Kratos.VELOCITY_Y) / lid_velocity,
                lid_velocity])
        else:
            features.append([0.0, 0.0, lid_velocity])
    return numpy.array(features)


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

    # ---- training data ----------------------------------------------------
    samples = []
    graph_object = edge_tensor = None
    for lid_velocity in TRAIN_LID_VELOCITIES:
        model, model_part = SolveCavity(lid_velocity)
        node_features, edge_index, edge_features, node_ids = graph_bridge.BuildGraph(model_part)
        inputs = BoundaryConditionFeatures(model_part, node_ids, float(lid_velocity))
        target = numpy.array(
            [[model_part.GetNode(int(nid)).GetSolutionStepValue(Kratos.VELOCITY_X),
              model_part.GetNode(int(nid)).GetSolutionStepValue(Kratos.VELOCITY_Y),
              0.0]
             for nid in node_ids]) / float(lid_velocity)
        samples.append((torch.from_numpy(inputs).float(),
                        torch.from_numpy(target).float()))
        if graph_object is None:
            graph_object = graph_bridge.ToPyGGraph(edge_index, len(node_ids))
            edge_tensor = torch.from_numpy(edge_features).float()
        print(f"  lid velocity {lid_velocity:.2f}: solved "
              f"(max |u| = {numpy.abs(target).max():.3f})")

    # ---- train ------------------------------------------------------------
    torch.manual_seed(0)
    mgn = MeshGraphNet(input_dim_nodes=3, input_dim_edges=4, output_dim=3,
                       processor_size=6, hidden_dim_processor=48,
                       hidden_dim_node_encoder=48, hidden_dim_edge_encoder=48,
                       hidden_dim_node_decoder=48)
    optimizer = torch.optim.Adam(mgn.parameters(), lr=2e-3)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, EPOCHS)
    losses = []
    for epoch in range(EPOCHS):
        epoch_loss = 0.0
        for inputs, target in samples:
            optimizer.zero_grad()
            loss = torch.nn.functional.mse_loss(
                mgn(inputs, edge_tensor, graph_object), target)
            loss.backward()
            optimizer.step()
            epoch_loss += loss.item()
        scheduler.step()
        losses.append(epoch_loss / len(samples))
    mgn.save(str(OUTPUT / "cavity_mgn.mdlus"))
    print(f"final loss: {losses[-1]:.3e}")

    # ---- deployment on an unseen lid velocity -----------------------------
    model, model_part = SolveCavity(TEST_LID_VELOCITY)
    reference = numpy.array([[node.GetSolutionStepValue(Kratos.VELOCITY_X),
                              node.GetSolutionStepValue(Kratos.VELOCITY_Y), 0.0]
                             for node in model_part.Nodes])
    # the process gathers its input from nodal variables: stage the
    # nondimensionalized boundary-condition features in EMBEDDED_VELOCITY
    for node in model_part.Nodes:
        if node.IsFixed(Kratos.VELOCITY_X):
            node.SetValue(Kratos.EMBEDDED_VELOCITY, [
                node.GetSolutionStepValue(Kratos.VELOCITY_X) / TEST_LID_VELOCITY,
                node.GetSolutionStepValue(Kratos.VELOCITY_Y) / TEST_LID_VELOCITY,
                TEST_LID_VELOCITY])
        else:
            node.SetValue(Kratos.EMBEDDED_VELOCITY, [0.0, 0.0, TEST_LID_VELOCITY])
        node.SetValue(Kratos.MESH_DISPLACEMENT, [0.0, 0.0, 0.0])

    process = graph_inference_process.Factory(Kratos.Parameters("""{
        "Parameters": {
            "model_part_name" : "FluidModelPart",
            "model_settings"  : {
                "checkpoint_file" : "output/cavity_mgn.mdlus",
                "checkpoint_type" : "physicsnemo",
                "device"          : "cpu"
            },
            "input_fields"    : [ { "variable_name" : "EMBEDDED_VELOCITY",  "data_location" : "node_non_historical" } ],
            "output_fields"   : [ { "variable_name" : "MESH_DISPLACEMENT",  "data_location" : "node_non_historical" } ]
        }
    }"""), model)
    model_part.ProcessInfo[Kratos.STEP] = 1
    process.ExecuteFinalizeSolutionStep()
    predicted = numpy.array([list(node.GetValue(Kratos.MESH_DISPLACEMENT))[:3]
                             for node in model_part.Nodes]) * TEST_LID_VELOCITY
    rmse = float(numpy.sqrt(numpy.mean((predicted - reference) ** 2)))
    print(f"unseen lid velocity {TEST_LID_VELOCITY}: rmse {rmse:.2e} "
          f"(velocity scale {numpy.abs(reference).max():.2f})")

    # ---- figures ----------------------------------------------------------
    points, triangles = MeshArrays(model_part)
    triangulation = tri.Triangulation(points[:, 0], points[:, 1], triangles)
    magnitude = lambda field: numpy.hypot(field[:, 0], field[:, 1])
    limits = dict(vmin=0.0, vmax=float(magnitude(reference).max()))

    figure, axes = pyplot.subplots(1, 3, figsize=(13.6, 4.1))
    for axis, (field, title) in zip(axes[:2], [(reference, "VMS solver"),
                                               (predicted, "MeshGraphNet")]):
        mappable = axis.tricontourf(triangulation, magnitude(field),
                                    levels=24, cmap="viridis", **limits)
        skip = slice(None, None, 2)
        axis.quiver(points[skip, 0], points[skip, 1],
                    field[skip, 0], field[skip, 1], color="w", scale=18, width=0.004)
        axis.set_aspect("equal")
        axis.set_title(f"|velocity| ({title}), unseen lid u = {TEST_LID_VELOCITY}")
        figure.colorbar(mappable, ax=axis, shrink=0.85)
    error = axes[2].tricontourf(triangulation, magnitude(predicted - reference),
                                levels=24, cmap="magma")
    axes[2].set_aspect("equal")
    axes[2].set_title("|error|")
    figure.colorbar(error, ax=axes[2], shrink=0.85)
    figure.tight_layout()
    figure.savefig(DATA / "cavity_fields.png", dpi=130)

    figure, axes = pyplot.subplots(1, 2, figsize=(10.4, 4.0))
    axes[0].semilogy(losses)
    axes[0].set_xlabel("epoch")
    axes[0].set_ylabel("MSE")
    axes[0].set_title("MeshGraphNet training")
    axes[0].grid(True, which="both", alpha=0.3)
    axes[1].plot(reference.ravel(), predicted.ravel(), ".", markersize=2.5, alpha=0.4)
    span = [reference.min(), reference.max()]
    axes[1].plot(span, span, "k--", linewidth=1)
    axes[1].set_xlabel("solver velocity component")
    axes[1].set_ylabel("MeshGraphNet velocity component")
    axes[1].set_title("Parity, unseen lid velocity")
    axes[1].grid(True, alpha=0.3)
    figure.tight_layout()
    figure.savefig(DATA / "cavity_training_and_parity.png", dpi=130)

    with open(OUTPUT / "cavity_summary.json", "w") as handle:
        json.dump({"rmse": rmse, "final_loss": losses[-1],
                   "velocity_scale": float(numpy.abs(reference).max())}, handle, indent=1)
    print(f"figures: {DATA / 'cavity_fields.png'}, {DATA / 'cavity_training_and_parity.png'}")


if __name__ == "__main__":
    main()
