"""Sampled designs, scored by handing them back to the solver.

This is what closes the loop and what makes the case worth having. A
generative model that produces plausible-looking structures has produced
pictures. Here every sampled density field is written onto the elements
through SIMP and **re-solved by Kratos**, so the score is the compliance
of the structure rather than a resemblance to the training set.

The held-out conditions ask for volume fractions the model was never
trained on - 0.45, 0.35 and 0.55, against a training set of 0.3, 0.4, 0.5
and 0.6 - so the third conditioning channel has to be interpolated rather
than recalled.

**Choosing the baseline is the whole difficulty, and the obvious one is
wrong.** Under SIMP with p = 3 the modulus goes as rho^3, so a uniform
field at rho = 0.4 is far more compliant than its volume fraction
suggests, and "the generated design beats uniform" is a bar almost
anything clears. It is reported here and never asserted. The bar that
means something is a **volume-fraction-matched random control**: a smooth
random structure using the same amount of material. Beating that says the
model learned where to put material, which is the only claim worth making.

The controls are matched by bisecting `SmoothRandomDensities`' threshold
until the realized volume fraction meets the request, because a control
that quietly used more material would be losing on material rather than
on design.

Run from this directory:  python3 03_sample_and_score.py
Outputs: ../data/generated_designs.png
"""

import json
import pathlib
import sys

import numpy

import KratosMultiphysics as Kratos
import KratosMultiphysics.PhysicsNeMoApplication  # registers the application  # noqa: F401

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import compliance_case  # noqa: E402

from KratosMultiphysics.PhysicsNeMoApplication.deployment import model_registry  # noqa: E402
from KratosMultiphysics.PhysicsNeMoApplication.training import diffusion_utils  # noqa: E402

HERE = pathlib.Path(__file__).parent
DATA = HERE.parent / "data"
OUTPUT = HERE / "output"

DIVISIONS = 16
SAMPLES = 8
STEPS = 18
SEED = 11
# rows the model has seen, volume fractions it has not
HELD_OUT = ((2, 0.45), (5, 0.35), (11, 0.55))


def Score(design, row):
    """A density image in, the compliance of the real structure out."""
    densities = numpy.repeat(numpy.asarray(design).reshape(-1), 2)
    compliance, _ = compliance_case.SolveCompliance(
        Kratos.Model(), densities, DIVISIONS,
        load_row=compliance_case.LoadRowFraction(DIVISIONS, row))
    return float(compliance)


def VolumeMatchedRandom(seed, volume_fraction):
    """A smooth random structure using the requested amount of material.

    The threshold is bisected rather than guessed: `SmoothRandomDensities`
    thresholds a standardized field, so its realized volume fraction moves
    with the threshold, and an unmatched control would be beaten on
    material rather than on where the material went.
    """
    low, high = -4.0, 4.0
    for _ in range(40):
        middle = 0.5 * (low + high)
        densities = compliance_case.SmoothRandomDensities(
            DIVISIONS, seed=seed, threshold=middle)
        if densities.mean() > volume_fraction:
            low = middle          # too much material, raise the bar
        else:
            high = middle
    return compliance_case.SmoothRandomDensities(
        DIVISIONS, seed=seed, threshold=0.5 * (low + high))


def Render(results):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure = plt.figure(figsize=(13.0, 3.3 * len(results)), constrained_layout=True)
    grid = figure.add_gridspec(len(results), 7)

    for row, result in enumerate(results):
        panels = [("optimality-criteria\noptimum", result["optimum"]),
                  ("volume-matched\nrandom", result["random_design"])]
        panels += [(f"sampled {index}", design)
                   for index, design in enumerate(result["designs"][:3])]
        for column, (name, values) in enumerate(panels):
            axis = figure.add_subplot(grid[row, column])
            axis.imshow(numpy.asarray(values).T, origin="lower", cmap="gray_r",
                        vmin=compliance_case._MINIMUM_DENSITY, vmax=1.0)
            axis.set_title(name, fontsize=7)
            axis.set_xticks([]), axis.set_yticks([])
            if column == 0:
                axis.set_ylabel(f"row {result['row']}\nvf {result['volume_fraction']:g}",
                                fontsize=8)

        axis = figure.add_subplot(grid[row, 5:7])
        axis.scatter(numpy.zeros(len(result["sampled"])) + 0.0, result["sampled"],
                     s=26, color="#2980b9", label="sampled", zorder=3)
        axis.scatter(numpy.zeros(len(result["random"])) + 1.0, result["random"],
                     s=26, color="#7f8c8d", label="volume-matched random", zorder=3)
        axis.scatter([2.0], [result["uniform"]], s=40, marker="s",
                     color="#e67e22", label="uniform", zorder=3)
        axis.scatter([3.0], [result["optimum_compliance"]], s=40, marker="*",
                     color="#c0392b", label="OC optimum", zorder=3)
        axis.set_xticks([0, 1, 2, 3])
        axis.set_xticklabels(["sampled", "random", "uniform", "optimum"], fontsize=7)
        axis.set_yscale("log"), axis.grid(alpha=0.3, axis="y")
        axis.set_ylabel("compliance", fontsize=8)
        if row == 0:
            axis.legend(fontsize=6, loc="upper right")

    figure.suptitle("Sampled designs, scored by re-solving them in Kratos")
    figure.savefig(DATA / "generated_designs.png", dpi=130)


if __name__ == "__main__":
    DATA.mkdir(exist_ok=True)
    OUTPUT.mkdir(exist_ok=True)
    Kratos.Logger.GetDefaultOutput().SetSeverity(Kratos.Logger.Severity.WARNING)

    checkpoint = OUTPUT / "topodiff_design.mdlus"
    if not checkpoint.is_file():
        raise SystemExit("run 02_train_topodiff.py first (it writes the checkpoint)")

    # LoadModel returns the bare TopoDiff, so the diffusion wrapper has to
    # be reapplied before it can be sampled from
    loaded, device = model_registry.LoadModel(Kratos.Parameters("""{
        "checkpoint_file" : "%s",
        "checkpoint_type" : "physicsnemo",
        "device"          : "cpu"
    }""" % checkpoint))
    wrapped = diffusion_utils.WrapDiffusionModel(loaded, "topodiff", out_channels=1)
    print(f"[data] checkpoint reloaded on {device} and re-wrapped for sampling")

    results = []
    for row, fraction in HELD_OUT:
        condition = compliance_case.ConstraintChannels(
            DIVISIONS, fraction,
            compliance_case.LoadRowFraction(DIVISIONS, row)).astype(numpy.float32)

        ensemble = diffusion_utils.GenerateEnsemble(wrapped, condition, Kratos.Parameters("""{
            "num_samples"        : %d,
            "num_steps"          : %d,
            "seed"               : %d,
            "denoiser_interface" : "protocol",
            "output_channels"    : 1
        }""" % (SAMPLES, STEPS, SEED)))
        designs = numpy.clip(ensemble[:, 0], compliance_case._MINIMUM_DENSITY, 1.0)
        sampled = [Score(design, row) for design in designs]

        random_designs = [VolumeMatchedRandom(seed, fraction)
                          for seed in range(100, 100 + SAMPLES)]
        random_scores = [Score(compliance_case.DensityGrid(d, DIVISIONS), row)
                         for d in random_designs]

        uniform = Score(numpy.full((DIVISIONS, DIVISIONS), fraction), row)
        optimum, _ = compliance_case.OptimizeSimp(
            divisions=DIVISIONS, volume_fraction=fraction,
            load_row=compliance_case.LoadRowFraction(DIVISIONS, row), iterations=30)
        optimum_compliance = Score(optimum, row)

        results.append({
            "row": row, "volume_fraction": fraction,
            "designs": designs, "sampled": sampled,
            "random": random_scores,
            "random_design": compliance_case.DensityGrid(random_designs[0], DIVISIONS),
            "uniform": uniform, "optimum": optimum,
            "optimum_compliance": optimum_compliance,
            "sampled_volume": float(designs.mean()),
        })
        print(f"[eval] row {row}, vf {fraction:g}: sampled mean "
              f"{numpy.mean(sampled):.4f} (volume {designs.mean():.3f}), "
              f"random mean {numpy.mean(random_scores):.4f}, "
              f"uniform {uniform:.4f}, optimum {optimum_compliance:.4f}")

    Render(results)
    with open(OUTPUT / "sampling_summary.json", "w") as handle:
        json.dump([{k: v for k, v in result.items()
                    if k not in ("designs", "optimum", "random_design")}
                   for result in results], handle, indent=1)

    # Two claims, and deliberately not a third. Every sampled design has
    # to be a real structure the solver can score, and the sampled mean
    # has to beat the volume-matched random control. "Beats uniform" is
    # printed above and never asserted: under SIMP p = 3 that bar is far
    # lower than it sounds, and asserting it would flatter the model.
    for result in results:
        assert numpy.isfinite(result["sampled"]).all(), result["row"]
        assert all(value > 0.0 for value in result["sampled"]), result["sampled"]
    losers = [(r["row"], numpy.mean(r["sampled"]), numpy.mean(r["random"]))
              for r in results if not numpy.mean(r["sampled"]) < numpy.mean(r["random"])]
    assert not losers, losers
    print("[done] figure at data/generated_designs.png")
