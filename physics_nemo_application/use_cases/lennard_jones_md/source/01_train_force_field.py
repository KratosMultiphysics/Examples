"""A Lennard-Jones force field: a MeshGraphNet trained on periodic graphs.

Molecular dynamics is the Lagrangian particle problem at its purest - no
mesh, no persistent connectivity, and interactions that exist only inside a
cutoff radius, in a PERIODIC box where the two nearest atoms may sit on
opposite sides of the domain. NVIDIA's own molecular-dynamics example
trains the generic MeshGraphNet on (positions -> forces) frames: no
molecular architecture exists upstream and none is needed. What the bridge
had to grow was the minimum-image neighbour search, which is
particle_bridge's "box_size".

This script:

1. integrates reference trajectories with velocity Verlet in reduced units
   (utilities.lennard_jones_reference - numpy only, no torch);
2. windows them into training pairs. Velocity Verlet IS the Stoermer-Verlet
   recurrence, so CreateParticleTrajectoryDataset's central-difference
   acceleration targets equal the integrator's own forces to round-off -
   labels with no discretization error in them;
3. trains two MeshGraphNet heads on the periodic radius graph of each
   frame: per-atom force (3 channels) and per-atom potential energy (1),
   the two halves of a learned force field;
4. saves the force model with BOTH normalization halves in its card, which
   is what lets ParticleInferenceProcess standardize the raw velocity
   history it gathers and de-normalize the acceleration it integrates.

WHY THE TRAJECTORIES ARE SHORT, which is the modelling lesson here. The
atoms start on a lattice and melt into a liquid. Once they do, pairs come
close and the r^-13 repulsive core produces forces one to two orders of
magnitude larger than the typical ones: measured over ten seeds, the
largest force in the trajectory is 2.0 at 20 steps, 32.3 at 26 and 81.3 at
32. Those spikes dominate a mean-squared loss, and a small network fits
none of them - trained across the melting onset the loss sits at the
predict-zero value and the model loses to its own baseline. So the recipe
is pinned in the near-equilibrium window, and the width of that window is
stated rather than hidden. A force field for the repulsive core is a
different (and much larger) model.

The reproducible claim (everything seeded): averaged over FOUR held-out
trajectories the model never saw, its force error is below that of the
mean-force predictor - the baseline a model ignoring its de-normalized
inputs could still match. Per-trajectory numbers are printed too, because
a mean can hide a single bad case.

Runs on CPU by design: the graphs are tiny (64 atoms, ~1150 edges) and a
fixed-seed CPU run is what the committed numbers were measured on.

Run from this directory:  python3 01_train_force_field.py
Outputs: ../data/lj_training.png, output/lj_forces.mdlus
"""

import json
import pathlib

import numpy
import torch

import KratosMultiphysics as Kratos
import KratosMultiphysics.PhysicsNeMoApplication  # registers the application  # noqa: F401
from KratosMultiphysics.PhysicsNeMoApplication.bridges import graph_bridge, particle_bridge
from KratosMultiphysics.PhysicsNeMoApplication.training import training_utils
from KratosMultiphysics.PhysicsNeMoApplication.training.torch_dataset import (
    CreateParticleTrajectoryDataset, MakeNormalizationCardEntries)
from KratosMultiphysics.PhysicsNeMoApplication.utilities import lennard_jones_reference as lj
from physicsnemo.models.meshgraphnet import MeshGraphNet

HERE = pathlib.Path(__file__).parent
DATA = HERE.parent / "data"
OUTPUT = HERE / "output"

ATOMS_PER_SIDE = 4          # 64 atoms on a simple cubic lattice
STEPS = 20                  # the near-equilibrium window (see the docstring)
DT = 0.005
HISTORY = 2                 # velocity states per feature window
HIDDEN = 32
EPOCHS = 120
TRAIN_SEEDS = tuple(range(8))
HELD_OUT_SEEDS = (8, 9, 10, 11)
# the usual 2.5 sigma cutoff; the box is 6.0, so the radius stays under half
# of it, which is what the minimum-image convention requires
CONNECTIVITY = '{"type": "radius", "radius": 2.5, "box_size": [6.0], "backend": "auto"}'


def Trajectory(seed):
    return lj.GenerateTrajectory(
        atoms_per_side=ATOMS_PER_SIDE, steps=STEPS, dt=DT, seed=seed)


def BuildSamples(dataset, targets=None):
    """(node features, edge features, PyG graph, target) per frame.

    The graph is rebuilt for every frame: the atoms move, so unlike a mesh
    the neighbour list is not shared between samples.
    """
    samples = []
    for index in range(len(dataset)):
        features, target = dataset[index]
        edge_index, edge_features = particle_bridge.BuildParticleGraphFromPositions(
            dataset.positions[index], Kratos.Parameters(CONNECTIVITY))
        samples.append((features, torch.from_numpy(edge_features),
                        graph_bridge.ToPyGGraph(edge_index, features.shape[0]),
                        target if targets is None else targets[index]))
    return samples


def MakeModel(output_dim, seed=0):
    torch.manual_seed(seed)
    return MeshGraphNet(
        input_dim_nodes=HISTORY * 3, input_dim_edges=4, output_dim=output_dim,
        processor_size=2, hidden_dim_processor=HIDDEN, hidden_dim_node_encoder=HIDDEN,
        hidden_dim_edge_encoder=HIDDEN, hidden_dim_node_decoder=HIDDEN).double()


def Train(model, samples, epochs, learning_rate, tag):
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    history = []
    for epoch in range(epochs):
        total = 0.0
        for features, edge_features, graph, target in samples:
            optimizer.zero_grad()
            loss = torch.nn.functional.mse_loss(
                model(features, edge_features, graph), target)
            loss.backward()
            optimizer.step()
            total += loss.item()
        history.append(total / len(samples))
        if epoch % 20 == 0 or epoch == epochs - 1:
            print(f"[train] {tag} epoch {epoch:3d}: {history[-1]:.4f}")
    return history


def EvaluateHeldOut(model, dataset):
    """Force error on trajectories the model never saw.

    Each held-out window is standardized with the TRAINING statistics (the
    model was trained on those) and the prediction de-normalized with the
    training target statistics - exactly what the model card makes the
    deployment process do.
    """
    feature_mean = torch.as_tensor(numpy.asarray(dataset.feature_mean, dtype=float))
    feature_std = torch.as_tensor(numpy.asarray(dataset.feature_std, dtype=float))
    target_mean = numpy.asarray(dataset.target_mean, dtype=float)
    target_std = numpy.asarray(dataset.target_std, dtype=float)

    results, scatter = [], []
    for seed in HELD_OUT_SEEDS:
        trajectory = Trajectory(seed)
        raw = CreateParticleTrajectoryDataset(
            trajectory["positions"], history_size=HISTORY, delta_time=DT)
        predicted, reference = [], []
        with torch.no_grad():
            for index in range(len(raw)):
                features, _ = raw[index]
                edge_index, edge_features = particle_bridge.BuildParticleGraphFromPositions(
                    raw.positions[index], Kratos.Parameters(CONNECTIVITY))
                graph = graph_bridge.ToPyGGraph(edge_index, features.shape[0])
                output = model((features - feature_mean) / feature_std,
                               torch.from_numpy(edge_features), graph)
                predicted.append(output.numpy() * target_std + target_mean)
                # mass is 1 in reduced units, so the acceleration IS the force
                reference.append(trajectory["forces"][HISTORY + index])
        predicted, reference = numpy.stack(predicted), numpy.stack(reference)

        error = float(numpy.sqrt(numpy.mean((predicted - reference) ** 2)))
        # a model that ignored its inputs entirely could still predict the
        # mean force of each frame; that is the bar a force field must clear
        baseline = float(numpy.sqrt(numpy.mean(
            (reference - reference.mean(axis=1, keepdims=True)) ** 2)))
        results.append({"seed": seed, "rmse": error, "baseline": baseline})
        scatter.append((predicted, reference))
        print(f"[eval] held-out seed {seed}: force RMSE {error:.4f} against the "
              f"mean-force predictor's {baseline:.4f} ({baseline / error:.2f}x)")
    return results, scatter


def Render(force_history, energy_history, scatter, results, energy_pair):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure, axes = plt.subplots(2, 2, figsize=(9.4, 6.6), constrained_layout=True)

    axes[0][0].semilogy(force_history, label="force head")
    axes[0][0].semilogy(energy_history, color="#c0392b", label="potential-energy head")
    axes[0][0].set_xlabel("epoch"), axes[0][0].set_ylabel("MSE (standardized)")
    axes[0][0].set_title("training"), axes[0][0].legend(fontsize=8)
    axes[0][0].grid(alpha=0.3)

    positions = numpy.arange(len(results))
    axes[0][1].bar(positions - 0.18, [r["rmse"] for r in results], width=0.36,
                   label="learned force field")
    axes[0][1].bar(positions + 0.18, [r["baseline"] for r in results], width=0.36,
                   color="#7f8c8d", label="mean-force predictor")
    axes[0][1].set_xticks(positions)
    axes[0][1].set_xticklabels([f"seed {r['seed']}" for r in results], fontsize=8)
    axes[0][1].set_ylabel("force RMSE"), axes[0][1].legend(fontsize=8)
    axes[0][1].set_title("held-out trajectories")

    predicted = numpy.concatenate([p.ravel() for p, _ in scatter])
    reference = numpy.concatenate([r.ravel() for _, r in scatter])
    axes[1][0].scatter(reference, predicted, s=3, alpha=0.2)
    limits = [reference.min(), reference.max()]
    axes[1][0].plot(limits, limits, "k--", lw=1)
    axes[1][0].set_xlabel("reference force component")
    axes[1][0].set_ylabel("predicted")
    axes[1][0].set_title("all held-out frames")

    predicted_energy, reference_energy = energy_pair
    axes[1][1].scatter(reference_energy, predicted_energy, s=16, alpha=0.7, color="#c0392b")
    limits = [reference_energy.min(), reference_energy.max()]
    axes[1][1].plot(limits, limits, "k--", lw=1)
    axes[1][1].set_xlabel("reference per-atom potential")
    axes[1][1].set_ylabel("predicted")
    axes[1][1].set_title("training frame 0")

    figure.suptitle("A Lennard-Jones force field on periodic radius graphs")
    figure.savefig(DATA / "lj_training.png", dpi=130)


if __name__ == "__main__":
    DATA.mkdir(exist_ok=True)
    OUTPUT.mkdir(exist_ok=True)
    Kratos.Logger.GetDefaultOutput().SetSeverity(Kratos.Logger.Severity.WARNING)

    trajectories = [Trajectory(seed) for seed in TRAIN_SEEDS]
    largest = max(float(numpy.linalg.norm(t["forces"], axis=2).max()) for t in trajectories)
    print(f"[data] {len(trajectories)} training trajectories of {STEPS} steps; "
          f"largest force anywhere in them {largest:.2f} (the near-equilibrium window)")

    positions = [trajectory["positions"] for trajectory in trajectories]
    dataset = CreateParticleTrajectoryDataset(
        positions, history_size=HISTORY, delta_time=DT, normalize=True)

    # the exactness the whole recipe rests on: the dataset's central
    # differences ARE the integrator's forces, because velocity Verlet is
    # the Stoermer-Verlet recurrence
    check = CreateParticleTrajectoryDataset(
        positions[0], history_size=HISTORY, delta_time=DT)
    residual = float(numpy.abs(
        check[0][1].numpy() - trajectories[0]["forces"][HISTORY]).max())
    print(f"[data] {len(dataset)} samples; central-difference targets match the "
          f"reference forces to {residual:.2e}")

    samples = BuildSamples(dataset)
    edges = int(samples[0][2].edge_index.shape[1])
    print(f"[data] frame 0 graph: {edges} directed edges, "
          f"{edges / samples[0][0].shape[0]:.1f} neighbours per atom")

    force_model = MakeModel(output_dim=3)
    force_history = Train(force_model, samples, EPOCHS, 2e-3, "force")

    # the second half of a force field: a scalar per atom on the same graphs
    potential = numpy.concatenate([
        trajectory["potential"][HISTORY:trajectory["potential"].shape[0] - 1]
        for trajectory in trajectories])
    energy_mean, energy_std = potential.mean(), potential.std()
    energy_targets = [torch.from_numpy((potential[i] - energy_mean) / energy_std)[:, None]
                      for i in range(len(dataset))]
    energy_samples = BuildSamples(dataset, energy_targets)
    energy_model = MakeModel(output_dim=1, seed=1)
    energy_history = Train(energy_model, energy_samples, EPOCHS, 1e-3, "energy")

    # both normalization halves travel with the checkpoint: the process
    # standardizes the RAW velocity history it gathers with the first and
    # de-normalizes the acceleration it integrates with the second
    card = {"input_fields": [{"variable_name": "VELOCITY",
                              "data_location": "node_historical"}],
            "output_fields": [{"variable_name": "ACCELERATION",
                               "data_location": "node_historical"}],
            "history_size": HISTORY,
            "connectivity": {"radius": 2.5, "box_size": [6.0]}}
    card.update(MakeNormalizationCardEntries(dataset))
    training_utils.SaveTrainedModel(force_model, OUTPUT / "lj_forces.mdlus", card=card)
    print(f"[train] checkpoint at {OUTPUT / 'lj_forces.mdlus'} with its normalization card")

    results, scatter = EvaluateHeldOut(force_model, dataset)
    with torch.no_grad():
        features, edge_features, graph, _ = energy_samples[0]
        predicted_energy = (energy_model(features, edge_features, graph).numpy().ravel()
                            * energy_std + energy_mean)
    Render(force_history, energy_history, scatter, results,
           (predicted_energy, potential[0]))

    mean_error = float(numpy.mean([r["rmse"] for r in results]))
    mean_baseline = float(numpy.mean([r["baseline"] for r in results]))
    print(f"[eval] over {len(results)} held-out trajectories: {mean_error:.4f} "
          f"against {mean_baseline:.4f} ({mean_baseline / mean_error:.2f}x)")

    with open(OUTPUT / "training_summary.json", "w") as handle:
        json.dump({"held_out": results, "mean_rmse": mean_error,
                   "mean_baseline": mean_baseline, "force_loss": force_history[-1],
                   "energy_loss": energy_history[-1], "target_match": residual,
                   "largest_training_force": largest}, handle, indent=1)

    # the reproducible claim: averaged over four trajectories it never saw,
    # the force field beats predicting each frame's mean force - the one
    # baseline a model that ignored its de-normalized inputs could reach.
    # The per-seed numbers above are printed so a good mean cannot hide a
    # bad case.
    assert mean_error < mean_baseline, (mean_error, mean_baseline, results)
    print("[done] figure at data/lj_training.png")
