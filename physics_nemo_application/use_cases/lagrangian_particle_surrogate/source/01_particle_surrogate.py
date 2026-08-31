"""A Lagrangian particle surrogate, deployed with its normalization card.

New physics for these examples: no mesh at all. A cloud of particles under
gravity and linear drag (a = g - c v, closed-form solvable) provides the
trajectories; a model learns the per-particle acceleration from a velocity
window, and ParticleInferenceProcess deploys it - building the proximity
graph each step (radius connectivity via particle_bridge), running the
model, and integrating the predicted acceleration into velocities and
POSITIONS (semi-implicit Euler; the mesh moves).

The governance detail this demonstrates: the model is trained on
STANDARDIZED accelerations (CreateParticleTrajectoryDataset normalize),
and the process reads the model card's "output_normalization" to
de-normalize before integrating. The process integrates its output TWICE
- v += dt a, x += dt v - so deploying the raw normalized output would
compound straight into positions; the card is what makes the checkpoint
self-describing.

Run time: under a minute.
"""

import json
import pathlib

import numpy
import torch
from matplotlib import pyplot
from PIL import Image

import KratosMultiphysics as Kratos
import KratosMultiphysics.PhysicsNeMoApplication  # registers the application  # noqa: F401
from KratosMultiphysics.PhysicsNeMoApplication.deployment import model_registry
from KratosMultiphysics.PhysicsNeMoApplication.processes.inference import particle_inference_process
from KratosMultiphysics.PhysicsNeMoApplication.training import training_utils
from KratosMultiphysics.PhysicsNeMoApplication.training.torch_dataset import CreateParticleTrajectoryDataset

OUTPUT = pathlib.Path("output")
DATA = pathlib.Path("..") / "data"

GRAVITY = numpy.array([0.0, 0.0, -9.81])
DAMPING = 0.5
DT = 0.02
PARTICLES = 40
DEPLOY_STEPS = 40


def Simulate(x0, steps, initial_velocity=None):
    """Ground truth: symplectic Euler of a = g - c v (matches the process)."""
    positions = [x0.copy()]
    velocity = numpy.zeros_like(x0) if initial_velocity is None else initial_velocity.copy()
    x = x0.copy()
    for _ in range(steps - 1):
        acceleration = GRAVITY - DAMPING * velocity
        velocity = velocity + DT * acceleration
        x = x + DT * velocity
        positions.append(x.copy())
    return numpy.stack(positions)  # (T, N, 3)


class TensorInterface(torch.nn.Module):
    """The process's "tensor" interface: (nodes, edges, edge_index) -> per-node output."""

    def __init__(self, trunk):
        super().__init__()
        self.trunk = trunk

    def forward(self, nodes, edges, edge_index):
        return self.trunk(nodes)


def main():
    OUTPUT.mkdir(exist_ok=True)
    DATA.mkdir(exist_ok=True)
    Kratos.Logger.GetDefaultOutput().SetSeverity(Kratos.Logger.Severity.WARNING)

    # ---- trajectories and the standardized dataset -------------------------
    rng = numpy.random.default_rng(0)
    trajectories = [Simulate(rng.random((PARTICLES, 3)) * [4.0, 4.0, 2.0], steps=50)
                    for _ in range(8)]
    # normalize=False: the process feeds the model RAW velocities at
    # deployment, so the features must stay raw here too - only the TARGETS
    # are standardized (by hand, with the dataset's own statistics), and the
    # model card is what undoes that at deployment
    dataset = CreateParticleTrajectoryDataset(
        trajectories, history_size=1, delta_time=DT, normalize=False)
    mean = numpy.asarray(dataset.target_mean, dtype=float)
    std = numpy.asarray(dataset.target_std, dtype=float)
    print(f"{len(dataset)} samples; target statistics "
          f"(mean {mean.round(3).tolist()}, std {std.round(3).tolist()})")

    # ---- train on raw features -> standardized accelerations ---------------
    torch.manual_seed(0)
    trunk = torch.nn.Sequential(
        torch.nn.Linear(3, 32), torch.nn.Tanh(), torch.nn.Linear(32, 3)).double()
    inputs = torch.cat([dataset[i][0] for i in range(len(dataset))])
    raw_targets = torch.cat([dataset[i][1] for i in range(len(dataset))])
    targets = (raw_targets - torch.as_tensor(mean)) / torch.as_tensor(std)
    history = training_utils.TrainModel(
        trunk, torch.utils.data.TensorDataset(inputs, targets), Kratos.Parameters("""{
            "epochs"        : 400,
            "batch_size"    : 1024,
            "learning_rate" : 5e-3,
            "device"        : "cpu",
            "seed"          : 0
        }"""))
    print(f"final training loss: {history[-1]:.3e}")

    # the checkpoint carries its own de-normalization
    checkpoint = OUTPUT / "particle_surrogate.pt"
    torch.jit.script(TensorInterface(trunk.cpu())).save(str(checkpoint))
    model_registry.SaveModelCard(checkpoint, {
        "output_normalization": {"type": "mean_std",
                                 "mean": mean.tolist(), "std": std.tolist()}})

    # ---- deployment: an unseen cloud stepped by the process ----------------
    kratos_model = Kratos.Model()
    particles = kratos_model.CreateModelPart("Particles")
    for variable in (Kratos.VELOCITY, Kratos.ACCELERATION, Kratos.DISPLACEMENT):
        particles.AddNodalSolutionStepVariable(variable)
    particles.SetBufferSize(2)
    x0 = rng.random((PARTICLES, 3)) * [4.0, 4.0, 2.0] + [0.0, 0.0, 3.0]
    for index, xyz in enumerate(x0):
        particles.CreateNewNode(index + 1, *xyz)
    particles.ProcessInfo[Kratos.DELTA_TIME] = DT

    process = particle_inference_process.Factory(Kratos.Parameters("""{
        "Parameters": {
            "model_part_name" : "Particles",
            "model_settings"  : { "checkpoint_file" : "%s", "device" : "cpu" },
            "model_interface" : "tensor",
            "connectivity"    : { "type" : "radius", "radius" : 1.0 },
            "history_size"    : 1
        }
    }""" % checkpoint), kratos_model)

    reference = Simulate(x0, steps=DEPLOY_STEPS + 1)
    predicted = [x0.copy()]
    for step in range(1, DEPLOY_STEPS + 1):
        particles.ProcessInfo[Kratos.STEP] = step
        process.ExecuteFinalizeSolutionStep()
        predicted.append(numpy.array([[node.X, node.Y, node.Z]
                                      for node in particles.Nodes]))
    predicted = numpy.stack(predicted)

    errors = numpy.sqrt(((predicted - reference) ** 2).mean(axis=(1, 2)))
    drop = float(reference[0, :, 2].mean() - reference[-1, :, 2].mean())
    print(f"deployed cloud: final position rmse {errors[-1]:.2e} "
          f"over a mean drop of {drop:.2f} m in {DEPLOY_STEPS} steps")

    # ---- figures ----------------------------------------------------------
    figure, axis = pyplot.subplots(figsize=(6.6, 3.9))
    time = numpy.arange(DEPLOY_STEPS + 1) * DT
    axis.semilogy(time, numpy.maximum(errors, 1e-12))
    axis.set_xlabel("time [s]")
    axis.set_ylabel("position RMSE [m]")
    axis.set_title("Error growth of the integrated surrogate cloud")
    axis.grid(True, which="both", alpha=0.3)
    figure.tight_layout()
    figure.savefig(DATA / "particle_error.png", dpi=130)

    frames = []
    for step in range(0, DEPLOY_STEPS + 1, 2):
        fig = pyplot.figure(figsize=(6.4, 5.2))
        axis3d = fig.add_subplot(111, projection="3d")
        axis3d.scatter(*reference[step].T, s=22, c="#7f8c8d", alpha=0.55,
                       label="closed-form reference")
        axis3d.scatter(*predicted[step].T, s=14, c="#c0392b",
                       label="ParticleInferenceProcess")
        axis3d.set_xlim(0, 4), axis3d.set_ylim(0, 4), axis3d.set_zlim(-2, 5.5)
        axis3d.set_title(f"t = {step * DT:.2f} s")
        axis3d.legend(loc="upper right", fontsize=8)
        fig.tight_layout()
        fig.canvas.draw()
        frames.append(Image.fromarray(
            numpy.asarray(fig.canvas.buffer_rgba())[:, :, :3]))
        pyplot.close(fig)
    frames[0].save(DATA / "particles.gif", save_all=True,
                   append_images=frames[1:], duration=140, loop=0)

    with open(OUTPUT / "particle_summary.json", "w") as handle:
        json.dump({"final_rmse": float(errors[-1]), "mean_drop": drop,
                   "final_loss": history[-1]}, handle, indent=1)
    print(f"figures: {DATA / 'particles.gif'}, {DATA / 'particle_error.png'}")


if __name__ == "__main__":
    main()
