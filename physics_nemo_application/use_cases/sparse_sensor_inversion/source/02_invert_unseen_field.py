"""Stage 2 - what can ten sensors tell you about the whole field?

An unseen case is solved, ten sensor pixels are read from it, and the
trained conditional diffusion model draws an ensemble of full fields
consistent with those readings (diffusion_utils.GenerateEnsemble - the
same sampler the diffusion inference process uses). The ensemble mean is
the reconstruction; the per-pixel ensemble std is the INVERSION
UNCERTAINTY, and its signature is the point of the example: the std dips
at the sensor positions and grows between them - the model knows where
it has been told the answer.

The sweep re-inverts the same field with 3..24 sensors (the model
trained on random 5..15-sensor masks), averaging THREE random layouts per
count - a single sensor layout is noisy (an unlucky placement at a given
count can outscore a lucky one at a higher count), and the trend is the
point, not any one draw.

Run time: ~2 minutes (ensembles are 16 samples x 18 EDM steps on CPU).
"""

import json
import pathlib

import numpy
from matplotlib import pyplot

import KratosMultiphysics as Kratos
from KratosMultiphysics.PhysicsNeMoApplication.training import diffusion_utils
from KratosMultiphysics.PhysicsNeMoApplication.deployment import model_registry
import importlib
stage1 = importlib.import_module("01_train_inversion")

OUTPUT = pathlib.Path("output")
DATA = pathlib.Path("..") / "data"

UNSEEN = {"conductivity": 1.3, "source_amplitude": 1.25, "source_center": (0.58, 0.42)}
SENSOR_COUNT = 10
SWEEP = (3, 5, 8, 10, 15, 20, 24)


def Ensemble(denoiser, condition, num_samples=16):
    return diffusion_utils.GenerateEnsemble(
        denoiser, condition, Kratos.Parameters("""{
            "num_samples" : %d, "num_steps" : 18, "seed" : 0
        }""" % num_samples))


def main():
    OUTPUT.mkdir(exist_ok=True)
    DATA.mkdir(exist_ok=True)
    Kratos.Logger.GetDefaultOutput().SetSeverity(Kratos.Logger.Severity.WARNING)

    truth = stage1.FieldGrid(UNSEEN)
    denoiser, _ = model_registry.LoadModel(Kratos.Parameters("""{
        "checkpoint_file" : "output/sensor_inversion.mdlus",
        "checkpoint_type" : "physicsnemo",
        "device"          : "cpu"
    }"""))

    rng = numpy.random.default_rng(3)
    condition = stage1.SensorCondition(truth, rng, count=SENSOR_COUNT)
    ensemble = Ensemble(denoiser, condition)[:, 0]
    mean, std = ensemble.mean(axis=0), ensemble.std(axis=0)
    rmse = float(numpy.sqrt(((mean - truth) ** 2).mean()))
    sensor_rows, sensor_cols = numpy.nonzero(condition[1])
    std_at_sensors = float(std[sensor_rows, sensor_cols].mean())
    std_away = float(std[condition[1] == 0].mean())
    print(f"{SENSOR_COUNT} sensors: reconstruction RMSE {rmse:.3f} "
          f"(field max {truth.max():.2f}); std at sensors {std_at_sensors:.3f} "
          f"vs {std_away:.3f} away")

    # ---- the reconstruction figure ----------------------------------------
    figure, axes = pyplot.subplots(1, 4, figsize=(14.4, 3.6))
    limits = dict(vmin=0.0, vmax=float(truth.max()))
    panels = [(truth, "truth (unseen solve)", "inferno", limits),
              (mean, "ensemble mean (16 draws)", "inferno", limits),
              (numpy.abs(mean - truth), "absolute error", "viridis", {}),
              (std, "ensemble std = inversion uncertainty", "viridis", {})]
    for axis, (plane, title, cmap, kwargs) in zip(axes, panels):
        plot = axis.imshow(plane.T, origin="lower", cmap=cmap, **kwargs)
        figure.colorbar(plot, ax=axis, shrink=0.85)
        axis.scatter(sensor_rows, sensor_cols, s=26, facecolors="none",
                     edgecolors="cyan", linewidths=1.1)
        axis.set_title(title, fontsize=10)
        axis.set_xticks([])
        axis.set_yticks([])
    figure.suptitle(f"Field inversion from {SENSOR_COUNT} sensors (circled)")
    figure.tight_layout()
    figure.savefig(DATA / "sensor_inversion.png", dpi=130)

    # ---- the sensor-count sweep (averaged over layouts) --------------------
    sweep_rng = numpy.random.default_rng(11)
    sweep_rmse, sweep_std = [], []
    for count in SWEEP:
        layout_rmse, layout_std = [], []
        for _ in range(3):
            sweep_condition = stage1.SensorCondition(truth, sweep_rng, count=count)
            members = Ensemble(denoiser, sweep_condition, num_samples=8)[:, 0]
            layout_rmse.append(float(numpy.sqrt(((members.mean(axis=0) - truth) ** 2).mean())))
            layout_std.append(float(members.std(axis=0).mean()))
        sweep_rmse.append(float(numpy.mean(layout_rmse)))
        sweep_std.append(float(numpy.mean(layout_std)))
        print(f"  {count:2d} sensors: RMSE {sweep_rmse[-1]:.3f} (+/-{numpy.std(layout_rmse):.3f}), "
              f"mean std {sweep_std[-1]:.3f}")

    figure, axis = pyplot.subplots(figsize=(6.8, 4.0))
    axis.plot(SWEEP, sweep_rmse, "s-", label="reconstruction RMSE")
    axis.plot(SWEEP, sweep_std, "o-", label="mean ensemble std")
    axis.axvspan(*stage1.SENSOR_RANGE, alpha=0.10, color="green")
    axis.text(sum(stage1.SENSOR_RANGE) / 2, max(sweep_rmse) * 0.95,
              "training sensor range", ha="center", fontsize=9, color="green")
    axis.set_xlabel("number of sensors")
    axis.set_ylabel("scaled temperature units")
    axis.set_title("More sensors, tighter inversion")
    axis.legend()
    axis.grid(True, alpha=0.3)
    figure.tight_layout()
    figure.savefig(DATA / "sensor_sweep.png", dpi=130)

    with open(OUTPUT / "inversion_summary.json", "w") as handle:
        json.dump({"unseen": {k: v for k, v in UNSEEN.items() if k != "source_center"}
                   | {"source_center": list(UNSEEN["source_center"])},
                   "rmse": rmse, "field_max": float(truth.max()),
                   "std_at_sensors": std_at_sensors, "std_away": std_away,
                   "sweep": {"counts": list(SWEEP), "rmse": sweep_rmse,
                             "std": sweep_std}}, handle, indent=1)
    print(f"figures: {DATA / 'sensor_inversion.png'}, {DATA / 'sensor_sweep.png'}")


if __name__ == "__main__":
    main()
