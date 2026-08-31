"""Stage 2 - cold vs warm-started Newton across an unseen load sweep.

Per load, the SAME nonlinear cantilever is solved twice:

* cold: the standard run, displacement starts at zero;
* warm: HybridInitializationProcess attached through the ProjectParameters
  processes list - one forward pass in ExecuteBeforeSolutionLoop writes the
  surrogate's displacement field into the solution-step variables, and
  Newton-Raphson iterates from there.

Measured, not asserted: NL_ITERATION_NUMBER from ProcessInfo, wall-clock
around Initialize+RunSolutionLoop, and the tip deflections of both runs
(they must agree - the warm start may only change the PATH to the solution,
never the solution).

The third figure is the experiment that shaped the whole example: seeds
of controlled quality (the exact solution plus rough per-node noise, or
smoothly scaled) show that Newton rewards SMOOTH, accurate seeds and
punishes rough ones - a state 100x closer to the solution than zero, with
per-node noise on it, takes MORE iterations than the cold start, because
the rough displacement field carries huge high-frequency strain residual.
That is why stage 1 polishes with LBFGS instead of stopping where Adam
stalls.

Two traps this script documents by construction:

* The process writes ALL nodes, including the clamp - and a value written
  to a fixed DOF becomes its Dirichlet value. The clamp is re-imposed
  after Initialize (the warm start runs inside it), before the loop.
* The convergence target must be ABSOLUTE for the comparison to mean
  anything: a relative criterion normalizes by the initial residual,
  which is exactly what the warm start shrinks - the better the warm
  start, the harsher its target (see structural_cantilever.py).

The per-iteration residual traces come from the solver's own convergence-
criterion output (echo_level 1), captured by file-descriptor redirection -
the numbers in the figure are the ones the strategy printed.

Run time: ~1 minute.
"""

import ctypes
import json
import os
import pathlib
import re
import sys
import time

import numpy
from matplotlib import pyplot

import KratosMultiphysics as Kratos
import KratosMultiphysics.PhysicsNeMoApplication  # registers the application  # noqa: F401

import structural_cantilever

OUTPUT = pathlib.Path("output")
DATA = pathlib.Path("..") / "data"

DIVISIONS = 8
LOAD_SCALE = 1.0e7
TRAIN_MAX = 3.5e7                # training covered [0.5e7, 3.5e7]
SWEEP = (0.75e7, 1.25e7, 1.75e7, 2.25e7, 2.75e7, 3.25e7,   # interpolation
         4.0e7, 4.5e7)                                     # extrapolation
TRACE_LOAD = 2.75e7

_RESIDUAL_LINE = re.compile(r"Absolute norm = ([0-9.eE+-]+)")


def _WarmStartProcessList():
    return Kratos.Parameters("""[{
        "python_module" : "hybrid_initialization_process",
        "kratos_module" : "KratosMultiphysics.PhysicsNeMoApplication.processes.inference",
        "Parameters"    : {
            "model_part_name" : "StructuralModelPart",
            "model_settings"  : {
                "checkpoint_file" : "output/cantilever_warmstart.pt",
                "device"          : "cpu"
            },
            "input_fields"    : [ { "variable_name" : "NODAL_VAUX",   "data_location" : "node_non_historical" } ],
            "output_fields"   : [ { "variable_name" : "DISPLACEMENT", "data_location" : "node_historical" } ]
        }
    }]""")


def RunCase(tip_load, warm, capture_log=None):
    """One solve; returns (iterations, tip, wall_seconds, residual_trace)."""
    model = Kratos.Model()
    analysis, part = structural_cantilever.CreateAnalysis(
        model, tip_load, DIVISIONS,
        echo_level=1 if capture_log else 0,
        extra_processes=_WarmStartProcessList() if warm else None)
    if warm:
        # the surrogate's input rows, gathered by the process as NODAL_VAUX
        for node in part.Nodes:
            node.SetValue(Kratos.NODAL_VAUX,
                          [node.X0, node.Y0, tip_load / LOAD_SCALE])

    def Solve():
        start = time.perf_counter()
        analysis.Initialize()          # warm start happens in here
        if warm:
            # a value written to a fixed DOF becomes its Dirichlet value:
            # re-impose the clamp the process just overwrote
            for node in part.Nodes:
                if node.IsFixed(Kratos.DISPLACEMENT_X):
                    node.SetSolutionStepValue(Kratos.DISPLACEMENT, [0.0, 0.0, 0.0])
        analysis.RunSolutionLoop()
        analysis.Finalize()
        return time.perf_counter() - start

    trace = None
    if capture_log:
        # the criterion prints at INFO severity; the run-wide filter is
        # WARNING, so lift it just for the captured solve
        Kratos.Logger.GetDefaultOutput().SetSeverity(Kratos.Logger.Severity.INFO)
        # flush PYTHON's and C++'s stdout buffers: std::cout is
        # block-buffered while redirected, and anything still sitting in
        # it would land in the wrong capture file
        sys.stdout.flush()
        ctypes.CDLL(None).fflush(None)
        saved = os.dup(1)
        with open(capture_log, "w") as handle:
            os.dup2(handle.fileno(), 1)
            try:
                wall = Solve()
                sys.stdout.flush()
                ctypes.CDLL(None).fflush(None)
            finally:
                os.dup2(saved, 1)
                os.close(saved)
                Kratos.Logger.GetDefaultOutput().SetSeverity(
                    Kratos.Logger.Severity.WARNING)
        trace = [float(match.group(1))
                 for match in map(_RESIDUAL_LINE.search, open(capture_log))
                 if match]
    else:
        wall = Solve()
    return (part.ProcessInfo[Kratos.NL_ITERATION_NUMBER],
            structural_cantilever.GetTipDeflection(part), wall, trace)


def main():
    OUTPUT.mkdir(exist_ok=True)
    DATA.mkdir(exist_ok=True)
    Kratos.Logger.GetDefaultOutput().SetSeverity(Kratos.Logger.Severity.WARNING)

    records = []
    for load in SWEEP:
        cold_iters, cold_tip, cold_wall, _ = RunCase(load, warm=False)
        warm_iters, warm_tip, warm_wall, _ = RunCase(load, warm=True)
        tip_gap = abs(warm_tip - cold_tip)
        records.append({
            "load": load, "extrapolation": load > TRAIN_MAX,
            "cold_iterations": cold_iters, "warm_iterations": warm_iters,
            "cold_wall": cold_wall, "warm_wall": warm_wall,
            "cold_tip": cold_tip, "warm_tip": warm_tip, "tip_gap": tip_gap})
        print(f"  load {load:.2e}: cold {cold_iters} it / warm {warm_iters} it, "
              f"tip {cold_tip:+.4f} vs {warm_tip:+.4f} (gap {tip_gap:.1e})"
              f"{'   [extrapolation]' if load > TRAIN_MAX else ''}")

    # residual traces for one load, cold and warm
    _, _, _, cold_trace = RunCase(TRACE_LOAD, warm=False,
                                  capture_log=str(OUTPUT / "cold_trace.log"))
    _, _, _, warm_trace = RunCase(TRACE_LOAD, warm=True,
                                  capture_log=str(OUTPUT / "warm_trace.log"))

    # ---- figures -----------------------------------------------------------
    loads = numpy.array([record["load"] for record in records]) / 1e7
    cold = [record["cold_iterations"] for record in records]
    warm = [record["warm_iterations"] for record in records]

    figure, (left, right) = pyplot.subplots(1, 2, figsize=(11.2, 4.2))
    width = 0.16
    left.bar(loads - width / 2 * 1.1, cold, width, label="cold start", color="#b3452c")
    left.bar(loads + width / 2 * 1.1, warm, width, label="warm start (surrogate)",
             color="#2c7fb3")
    left.axvspan(TRAIN_MAX / 1e7, loads.max() + 0.3, alpha=0.12, color="gray")
    left.text(loads.max() - 0.02, max(cold) - 0.3, "extrapolation",
              ha="right", fontsize=9, color="gray")
    left.set_xlabel("tip load [$10^7$ N]")
    left.set_ylabel("Newton iterations to converge")
    left.set_title("Iterations, cold vs warm-started")
    left.legend()
    left.grid(True, axis="y", alpha=0.3)

    right.semilogy(range(1, len(cold_trace) + 1), cold_trace, "s-", label="cold start")
    right.semilogy(range(1, len(warm_trace) + 1), warm_trace, "o-", label="warm start")
    right.set_xlabel("Newton iteration")
    right.set_ylabel("residual norm (solver's own output)")
    right.set_title(f"Residual traces, load {TRACE_LOAD:.2e} N")
    right.legend()
    right.grid(True, which="both", alpha=0.3)
    figure.tight_layout()
    figure.savefig(DATA / "newton_acceleration.png", dpi=130)

    interpolation = [record for record in records if not record["extrapolation"]]
    saved = (sum(record["cold_iterations"] for record in interpolation)
             - sum(record["warm_iterations"] for record in interpolation))
    total_cold = sum(record["cold_iterations"] for record in interpolation)
    max_gap = max(record["tip_gap"] for record in records)
    print(f"interpolation loads: {saved}/{total_cold} Newton iterations saved; "
          f"max tip-deflection gap warm vs cold {max_gap:.2e} m")

    # ---- the seed-quality experiment --------------------------------------
    reference_model = Kratos.Model()
    reference_analysis, reference_part = structural_cantilever.CreateAnalysis(
        reference_model, TRACE_LOAD, DIVISIONS)
    reference_analysis.Run()
    cold_reference = reference_part.ProcessInfo[Kratos.NL_ITERATION_NUMBER]
    exact = {node.Id: numpy.array(node.GetSolutionStepValue(Kratos.DISPLACEMENT))
             for node in reference_part.Nodes}

    def IterationsFromSeed(make_seed):
        model = Kratos.Model()
        analysis, part = structural_cantilever.CreateAnalysis(model, TRACE_LOAD, DIVISIONS)
        analysis.Initialize()
        for node in part.Nodes:
            if not node.IsFixed(Kratos.DISPLACEMENT_X):
                node.SetSolutionStepValue(Kratos.DISPLACEMENT, list(make_seed(node)))
        analysis.RunSolutionLoop()
        analysis.Finalize()
        return part.ProcessInfo[Kratos.NL_ITERATION_NUMBER]

    rng = numpy.random.default_rng(0)
    noise_levels = (1e-6, 1e-5, 1e-4, 1e-3, 3e-3)
    rough = []
    for level in noise_levels:
        def Rough(node, level=level):
            noise = rng.normal(0.0, level, 3)
            noise[2] = 0.0
            return exact[node.Id] + noise
        rough.append(IterationsFromSeed(Rough))
    scale_factors = (1.001, 1.005, 1.02, 1.1, 1.3)
    smooth_levels, smooth = [], []
    for factor in scale_factors:
        smooth_levels.append(abs(factor - 1.0) * float(
            numpy.sqrt(numpy.mean([value @ value for value in exact.values()]))))
        smooth.append(IterationsFromSeed(lambda node, f=factor: exact[node.Id] * f))

    figure, axis = pyplot.subplots(figsize=(6.8, 4.2))
    axis.semilogx(noise_levels, rough, "s-", color="#b3452c",
                  label="rough seed (exact + per-node noise)")
    axis.semilogx(smooth_levels, smooth, "o-", color="#2c7fb3",
                  label="smooth seed (exact, scaled)")
    axis.axhline(cold_reference, color="gray", linestyle="--", linewidth=1.2,
                 label=f"cold start ({cold_reference} iterations)")
    axis.set_xlabel("seed error magnitude [m]")
    axis.set_ylabel("Newton iterations to converge")
    axis.set_title(f"What Newton wants from a warm start (load {TRACE_LOAD:.2e} N)")
    axis.legend()
    axis.grid(True, which="both", alpha=0.3)
    figure.tight_layout()
    figure.savefig(DATA / "seed_quality.png", dpi=130)

    with open(OUTPUT / "acceleration_summary.json", "w") as handle:
        json.dump({"records": records, "iterations_saved": saved,
                   "total_cold_iterations": total_cold, "max_tip_gap": max_gap,
                   "cold_trace": cold_trace, "warm_trace": warm_trace,
                   "seed_experiment": {
                       "cold_reference": cold_reference,
                       "noise_levels": list(noise_levels), "rough_iterations": rough,
                       "smooth_levels": smooth_levels, "smooth_iterations": smooth}},
                  handle, indent=1)
    print(f"figures: {DATA / 'newton_acceleration.png'}, {DATA / 'seed_quality.png'}")


if __name__ == "__main__":
    main()
