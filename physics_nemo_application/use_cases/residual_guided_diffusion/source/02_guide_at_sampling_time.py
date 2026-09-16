"""Steering a trained denoiser with sensors, and with the solver's own physics.

Script 01 trained an informative but incomplete prior: a diffusion model
conditioned on the heat-source field, so it knows WHERE the heat enters but
not how well the plate conducts it - the shape of the answer is determined,
its magnitude is not. This script steers that same checkpoint - no
retraining, no second model - two different ways, and compares both against
sampling it unguided:

* **`"data_consistency"`** pulls the samples toward ten sparse sensor
  readings. The classical inverse problem: some measurements, and a prior
  over plausible fields.
* **`"model_consistency"`** pulls them toward a differentiable forward
  operator, and the operator here is the EXACT DISCRETE FEM RESIDUAL of
  the case, assembled by Kratos through
  `MakeKratosResidualObservationOperator`. The observation is exactly
  zero - a field that solves the PDE has no residual - so this is the
  solver's own physics grading the generator at every sampling step.

Diffusion posterior sampling is what makes both possible on an
already-trained model: the guidance term enters the sampler's score, not
the training loss. The cost is a gradient through the model at every step.

STD_Y IS THE WHOLE BALLGAME, and the sweep below is in this case because
getting it wrong is silent in both directions. It is nominally the
observation noise level, but it also sets the guidance strength, which
scales as 1/(2 std_y^2). Measured here against a residual whose unguided
norm is 2.2e-2:

    std_y  1.0   0.3   0.1   0.03   0.01    0.003      0.001
    ratio  1.00x 1.01x 1.07x 1.84x  5.95x   blown up   raises

Too large and the term is simply off - at std_y = 1.0 the "guided" ensemble
matches the unguided one to four significant figures, which is easy to
mistake for guidance that works, because the comparison still passes a
naive `guided < unguided` test by a margin of 0.07 %. Too small and it
diverges. Note what sits between: at 0.003 the sampler produces FINITE
values whose residual is 1.2e+06, and nothing raises. The bridge's guard
catches non-finite output at 0.001, but there is a band just above it where
the numbers are finite and meaningless. Match std_y to the scale of the
thing being observed.

Two more contracts this exercises:

* the residual operator WRITES the trial field into the model part's DOFs
  while assembling, so `operator.Restore()` must follow every use; the
  script checks the temperature field comes back bit-identical.
* the residual is assembled in PHYSICAL units, which is why the operator is
  handed the card's "output_normalization": the prior was trained on fields
  scaled by ~96 to meet EDM's sigma_data, and a residual computed on
  EDM-scaled values would mean nothing.

The reproducible claim (everything seeded): each guided ensemble beats the
unguided one AT THE THING IT IS STEERED TOWARD - the sensor-guided mean is
closer to the readings, and the residual-guided mean has a materially lower
PDE residual.

Run from this directory:  python3 02_guide_at_sampling_time.py
Outputs: ../data/dps_guidance.png, ../data/dps_std_y_sweep.png
"""

import json
import pathlib
import sys

import numpy
import torch

import KratosMultiphysics as Kratos
import KratosMultiphysics.PhysicsNeMoApplication  # registers the application  # noqa: F401

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import thermal_plate  # noqa: E402

from KratosMultiphysics.PhysicsNeMoApplication.bridges import grid_bridge  # noqa: E402
from KratosMultiphysics.PhysicsNeMoApplication.deployment import model_registry  # noqa: E402
from KratosMultiphysics.PhysicsNeMoApplication.physics import (  # noqa: E402
    diffusion_residual_operator)
from KratosMultiphysics.PhysicsNeMoApplication.training import diffusion_utils  # noqa: E402

HERE = pathlib.Path(__file__).parent
DATA = HERE.parent / "data"
OUTPUT = HERE / "output"

GRID_SHAPE = (16, 16, 2)
SQUEEZE_AXIS = 2
BOUNDING_BOX = (numpy.zeros(3), numpy.array([1.0, 1.0, 0.0]))
DIVISIONS = 16
SENSORS = 10
NUM_SAMPLES, NUM_STEPS = 8, 18
SENSOR_STD_Y = 0.5          # the sensor readings' own scale
RESIDUAL_STD_Y = 0.01       # measured: the residual's scale, 5.95x at this value
SWEEP = (1.0, 0.3, 0.1, 0.03, 0.01, 0.003, 0.001)   # 0.001 is where the guard fires


def SampleGrid(model_part, variable):
    grid, _ = grid_bridge.SampleFieldsOnGrid(
        model_part, [(variable, "node_historical")], GRID_SHAPE, BOUNDING_BOX)
    return grid.mean(axis=SQUEEZE_AXIS + 1)[0]


def HeldOutCase():
    """A case the prior never saw (it trained on the first 68 of seed 7)."""
    case = thermal_plate.SampleCases(80, seed=7)[-1]
    model, model_part = thermal_plate.Solve(divisions=DIVISIONS, **case)
    return model, model_part, case


def MakeOperator(model_part, normalization):
    return diffusion_residual_operator.MakeKratosResidualObservationOperator(
        model_part, Kratos.Parameters("""{
            "residual_fields" : [ { "variable_name" : "TEMPERATURE",
                                    "data_location" : "node_historical" } ],
            "grid_shape"      : [16, 16, 2],
            "bounding_box"    : [],
            "squeeze_axis"    : 2
        }"""), output_normalization=normalization)


def Sample(model, condition, guidance, **kwargs):
    settings = Kratos.Parameters("""{
        "num_samples"        : %d,
        "num_steps"          : %d,
        "seed"               : 0,
        "denoiser_interface" : "edm",
        "output_channels"    : 1
    }""" % (NUM_SAMPLES, NUM_STEPS))
    settings.AddValue("guidance", Kratos.Parameters(guidance))
    return diffusion_utils.GenerateEnsemble(model, condition, settings, **kwargs)


def SensorMask(truth, seed=0):
    rng = numpy.random.default_rng(seed)
    mask = numpy.zeros_like(truth, dtype=bool)
    mask.reshape(-1)[rng.choice(truth.size, size=SENSORS, replace=False)] = True
    return truth * mask, mask


def Render(truth, scale, ensembles, summary, mask):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    names = list(ensembles)
    figure, axes = plt.subplots(2, len(names) + 1, figsize=(3.0 * (len(names) + 1), 5.6),
                                constrained_layout=True)
    image = axes[0][0].imshow(truth.T, origin="lower", cmap="inferno")
    figure.colorbar(image, ax=axes[0][0], shrink=0.8)
    axes[0][0].set_title("truth (held-out solve)", fontsize=9)
    rows, cols = numpy.where(mask)
    axes[0][0].scatter(rows, cols, s=12, facecolors="none", edgecolors="white", lw=0.8)
    axes[1][0].axis("off")
    axes[1][0].text(0.0, 0.5, "white circles:\nthe ten sensors\n\nresidual observation\nis exactly zero -\na solved field has\nno residual",
                    fontsize=8, va="center")

    # every |error| panel MUST share one colour scale: given its own, the
    # unguided map (up to 8e-3) and the residual-guided one (up to 1.2e-3)
    # look identical, and the figure would hide the factor of five it exists
    # to show
    error_max = max(float(numpy.abs(ensembles[n].mean(axis=0)[0] / scale - truth).max())
                    for n in names)
    for column, name in enumerate(names, start=1):
        mean = ensembles[name].mean(axis=0)[0] / scale
        image = axes[0][column].imshow(mean.T, origin="lower", cmap="inferno",
                                       vmin=truth.min(), vmax=truth.max())
        figure.colorbar(image, ax=axes[0][column], shrink=0.8)
        axes[0][column].set_title(f"{name}\nensemble mean", fontsize=9)
        image = axes[1][column].imshow(numpy.abs(mean - truth).T, origin="lower",
                                       cmap="viridis", vmin=0.0, vmax=error_max)
        figure.colorbar(image, ax=axes[1][column], shrink=0.8)
        axes[1][column].set_title(
            f"|error|  RMSE {summary[name]['rmse']:.2e}\n"
            f"sensors {summary[name]['sensor_mismatch']:.2e}  "
            f"residual {summary[name]['residual_norm']:.2e}", fontsize=8)
    for axis in axes.ravel():
        if axis.images:
            axis.set_xticks([]), axis.set_yticks([])
    figure.suptitle("Two ways to steer ONE trained denoiser at sampling time")
    figure.savefig(DATA / "dps_guidance.png", dpi=130)

    # the sweep: why std_y is the whole ballgame
    # Plotting the blown-up point to scale would stretch the y axis over
    # eight decades and flatten the entire USEFUL range (1.00x to 5.95x)
    # into a line at the bottom - the figure would hide exactly what it is
    # for. The working regime gets the axis; the blow-up is marked at the
    # top edge with its real value in the label.
    unguided = summary["unguided"]["residual_norm"]
    usable = [(s, r) for s, r in summary["_sweep"]
              if numpy.isfinite(r) and r <= 10.0 * unguided]
    blown = [(s, r) for s, r in summary["_sweep"]
             if not numpy.isfinite(r) or r > 10.0 * unguided]

    figure, axis = plt.subplots(figsize=(7.0, 4.2), constrained_layout=True)
    axis.loglog([s for s, _ in usable], [r for _, r in usable], "o-",
                label="residual-guided")
    axis.axhline(unguided, ls="--", color="#7f8c8d", label="unguided baseline")
    axis.axvline(RESIDUAL_STD_Y, color="#27ae60", lw=1.2,
                 label=f"chosen std_y = {RESIDUAL_STD_Y} ({unguided / dict(usable)[RESIDUAL_STD_Y]:.2f}x)")
    top = 3.0 * unguided
    for std_y, value in blown:
        axis.plot([std_y], [top], "v", color="#c0392b", markersize=9)
        label = ("raised" if not numpy.isfinite(value)
                 else f"finite, and meaningless\n(residual {value:.1e})")
        axis.annotate(label, (std_y, top), fontsize=8, color="#c0392b",
                      xytext=(8, -6), textcoords="offset points")
    axis.set_ylim(top=top * 1.6)
    axis.set_xlabel("std_y   (guidance strength goes as 1/(2 std_y²))")
    axis.set_ylabel("PDE residual norm of the ensemble mean")
    axis.set_title("Too large and the term is simply off; too small and it blows up\n"
                   "(the blown-up point is marked, not plotted to scale)", fontsize=9)
    axis.grid(alpha=0.3, which="both"), axis.legend(fontsize=8, loc="lower right")
    figure.savefig(DATA / "dps_std_y_sweep.png", dpi=130)


if __name__ == "__main__":
    DATA.mkdir(exist_ok=True)
    OUTPUT.mkdir(exist_ok=True)
    Kratos.Logger.GetDefaultOutput().SetSeverity(Kratos.Logger.Severity.WARNING)

    checkpoint = OUTPUT / "thermal_prior.mdlus"
    if not checkpoint.is_file():
        raise SystemExit("run 01_train_prior.py first (it writes the prior)")
    model_settings = Kratos.Parameters("""{
        "checkpoint_file" : "%s", "checkpoint_type" : "physicsnemo", "device" : "cpu"
    }""" % checkpoint)
    # LoadModel returns (model, device) - binding the tuple as the model
    # fails later and obscurely, inside the sampler
    model, _device = model_registry.LoadModel(model_settings.Clone())
    normalization = model_registry.LoadOutputNormalization(model_settings.Clone())

    kratos_model, model_part, case = HeldOutCase()
    truth = SampleGrid(model_part, "TEMPERATURE")
    condition = SampleGrid(model_part, "HEAT_FLUX")[None]
    scale = json.loads((OUTPUT / "prior_summary.json").read_text())["scale"]
    print(f"[data] held-out case: T max {truth.max():.4e}, prior scale {scale:.1f}")

    observation, mask = SensorMask(truth * scale)
    operator = MakeOperator(model_part, normalization)
    residual_observation = operator.observation.numpy()[0]
    print(f"[data] residual observation is zero by construction: "
          f"|y| max {numpy.abs(residual_observation).max():.1e}")

    print("[eval] sampling three ensembles from the SAME checkpoint")
    ensembles = {
        "unguided": Sample(model, condition, '{"type": "none"}'),
        # the observation and mask need the CHANNEL axis the latent has
        "sensor-guided": Sample(
            model, condition,
            '{"type": "data_consistency", "std_y": %g}' % SENSOR_STD_Y,
            observation=observation[None], mask=mask[None]),
    }
    operator.Restore()
    ensembles["residual-guided"] = Sample(
        model, condition,
        '{"type": "model_consistency", "std_y": %g}' % RESIDUAL_STD_Y,
        observation=residual_observation, observation_operator=operator)
    operator.Restore()

    def ResidualNorm(ensemble):
        value = float(operator(torch.tensor(ensemble)).norm(dim=1).mean())
        operator.Restore()
        return value

    summary = {}
    for name, ensemble in ensembles.items():
        mean = ensemble.mean(axis=0)[0]
        summary[name] = {
            "sensor_mismatch": float(numpy.sqrt(numpy.mean(
                (mean[mask] - (truth * scale)[mask]) ** 2))),
            "residual_norm": ResidualNorm(ensemble),
            "rmse": float(numpy.sqrt(numpy.mean((mean / scale - truth) ** 2))),
        }
        print(f"[eval] {name:<16} sensors {summary[name]['sensor_mismatch']:.4e}  "
              f"residual {summary[name]['residual_norm']:.4e}  "
              f"field RMSE {summary[name]['rmse']:.4e}")

    print("[eval] sweeping std_y - the term is off when it is too large and "
          "diverges when it is too small")
    sweep = []
    for std_y in SWEEP:
        try:
            ensemble = Sample(model, condition,
                              '{"type": "model_consistency", "std_y": %g}' % std_y,
                              observation=residual_observation,
                              observation_operator=operator)
            value = ResidualNorm(ensemble)
        except ValueError as error:
            value = float("nan")
            print(f"[eval]   std_y {std_y:<8g} raised: {str(error)[:60]}")
        finally:
            # The operator WRITES into the model part to evaluate the
            # residual, and `Restore` puts it back. On the successful
            # path `ResidualNorm` restores - but when the sampler raises,
            # the exception escapes before any restore runs and leaves
            # the model part silently modified. The intactness check at
            # the end of this script is what caught that, so the restore
            # belongs in a `finally`, not after the call.
            operator.Restore()
        sweep.append((std_y, value))
        if numpy.isfinite(value):
            ratio = summary["unguided"]["residual_norm"] / max(value, 1e-30)
            flag = "  <- finite, and meaningless" if ratio < 0.1 else ""
            print(f"[eval]   std_y {std_y:<8g} residual {value:.4e}  {ratio:5.2f}x{flag}")
    summary["_sweep"] = sweep

    after = SampleGrid(model_part, "TEMPERATURE")
    print(f"[eval] model part intact after guided sampling: "
          f"{numpy.allclose(after, truth, atol=1e-12)}")

    Render(truth, scale, ensembles, summary, mask)
    with open(OUTPUT / "guidance_summary.json", "w") as handle:
        json.dump({k: v for k, v in summary.items() if k != "_sweep"}
                  | {"sweep": [[s, r] for s, r in sweep]}, handle, indent=1)

    # Each guided ensemble must beat the unguided one AT THE THING IT IS
    # STEERED TOWARD, and by a MARGIN: a bare `<` passes on a 0.07 %
    # difference, which is what an effectively-disabled guidance term
    # produces. Measured margins here are ~1.7x and ~6x.
    sensor_gain = (summary["unguided"]["sensor_mismatch"]
                   / summary["sensor-guided"]["sensor_mismatch"])
    residual_gain = (summary["unguided"]["residual_norm"]
                     / summary["residual-guided"]["residual_norm"])
    print(f"[eval] margins: sensors {sensor_gain:.2f}x, residual {residual_gain:.2f}x")
    assert sensor_gain > 1.3, summary
    assert residual_gain > 2.0, summary
    assert numpy.allclose(after, truth, atol=1e-12), "the model part was left modified"
    print("[done] figures at data/dps_guidance.png and data/dps_std_y_sweep.png")
