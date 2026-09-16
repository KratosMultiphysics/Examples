"""The learned force field rolled out autoregressively in the periodic box.

Script 01 trained the force field and graded it on frames of trajectories
it had never seen. This one hands it the loop: a Kratos node cloud is
seeded with two true velocity states and then stepped by
ParticleInferenceProcess alone, which every step rebuilds the minimum-image
radius graph from the CURRENT node positions, standardizes the velocity
history with the card, runs the model, de-normalizes the acceleration and
integrates it twice - into velocities and then into node positions.
Nothing else touches the cloud.

How such a rollout is graded honestly is half the point. Molecular dynamics
is chaotic, so position error against the reference eventually measures
Lyapunov time rather than the quality of a force field. What stays
meaningful is whether the model predicts the right forces for the
configurations IT HAS ITSELF WANDERED INTO, so every step recomputes the
reference forces at the surrogate's own positions and compares them with
the mean-force predictor at those same configurations.

AND THE ROLLOUT EVENTUALLY DIVERGES, which this case shows rather than
crops. Measured over 80 steps, the mean force per 10-step block runs
0.19, 0.36, 0.54, then 3.2, 33, 409, 9185 and 6.1e5: past roughly thirty
steps the self-driven trajectory goes numerically unstable, atoms are
driven together, and the r^-13 core does the rest. Note what happens to
the comparison there - the ratio to the baseline returns to almost exactly
1.00, not because the model has become as good as predicting the mean
force, but because both numbers are saturated by the same astronomically
large reference forces. A metric can keep reporting a healthy-looking
value long after the thing it measures has stopped meaning anything. This
is the ordinary failure mode of an autoregressive learned force field with
no thermostat or stability mechanism, and it is why the claim below is
made over a stated deployment horizon rather than "forever".

The reproducible claim (everything seeded): over the claimed horizon of
CLAIM_STEPS steps, the force field's error stays below the mean-force
predictor's. The full-length behaviour is plotted on a log axis beside it.

Run from this directory:  python3 02_rollout_in_the_box.py
Outputs: ../data/lj_rollout.png, ../data/lj_box.gif
"""

import json
import pathlib

import numpy
from PIL import Image

import KratosMultiphysics as Kratos
import KratosMultiphysics.PhysicsNeMoApplication  # registers the application  # noqa: F401
from KratosMultiphysics.PhysicsNeMoApplication.processes.inference import (
    particle_inference_process)
from KratosMultiphysics.PhysicsNeMoApplication.utilities import lennard_jones_reference as lj

HERE = pathlib.Path(__file__).parent
DATA = HERE.parent / "data"
OUTPUT = HERE / "output"

ATOMS_PER_SIDE = 4
DT = 0.005
HISTORY = 2
HELD_OUT_SEED = 8          # one of 01's held-out trajectories
ROLLOUT_STEPS = 60         # long enough to show the instability
CLAIM_STEPS = 30           # the deployment horizon this case claims
STEPS = HISTORY + ROLLOUT_STEPS + 2
CONNECTIVITY = '{"type": "radius", "radius": 2.5, "box_size": [6.0], "backend": "auto"}'


def CreateAtomCloud(model, positions):
    """A bare Kratos node cloud - no elements, no mesh, just atoms."""
    model_part = model.CreateModelPart("Atoms")
    for variable in (Kratos.VELOCITY, Kratos.ACCELERATION, Kratos.DISPLACEMENT):
        model_part.AddNodalSolutionStepVariable(variable)
    model_part.SetBufferSize(2)
    for index, xyz in enumerate(positions):
        model_part.CreateNewNode(index + 1, *[float(c) for c in xyz])
    model_part.ProcessInfo[Kratos.DELTA_TIME] = DT
    return model_part


def CreateProcess(model, checkpoint):
    return particle_inference_process.Factory(Kratos.Parameters('''{
        "Parameters": {
            "model_part_name" : "Atoms",
            "model_settings"  : { "checkpoint_file" : "%s",
                                  "checkpoint_type" : "physicsnemo",
                                  "device" : "cpu" },
            "model_interface" : "meshgraphnet",
            "connectivity"    : %s,
            "history_size"    : %d
        }
    }''' % (checkpoint, CONNECTIVITY, HISTORY)), model)


def ReadNodes(model_part, variable=None):
    if variable is None:
        return numpy.array([[node.X, node.Y, node.Z] for node in model_part.Nodes])
    return numpy.array([node.GetSolutionStepValue(variable) for node in model_part.Nodes])


def RadialDistribution(frames, box, bins=40, maximum=3.0):
    """g(r) from minimum-image pair distances, averaged over frames."""
    box = numpy.asarray(box, dtype=float)
    edges = numpy.linspace(0.0, maximum, bins + 1)
    counts = numpy.zeros(bins)
    atoms = frames[0].shape[0]
    for positions in frames:
        delta = positions[:, None, :] - positions[None, :, :]
        delta = lj.MinimumImage(delta.reshape(-1, 3), box).reshape(atoms, atoms, 3)
        distance = numpy.linalg.norm(delta, axis=2)
        counts += numpy.histogram(distance[numpy.triu_indices(atoms, k=1)], bins=edges)[0]
    centers = 0.5 * (edges[1:] + edges[:-1])
    shell = (4.0 / 3.0) * numpy.pi * (edges[1:] ** 3 - edges[:-1] ** 3)
    density = atoms / float(numpy.prod(box))
    ideal = 0.5 * atoms * density * shell * len(frames)
    return centers, counts / numpy.maximum(ideal, 1e-12)


def Rollout(model_part, process, trajectory):
    """Seeds the history with two true states, then lets the process drive."""
    box = trajectory["box_size"]
    positions = trajectory["positions"]
    # the true window (v_{t-1}, v_t) by the same finite difference the
    # dataset used; the process makes no prediction until it holds
    # history_size states, so the first call only warms it up
    window = [(positions[HISTORY - 1] - positions[HISTORY - 2]) / DT,
              (positions[HISTORY] - positions[HISTORY - 1]) / DT]

    record = {"force_rmse": [], "baseline": [], "energy": [], "frames": []}
    step = 0
    for velocity in window:
        step += 1
        for row, node in enumerate(model_part.Nodes):
            node.SetSolutionStepValue(Kratos.VELOCITY, [float(c) for c in velocity[row]])
        model_part.ProcessInfo[Kratos.STEP] = step
        seen, seen_velocity = ReadNodes(model_part), ReadNodes(model_part, Kratos.VELOCITY)
        process.ExecuteFinalizeSolutionStep()
        if step == HISTORY:   # the first step that predicts and integrates
            _Score(model_part, seen, seen_velocity, box, record)

    for _ in range(ROLLOUT_STEPS):
        step += 1
        model_part.ProcessInfo[Kratos.STEP] = step
        # what the model is about to see, read BEFORE it integrates
        seen, seen_velocity = ReadNodes(model_part), ReadNodes(model_part, Kratos.VELOCITY)
        process.ExecuteFinalizeSolutionStep()
        _Score(model_part, seen, seen_velocity, box, record)
    return record


def _Score(model_part, seen, seen_velocity, box, record):
    """Grades the prediction the process just made at the positions it saw."""
    predicted = ReadNodes(model_part, Kratos.ACCELERATION)
    reference, _ = lj.ComputeForcesAndPotential(seen, box)   # mass 1: force = acceleration
    record["force_rmse"].append(
        float(numpy.sqrt(numpy.mean((predicted - reference) ** 2))))
    record["baseline"].append(float(numpy.sqrt(numpy.mean(
        (reference - reference.mean(axis=0)) ** 2))))
    record["energy"].append(float(lj.ComputeEnergy(seen, seen_velocity, box)))
    record["frames"].append(seen)


def Render(record, reference_energies, reference_frames, box):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    steps = numpy.arange(len(record["force_rmse"]))
    figure, axes = plt.subplots(1, 3, figsize=(13.2, 3.7), constrained_layout=True)

    axes[0].semilogy(steps, record["force_rmse"], label="learned force field")
    axes[0].semilogy(steps, record["baseline"], "--", color="#7f8c8d",
                     label="mean-force predictor")
    axes[0].axvline(CLAIM_STEPS, color="#27ae60", lw=1.2)
    axes[0].axvspan(0, CLAIM_STEPS, color="#2ecc71", alpha=0.10)
    axes[0].set_title(f"forces at the surrogate's own positions\n"
                      f"(green: the {CLAIM_STEPS}-step claimed horizon)", fontsize=9)
    axes[0].set_xlabel("rollout step"), axes[0].set_ylabel("force RMSE (log)")
    axes[0].legend(fontsize=8), axes[0].grid(alpha=0.3, which="both")

    claimed = slice(0, CLAIM_STEPS)
    axes[1].plot(steps[claimed], numpy.array(record["energy"])[claimed],
                 label="surrogate rollout")
    axes[1].plot(steps[claimed], reference_energies[:CLAIM_STEPS], "--",
                 color="#7f8c8d", label="velocity Verlet")
    axes[1].set_title("total energy over the claimed horizon", fontsize=9)
    axes[1].set_xlabel("rollout step"), axes[1].set_ylabel("total energy")
    axes[1].legend(fontsize=8), axes[1].grid(alpha=0.3)

    centers, surrogate_g = RadialDistribution(record["frames"][:CLAIM_STEPS], box)
    _, reference_g = RadialDistribution(reference_frames[:CLAIM_STEPS], box)
    axes[2].plot(centers, surrogate_g, label="surrogate rollout")
    axes[2].plot(centers, reference_g, "--", color="#7f8c8d", label="reference")
    axes[2].set_title("radial distribution over the claimed horizon", fontsize=9)
    axes[2].set_xlabel("r"), axes[2].set_ylabel("g(r)")
    axes[2].legend(fontsize=8), axes[2].grid(alpha=0.3)

    figure.suptitle("A learned Lennard-Jones force field driving a Kratos node cloud "
                    "- and where it stops working")
    figure.savefig(DATA / "lj_rollout.png", dpi=130)


def RenderBox(record, reference_frames, box):
    """The periodic box over the claimed horizon, atoms wrapped back in."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    potentials = numpy.concatenate([
        lj.ComputeForcesAndPotential(p, box)[1] for p in record["frames"][:CLAIM_STEPS]])
    limits = (float(potentials.min()), float(potentials.max()))
    frames = []
    for index in range(0, CLAIM_STEPS, 2):
        figure = plt.figure(figsize=(8.4, 4.4))
        for column, (positions, title) in enumerate((
                (reference_frames[index], "velocity Verlet"),
                (record["frames"][index], "ParticleInferenceProcess"))):
            wrapped = numpy.mod(positions, numpy.asarray(box, dtype=float))
            energy = lj.ComputeForcesAndPotential(positions, box)[1]
            axis = figure.add_subplot(1, 2, column + 1, projection="3d")
            axis.scatter(*wrapped.T, c=energy, cmap="coolwarm",
                         vmin=limits[0], vmax=limits[1], s=34, depthshade=False)
            axis.set_xlim(0, box[0]), axis.set_ylim(0, box[1]), axis.set_zlim(0, box[2])
            axis.set_xticks([]), axis.set_yticks([]), axis.set_zticks([])
            axis.set_title(f"{title}\nstep {index}", fontsize=9)
        figure.suptitle("atoms wrapped into the periodic box, coloured by potential energy",
                        fontsize=10)
        figure.canvas.draw()
        frames.append(Image.fromarray(numpy.asarray(figure.canvas.buffer_rgba())[:, :, :3]))
        plt.close(figure)
    frames[0].save(DATA / "lj_box.gif", save_all=True, append_images=frames[1:],
                   duration=160, loop=0)


if __name__ == "__main__":
    DATA.mkdir(exist_ok=True)
    OUTPUT.mkdir(exist_ok=True)
    Kratos.Logger.GetDefaultOutput().SetSeverity(Kratos.Logger.Severity.WARNING)

    checkpoint = OUTPUT / "lj_forces.mdlus"
    if not checkpoint.is_file():
        raise SystemExit("run 01_train_force_field.py first (it writes the checkpoint)")

    trajectory = lj.GenerateTrajectory(
        atoms_per_side=ATOMS_PER_SIDE, steps=STEPS, dt=DT, seed=HELD_OUT_SEED)
    box = trajectory["box_size"]
    print(f"[data] held-out trajectory (seed {HELD_OUT_SEED}): "
          f"{trajectory['positions'].shape[1]} atoms in a {box} box")

    model = Kratos.Model()
    model_part = CreateAtomCloud(model, trajectory["positions"][HISTORY])
    process = CreateProcess(model, checkpoint)
    record = Rollout(model_part, process, trajectory)

    reference_frames = trajectory["positions"][HISTORY:HISTORY + len(record["frames"])]
    reference_energies = [lj.ComputeEnergy(p, v, box) for p, v in zip(
        trajectory["positions"][HISTORY:], trajectory["velocities"][HISTORY:])]

    claimed = slice(0, CLAIM_STEPS)
    error = float(numpy.mean(record["force_rmse"][claimed]))
    baseline = float(numpy.mean(record["baseline"][claimed]))
    drift = abs(record["energy"][CLAIM_STEPS - 1] - record["energy"][0]) / abs(record["energy"][0])
    reference_drift = abs(reference_energies[CLAIM_STEPS - 1]
                          - reference_energies[0]) / abs(reference_energies[0])
    print(f"[eval] claimed horizon ({CLAIM_STEPS} steps): force RMSE {error:.4f} against the "
          f"mean-force predictor's {baseline:.4f} ({baseline / error:.2f}x)")
    print(f"[eval] energy drift there: surrogate {drift:.2e}, "
          f"symplectic reference {reference_drift:.2e} "
          f"({drift / reference_drift:.0f}x larger - the integrator is not symplectic)")

    # the instability, reported as the measured limitation it is
    blocks = [(a, float(numpy.mean(record["force_rmse"][a:a + 10])))
              for a in range(0, len(record["force_rmse"]), 10)]
    print("[eval] mean force error per 10-step block: "
          + ", ".join(f"{a}-{a + 9}: {v:.3g}" for a, v in blocks))
    print(f"[eval] beyond ~{CLAIM_STEPS} steps the self-driven rollout diverges; the ratio to "
          f"the baseline returns to ~1.00 only because both are saturated by the same "
          f"enormous reference forces")

    Render(record, reference_energies, reference_frames, box)
    RenderBox(record, reference_frames, box)

    with open(OUTPUT / "rollout_summary.json", "w") as handle:
        json.dump({"claim_steps": CLAIM_STEPS, "claimed_rmse": error,
                   "claimed_baseline": baseline, "rollout_steps": ROLLOUT_STEPS,
                   "energy_drift": drift, "reference_energy_drift": reference_drift,
                   "force_error_blocks": blocks}, handle, indent=1)

    # the reproducible claim: over the stated deployment horizon, along its
    # OWN trajectory - the configurations it wandered into, not the
    # reference's - the force field beats predicting each frame's mean
    # force. Beyond that horizon it diverges, which the figure shows.
    assert error < baseline, (error, baseline)
    print("[done] figures at data/lj_rollout.png and data/lj_box.gif")
