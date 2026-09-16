"""The learned force field rolled out autoregressively in the periodic box.

Script 01 trained the force field and graded it on single frames. This one
hands it the loop: a Kratos node cloud is seeded with two true velocity
states and then stepped by ParticleInferenceProcess alone, which every step
rebuilds the minimum-image radius graph from the CURRENT node positions,
standardizes the velocity history with the card, runs the model,
de-normalizes the acceleration and integrates it twice - into velocities
and then into node positions. Nothing else touches the cloud.

How to grade such a rollout honestly is the interesting part. Molecular
dynamics is chaotic: two trajectories differing by 1e-8 separate
exponentially, so position error against the reference says almost nothing
about the force field after a few dozen steps, and a case that reported it
as the headline number would be measuring Lyapunov time, not learning. What
IS meaningful is whether the model still predicts the right forces for the
configurations it has itself wandered into. So at every step the reference
forces are recomputed AT THE SURROGATE'S OWN POSITIONS and compared with
what the model said, against the mean-force predictor at those same
positions. The structural observables - total energy and the radial
distribution function - are reported alongside, because a force field that
tracked forces while destroying the liquid's structure would not be useful.

The reproducible claim (everything seeded): averaged over the rollout, the
model's force error stays below the mean-force predictor's.

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
# The rollout deliberately runs past the window the model was trained in
# (script 01 trains on 20-step trajectories). The figure shows what that
# costs: as the cloud melts into configurations unlike its training data,
# close pairs appear and the force error climbs toward the baseline. The
# asserted claim is therefore made over the trained-in regime, and the
# degradation beyond it is reported rather than cropped out.
ROLLOUT_STEPS = 30
TRAINED_STEPS = 16         # rollout steps still inside the training window
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
        seen = ReadNodes(model_part)
        process.ExecuteFinalizeSolutionStep()
        if step == HISTORY:   # the first step that predicts and integrates
            _Score(model_part, seen, box, record)

    for _ in range(ROLLOUT_STEPS):
        step += 1
        model_part.ProcessInfo[Kratos.STEP] = step
        seen = ReadNodes(model_part)          # what the model is about to see
        process.ExecuteFinalizeSolutionStep()  # predict, then integrate v and x
        _Score(model_part, seen, box, record)
    return record


def _Score(model_part, seen, box, record):
    """Grades the prediction the process just made at the positions it saw."""
    predicted = ReadNodes(model_part, Kratos.ACCELERATION)
    reference, _ = lj.ComputeForcesAndPotential(seen, box)   # mass 1: force = acceleration
    record["force_rmse"].append(
        float(numpy.sqrt(numpy.mean((predicted - reference) ** 2))))
    record["baseline"].append(float(numpy.sqrt(numpy.mean(
        (reference - reference.mean(axis=0)) ** 2))))
    record["energy"].append(float(lj.ComputeEnergy(
        seen, ReadNodes(model_part, Kratos.VELOCITY), box)))
    record["frames"].append(seen)


def Render(record, reference_energies, reference_frames, box):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    steps = numpy.arange(len(record["force_rmse"]))
    figure, axes = plt.subplots(1, 3, figsize=(13.0, 3.6), constrained_layout=True)

    axes[0].plot(steps, record["force_rmse"], label="learned force field")
    axes[0].plot(steps, record["baseline"], "--", color="#7f8c8d",
                 label="mean-force predictor")
    axes[0].axvspan(0, TRAINED_STEPS, color="#2ecc71", alpha=0.12)
    axes[0].axvline(TRAINED_STEPS, color="#27ae60", lw=1)
    axes[0].text(0.5, 0.96, "trained-in window", transform=axes[0].transAxes,
                 ha="center", va="top", fontsize=8, color="#1e8449")
    axes[0].set_xlabel("rollout step"), axes[0].set_ylabel("force RMSE")
    axes[0].set_title("graded at the surrogate's own positions")
    axes[0].legend(fontsize=8), axes[0].grid(alpha=0.3)

    axes[1].plot(steps, record["energy"], label="surrogate rollout")
    axes[1].plot(steps, reference_energies[:len(steps)], "--", color="#7f8c8d",
                 label="velocity Verlet")
    axes[1].set_xlabel("rollout step"), axes[1].set_ylabel("total energy")
    axes[1].set_title("energy is not conserved by construction")
    axes[1].legend(fontsize=8), axes[1].grid(alpha=0.3)

    centers, surrogate_g = RadialDistribution(record["frames"], box)
    _, reference_g = RadialDistribution(reference_frames, box)
    axes[2].plot(centers, surrogate_g, label="surrogate rollout")
    axes[2].plot(centers, reference_g, "--", color="#7f8c8d", label="reference")
    axes[2].set_xlabel("r"), axes[2].set_ylabel("g(r)")
    axes[2].set_title("radial distribution function")
    axes[2].legend(fontsize=8), axes[2].grid(alpha=0.3)

    figure.suptitle("A learned Lennard-Jones force field driving a Kratos node cloud")
    figure.savefig(DATA / "lj_rollout.png", dpi=130)
    return centers, surrogate_g, reference_g


def RenderBox(record, reference_frames, box, potentials):
    """The periodic box, atoms wrapped back in and coloured by potential."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    frames = []
    limits = (float(potentials.min()), float(potentials.max()))
    for index in range(0, len(record["frames"]), 2):
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

    # The boundary is set by the TRAINING window, not by where the curves
    # happen to cross: script 01 trains on 20-step trajectories, so only the
    # first TRAINED_STEPS of this rollout are configurations of the kind the
    # model ever saw. Both numbers are reported; only the first is asserted.
    trained = slice(0, TRAINED_STEPS)
    mean_error = float(numpy.mean(record["force_rmse"][trained]))
    mean_baseline = float(numpy.mean(record["baseline"][trained]))
    full_error = float(numpy.mean(record["force_rmse"]))
    full_baseline = float(numpy.mean(record["baseline"]))
    drift = abs(record["energy"][-1] - record["energy"][0]) / abs(record["energy"][0])
    reference_drift = abs(reference_energies[len(record["energy"]) - 1]
                          - reference_energies[0]) / abs(reference_energies[0])
    displacement = float(numpy.abs(
        record["frames"][-1] - reference_frames[len(record["frames"]) - 1]).max())
    print(f"[eval] trained-in window (first {TRAINED_STEPS} steps): force RMSE "
          f"{mean_error:.4f} against the mean-force predictor's {mean_baseline:.4f} "
          f"({mean_baseline / mean_error:.2f}x)")
    print(f"[eval] whole {ROLLOUT_STEPS}-step rollout: {full_error:.4f} against "
          f"{full_baseline:.4f} ({full_baseline / full_error:.2f}x) - reported, "
          f"not asserted: past the training window the cloud melts and the "
          f"repulsive core takes over")
    print(f"[eval] energy drift over the rollout: surrogate {drift:.2e}, "
          f"symplectic reference {reference_drift:.2e}")
    print(f"[eval] largest position difference from the reference: {displacement:.3f} "
          f"(chaos, not a failure of the force field)")

    potentials = numpy.concatenate([
        lj.ComputeForcesAndPotential(p, box)[1] for p in record["frames"][::2]])
    centers, surrogate_g, reference_g = Render(
        record, reference_energies, reference_frames, box)
    RenderBox(record, reference_frames, box, potentials)

    with open(OUTPUT / "rollout_summary.json", "w") as handle:
        json.dump({"trained_in_rmse": mean_error, "trained_in_baseline": mean_baseline,
                   "full_rollout_rmse": full_error, "full_rollout_baseline": full_baseline,
                   "trained_steps": TRAINED_STEPS,
                   "energy_drift": drift, "reference_energy_drift": reference_drift,
                   "max_position_difference": displacement,
                   "steps": len(record["force_rmse"])}, handle, indent=1)

    # the reproducible claim: along its OWN trajectory - the configurations
    # it wandered into, not the reference's - the force field beats
    # predicting each frame's mean force, for as long as those
    # configurations resemble its training data. Position error is
    # deliberately not the claim: MD is chaotic and that number measures
    # Lyapunov time, not the quality of the force field.
    assert mean_error < mean_baseline, (mean_error, mean_baseline)
    print("[done] figures at data/lj_rollout.png and data/lj_box.gif")
