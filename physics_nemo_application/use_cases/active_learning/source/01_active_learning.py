"""Active learning with Kratos as the ground-truth labeler.

Each queried conductivity is solved by the real ConvectionDiffusion
analysis, launched through the application's active-learning backend
(InProcessBackend + CreateKratosLabelStrategy - the same components
physicsnemo.active_learning's Driver consumes). The query strategy is the
application's ensemble-disagreement one: three surrogate seeds score a
candidate pool, and the solver budget goes where they disagree most.

An HONEST result, kept as found: on this smooth one-parameter family the
error curves of active and random sampling coincide - a handful of solves
saturates the surrogate, so placement cannot matter. What the run shows
instead is WHERE the disagreement strategy spends its budget: it clusters
at the low-conductivity edge, where T ~ f/k varies fastest - exactly the
behavior that pays off when the response is expensive and sharp. Probes
of harder observables (2D source positions, near-singular source widths)
moved the needle by only ~20%, so the smoothness, not the machinery, is
the limiting factor here.

Run time: ~4 minutes (two arms x 8 rounds x 3-member ensembles, plus the
labeling solves).
"""

import json
import pathlib
import queue

import numpy
import torch
from matplotlib import pyplot

import KratosMultiphysics as Kratos
from KratosMultiphysics.PhysicsNeMoApplication.active_learning.sample_io import KratosALSample
from KratosMultiphysics.PhysicsNeMoApplication.active_learning.execution_backends.in_process_backend import (
    InProcessBackend)
from KratosMultiphysics.PhysicsNeMoApplication.active_learning.kratos_label_strategy import (
    CreateKratosLabelStrategy)
from KratosMultiphysics.PhysicsNeMoApplication.active_learning import query_strategies

import thermal_plate

OUTPUT = pathlib.Path("output")
DATA = pathlib.Path("..") / "data"

K_RANGE = (0.15, 2.4)
INITIAL_KS = [0.8, 1.6]
ROUNDS = 8
HELD_OUT_KS = numpy.geomspace(0.18, 2.3, 10)   # dense where T ~ f/k varies fastest
DIVISIONS = 20


def MakeLabeler():
    """Kratos as the labeler, through the app's backend components."""
    pathlib.Path("al_parameters.json").write_text(json.dumps(
        {"case_settings": {"conductivity": 1.0}}, indent=2))
    backend = InProcessBackend(Kratos.Parameters("""{
        "project_parameters_file" : "al_parameters.json",
        "analysis_stage_module"   : "thermal_analysis_stage",
        "working_directory"       : "output/al_cases",
        "model_part_name"         : "ThermalModelPart",
        "output_field_specs"      : [ { "variable_name" : "TEMPERATURE", "data_location" : "node_historical" } ]
    }"""))
    return CreateKratosLabelStrategy(
        backend, provides_fields={"TEMPERATURE__node_historical"})


def Label(labeler, conductivity, index):
    """One real solve -> the (N,) temperature field."""
    sample = KratosALSample(f"k_{index}_{conductivity:.4f}",
                            parameters={"case_settings/conductivity": float(conductivity)})
    to_label, serialized = queue.Queue(), queue.Queue()
    to_label.put(sample)
    labeler(to_label, serialized)
    labeled = serialized.get()
    return numpy.asarray(labeled.fields["TEMPERATURE__node_historical"], dtype=float)


def NodeCoordinates():
    model = Kratos.Model()
    part = thermal_plate.CreateModelPart(model, DIVISIONS)
    return numpy.array([[node.X, node.Y] for node in part.Nodes])


def TrainEnsemble(coordinates, pool, seeds=(0, 1, 2)):
    """Three (x, y, k) -> T members on the labeled pool."""
    inputs, targets = [], []
    for conductivity, field in pool:
        for (x, y), value in zip(coordinates, field):
            inputs.append([x, y, conductivity])
            targets.append([value])
    inputs = torch.tensor(inputs, dtype=torch.float64)
    targets = torch.tensor(targets, dtype=torch.float64)
    members = []
    for seed in seeds:
        torch.manual_seed(seed)
        member = torch.nn.Sequential(
            torch.nn.Linear(3, 32), torch.nn.Tanh(),
            torch.nn.Linear(32, 32), torch.nn.Tanh(),
            torch.nn.Linear(32, 1)).double()
        optimizer = torch.optim.Adam(member.parameters(), lr=2e-3)
        for _ in range(300):
            optimizer.zero_grad()
            torch.nn.functional.mse_loss(member(inputs), targets).backward()
            optimizer.step()
        members.append(member.eval())
    return members


def HeldOutError(members, coordinates, references):
    errors = []
    with torch.no_grad():
        for conductivity, field in references:
            batch = torch.tensor(
                numpy.column_stack([coordinates,
                                    numpy.full(len(coordinates), conductivity)]),
                dtype=torch.float64)
            mean = numpy.mean([m(batch).numpy()[:, 0] for m in members], axis=0)
            errors.append(numpy.sqrt(numpy.mean((mean - field) ** 2)))
    return float(numpy.mean(errors))


def QueryByDisagreement(members, coordinates, labeled_ks, index):
    """The app's ensemble-disagreement strategy picks the next k."""
    for seed, member in enumerate(members):
        torch.jit.script(member).save(f"output/al_member_{seed}.pt")
    settings = Kratos.Parameters("""{
        "max_samples"          : 1,
        "candidate_pool_size"  : 24,
        "ensemble_checkpoints" : []
    }""")
    for seed in range(len(members)):
        entry = Kratos.Parameters('{ "checkpoint_file": "", "device": "cpu" }')
        entry["checkpoint_file"].SetString(f"output/al_member_{seed}.pt")
        settings["ensemble_checkpoints"].Append(entry)

    rng = numpy.random.default_rng(1000 + index)

    def CandidateSampler(count):
        candidates = rng.uniform(*K_RANGE, size=count)
        return [{"case_settings/conductivity": float(k)} for k in candidates]

    def EncodeCandidate(candidate):
        k = candidate["case_settings/conductivity"]
        return torch.tensor(
            numpy.column_stack([coordinates, numpy.full(len(coordinates), k)]),
            dtype=torch.float64)

    strategy = query_strategies.CreateEnsembleDisagreementStrategy(
        settings, CandidateSampler, EncodeCandidate)
    candidate_queue = queue.Queue()
    strategy.sample(candidate_queue)
    picked = candidate_queue.get()
    return float(picked.parameters["case_settings/conductivity"])


def main():
    OUTPUT.mkdir(exist_ok=True)
    DATA.mkdir(exist_ok=True)
    Kratos.Logger.GetDefaultOutput().SetSeverity(Kratos.Logger.Severity.WARNING)

    labeler = MakeLabeler()
    coordinates = NodeCoordinates()
    references = [(float(k), Label(labeler, float(k), 900 + i))
                  for i, k in enumerate(HELD_OUT_KS)]

    curves = {}
    queried = {}
    for arm in ("active", "random"):
        pool = [(k, Label(labeler, k, index)) for index, k in enumerate(INITIAL_KS)]
        rng = numpy.random.default_rng(7)
        curve = []
        queried[arm] = []
        for round_index in range(ROUNDS + 1):
            members = TrainEnsemble(coordinates, pool)
            curve.append((len(pool), HeldOutError(members, coordinates, references)))
            if round_index == ROUNDS:
                break
            if arm == "active":
                next_k = QueryByDisagreement(members, coordinates,
                                             [k for k, _ in pool], round_index)
            else:
                next_k = float(rng.uniform(*K_RANGE))
            queried[arm].append(next_k)
            pool.append((next_k, Label(labeler, next_k, 100 + round_index)))
            print(f"  {arm}: solve {len(pool) + 1}, queried k = {next_k:.3f}")
        curves[arm] = curve
        print(f"{arm}: {curve[0][1]:.2e} @ {curve[0][0]} solves -> "
              f"{curve[-1][1]:.2e} @ {curve[-1][0]} solves")

    figure, axes = pyplot.subplots(1, 2, figsize=(12.4, 4.2))
    for arm, marker in (("active", "o"), ("random", "s")):
        budgets, errors = zip(*curves[arm])
        axes[0].semilogy(budgets, errors, marker + "-",
                         label=f"{arm} ({'ensemble disagreement' if arm == 'active' else 'uniform'})")
    axes[0].set_xlabel("number of Kratos solves in the training pool")
    axes[0].set_ylabel("held-out field RMSE (10 unseen conductivities)")
    axes[0].set_title("Error vs budget: the curves coincide\n(a smooth family saturates early - the honest result)")
    axes[0].legend()
    axes[0].grid(True, which="both", alpha=0.3)

    for row, arm in enumerate(("active", "random")):
        ks = queried[arm]
        axes[1].plot(ks, [row] * len(ks), "o" if arm == "active" else "s",
                     markersize=9, alpha=0.7, label=arm)
    axes[1].set_yticks([0, 1], ["active", "random"])
    axes[1].set_xlabel("queried conductivity k")
    axes[1].set_title("Where the budget went: disagreement clusters\nat the low-k edge, where T ~ f/k varies fastest")
    axes[1].grid(True, axis="x", alpha=0.3)
    figure.tight_layout()
    figure.savefig(DATA / "active_learning_curve.png", dpi=130)

    with open(OUTPUT / "al_summary.json", "w") as handle:
        json.dump({"curves": curves, "queried": queried}, handle, indent=1)
    print(f"figure : {DATA / 'active_learning_curve.png'}")


if __name__ == "__main__":
    main()
