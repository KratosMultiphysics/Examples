"""Stage 1 - transient thermo-mechanical solves, then temporal training.

Runs the coupled cooling case at several cooling rates, collects per-step
states (displacements + temperature per node), and trains an
autoregressive surrogate two ways:

* **single-step**: windows of the last H states -> next state, the
  standard supervised setup;
* **+ BPTT** (TrainAutoregressive): the same model then fine-tuned through
  its own rollout - gradients flow through the model feeding itself, which
  is what controls compounding error at deployment.

The comparison is evaluated on a held-out cooling rate the model never
saw, as autoregressive error growth over the rollout.

Run time: ~2 minutes (4 transient coupled solves + training).
"""

import copy
import json
import pathlib

import numpy
import torch
from matplotlib import pyplot

import KratosMultiphysics as Kratos
from KratosMultiphysics.PhysicsNeMoApplication.training import temporal_training
from KratosMultiphysics.PhysicsNeMoApplication.training import training_utils
from KratosMultiphysics.PhysicsNeMoApplication.training import rollout_utils
import sintering_case
import surrogate_model

OUTPUT = pathlib.Path("output")
DATA = pathlib.Path("..") / "data"

TRAIN_RATES = [1200.0, 1600.0, 2000.0]
HELD_OUT_RATE = 1400.0
DIVISIONS = 10
TIME_STEP = 0.0125
END_TIME = 0.5          # 40 steps
HISTORY = surrogate_model.HISTORY


def CollectState(model_part):
    """(N, 3) per-node state: displacement x/y and temperature."""
    return [[node.GetSolutionStepValue(Kratos.DISPLACEMENT_X),
             node.GetSolutionStepValue(Kratos.DISPLACEMENT_Y),
             node.GetSolutionStepValue(Kratos.TEMPERATURE)]
            for node in model_part.Nodes]


def RunTrajectory(cooling_rate: float):
    model = Kratos.Model()
    analysis = sintering_case.CreateSinteringAnalysis(
        model, divisions=DIVISIONS, cooling_rate=cooling_rate,
        time_step=TIME_STEP, end_time=END_TIME)
    states = sintering_case.RunTransientAnalysis(analysis, collect=CollectState)
    return states  # (T, N, 3)




def main():
    OUTPUT.mkdir(exist_ok=True)
    DATA.mkdir(exist_ok=True)
    Kratos.Logger.GetDefaultOutput().SetSeverity(Kratos.Logger.Severity.WARNING)

    # ---- the ground truth: coupled transient solves -----------------------
    trajectories = []
    for rate in TRAIN_RATES:
        states = RunTrajectory(rate)
        trajectories.append(states)
        shrink = states[-1, :, :2]
        print(f"  rate {rate:6.0f}: {states.shape[0]} steps, "
              f"final max |displacement| {numpy.abs(shrink).max():.2e}")
    held_out = RunTrajectory(HELD_OUT_RATE)

    # trajectories stay (T, N, 3): the window convention is per-node, so the
    # same model transfers between meshes. Normalization is PER CHANNEL:
    # temperatures are O(1000) and displacements O(0.1), so one global scale
    # would push the displacement channels to noise level - the loss would
    # optimize temperature only and the rollout displacement would be junk
    scale = numpy.abs(numpy.stack(trajectories)).max(axis=(0, 1, 2))  # (3,)
    train_scaled = [t / scale for t in trajectories]
    test_scaled = held_out / scale
    numpy.savez(OUTPUT / "trajectories.npz",
                train=numpy.stack(trajectories), held_out=held_out, scale=scale,
                train_rates=TRAIN_RATES, held_out_rate=HELD_OUT_RATE)

    # ---- single-step training ---------------------------------------------
    dataset = temporal_training.CreateTrajectoryWindowDataset(
        train_scaled, Kratos.Parameters(
            '{"scheme": "single_step", "history_size": %d}' % HISTORY))
    print(f"{len(dataset)} single-step windows from {len(TRAIN_RATES)} trajectories")

    # device "cpu" on purpose: a per-node MLP this small is dominated by
    # kernel-launch overhead on a GPU and trains several times faster on CPU
    single_step = surrogate_model.Create(0)
    single_history = training_utils.TrainModel(single_step, dataset, Kratos.Parameters("""{
        "epochs"        : 600,
        "batch_size"    : 16,
        "learning_rate" : 1.5e-3,
        "device"        : "cpu",
        "echo_interval" : 200,
        "seed"          : 0
    }"""))

    # ---- BPTT fine-tuning through the model's own rollout -----------------
    bptt = copy.deepcopy(single_step)
    # the fine-tune must not destroy an already-converged single-step
    # model, so the learning rate is two orders of magnitude below the
    # single-step one: the rollout objective only nudges the weights
    # against compounding error
    bptt_history = temporal_training.TrainAutoregressive(bptt, train_scaled, Kratos.Parameters("""{
        "epochs"                 : 120,
        "rollout_steps"          : 24,
        "history_size"           : %d,
        "learning_rate"          : 2e-5,
        "gradient_checkpointing" : false,
        "device"                 : "cpu",
        "echo_interval"          : 40,
        "seed"                   : 0
    }""" % HISTORY))
    print(f"single-step loss {single_history[-1]:.3e}; "
          f"BPTT rollout loss {bptt_history[-1]:.3e}")

    # ---- error growth on the held-out cooling rate ------------------------
    _, single_errors = rollout_utils.EvaluateRollout(
        single_step.cpu(), test_scaled, history_size=HISTORY)
    _, bptt_errors = rollout_utils.EvaluateRollout(
        bptt.cpu(), test_scaled, history_size=HISTORY)

    torch.save(single_step.state_dict(), OUTPUT / "single_step.pt")
    torch.save(bptt.state_dict(), OUTPUT / "bptt.pt")

    figure, axes = pyplot.subplots(1, 2, figsize=(11.5, 4.0))
    axes[0].semilogy(single_history, label="single-step (600 epochs)")
    offset = numpy.arange(len(bptt_history)) + len(single_history)
    axes[0].semilogy(offset, bptt_history, label="+ BPTT fine-tune (120 epochs)")
    axes[0].set_xlabel("epoch")
    axes[0].set_ylabel("loss")
    axes[0].set_title("Training")
    axes[0].legend()
    axes[0].grid(True, which="both", alpha=0.3)

    axes[1].semilogy(single_errors, label="single-step training", linewidth=1.7)
    axes[1].semilogy(bptt_errors, label="+ BPTT", linewidth=1.7)
    axes[1].set_xlabel("rollout step (held-out cooling rate)")
    axes[1].set_ylabel("RMS error (normalized)")
    axes[1].set_title("Autoregressive error growth, unseen schedule")
    axes[1].legend()
    axes[1].grid(True, which="both", alpha=0.3)
    figure.tight_layout()
    figure.savefig(DATA / "training_and_error_growth.png", dpi=130)

    with open(OUTPUT / "training_summary.json", "w") as handle:
        json.dump({
            "single_step_mean_rollout_error": float(single_errors.mean()),
            "bptt_mean_rollout_error": float(bptt_errors.mean()),
            "single_step_final_error": float(single_errors[-1]),
            "bptt_final_error": float(bptt_errors[-1]),
        }, handle, indent=1)
    print(f"mean rollout error: single-step {single_errors.mean():.4f}, "
          f"BPTT {bptt_errors.mean():.4f}")
    print(f"figure : {DATA / 'training_and_error_growth.png'}")


if __name__ == "__main__":
    main()
