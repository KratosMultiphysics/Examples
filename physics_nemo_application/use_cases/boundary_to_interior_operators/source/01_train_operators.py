"""Two operators that map a boundary condition to the interior field.

A surrogate does not have to be pointwise. This case trains two operators
on the same family of boundary-driven Laplace problems - a unit cube with
TEMPERATURE fixed to zero on five faces and a Gaussian bump on the top -
and deploys both through the same `PointCloudInferenceProcess`:

* **xDeepONet** (`physicsnemo.experimental.models.xdeeponet.DeepONet`) maps
  the case PARAMETERS to the field at arbitrary query points. Its branch
  takes (cx, cy, A) and its trunk takes coordinates, so the model is an
  operator from a three-number description of the boundary to a function
  on the domain. This is what `RomSurrogateProcess` does through a POD
  basis, without the basis.
* **GLOBE** (`physicsnemo.experimental.models.globe.GLOBE`) maps the
  BOUNDARY DATA itself to the interior, with Green's-function-like kernels
  on a Barnes-Hut cluster tree - the structure an elliptic problem
  actually has, since here the interior is determined by nothing but the
  boundary values.

The two are trained on the same 16 cases and evaluated on the same 8
held-out ones, so the comparison is like for like. Neither is expected to
win outright and the point is not a ranking: they take genuinely different
inputs, and the interesting question is whether either beats the trivial
predictor that ignores its input entirely.

SIZING GLOBE IS THE WHOLE EXERCISE, and the shipped unit test's parameters
are a trap here. Built at 1 communication hyperlayer with
`hidden_layer_sizes=[16]` - which is what the test uses, because a test
exists to run fast - GLOBE converges to the optimal CONSTANT: its
prediction's mean and maximum are equal, both land on the target field's
mean, and the in-sample RMSE comes out exactly equal to the field's
standard deviation. It looks like a trained model and it has learned one
number. Widening it to 2 hyperlayers, 12/6 latent scalars/vectors and
[32, 32] breaks the collapse. Training data matters just as much: on 8
cases the held-out margin was 1.09x, barely distinguishable from luck; on
16 it is 2.07x and 7.84x for two different model seeds, winning 8 of 8
held-out cases each time. The direction is stable, the MARGIN is not, so
the claim below is about beating the baseline rather than by how much.

GLOBE takes about 6.5 minutes here; the whole script runs in roughly 8.

Two contracts worth knowing before writing either:

* an xDeepONet cannot be checkpointed as `.mdlus` (`Module.save` refuses
  plain torch submodules) and cannot be scripted (its forward takes
  *args), so it is saved by `torch.jit.trace` and deployed as
  `checkpoint_type: "torchscript"`. Tracing stays valid at any number of
  query points, which the deployment script relies on.
* GLOBE's training loop is its own (`globe_training.TrainGlobe`) rather
  than `TrainModel`, because its cases are dicts of meshes and no collate
  function can stack those into a batch tensor. Its cluster tree is built
  per forward on CPU; that is the verified path and the loop defaults to
  it.

The reproducible claim (everything seeded): on the four held-out cases,
both operators predict the interior field better than the node-wise mean
of the training fields.

Run from this directory:  python3 01_train_operators.py
Outputs: ../data/operators_training.png, output/deeponet.pt, output/globe.mdlus
"""

import json
import pathlib
import sys
import time
import warnings

import numpy
import torch

import KratosMultiphysics as Kratos
import KratosMultiphysics.PhysicsNeMoApplication  # registers the application  # noqa: F401

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import thermal_cube_dirichlet as thermal  # noqa: E402

from KratosMultiphysics.PhysicsNeMoApplication.bridges import globe_bridge  # noqa: E402
from KratosMultiphysics.PhysicsNeMoApplication.training import globe_training  # noqa: E402
from KratosMultiphysics.PhysicsNeMoApplication.training import training_utils  # noqa: E402

HERE = pathlib.Path(__file__).parent
DATA = HERE.parent / "data"
OUTPUT = HERE / "output"

DIVISIONS = 4
TRAIN_CASES, TEST_CASES = 16, 8
GLOBE_EPOCHS = 300          # measured: 60 leaves it far short of generalizing
DEEPONET_EPOCHS = 400
WIDTH = 64
BRANCH_WIDTH = 3            # (cx, cy, A) - the case parameters
REFERENCE_LENGTH = {"L": 1.0}


def SolveFamily():
    """Solve the whole family once; every model must outlive its part."""
    cases = thermal.SampleCases(TRAIN_CASES + TEST_CASES, seed=0)
    kept, records = [], []
    for index, case in enumerate(cases):
        model, model_part = thermal.Solve(divisions=DIVISIONS, **case)
        kept.append(model)
        coordinates = numpy.array([[node.X, node.Y, node.Z]
                                   for node in model_part.Nodes], dtype=float)
        field = numpy.array([[node.GetSolutionStepValue(Kratos.TEMPERATURE)]
                             for node in model_part.Nodes], dtype=float)
        meshes = globe_bridge.BuildGlobeBoundaryMeshes(
            model_part, [thermal.TOP_BOUNDARY_NAME],
            [("TEMPERATURE", "node_historical")], source_container="Conditions")
        records.append({
            "parameters": numpy.array([case["center"][0], case["center"][1],
                                       case["amplitude"]], dtype=float),
            "coordinates": coordinates, "field": field, "meshes": meshes,
            "case": case, "model_part": model_part,
        })
        if (index + 1) % 8 == 0:
            print(f"[data] solved {index + 1}/{len(cases)} boundary-driven cases")
    return kept, records[:TRAIN_CASES], records[TRAIN_CASES:]


def MakeDeepONet(seed=0):
    """Branch (case parameters) x trunk (query coordinates) -> field."""
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")       # physicsnemo.experimental import notice
        from physicsnemo.experimental.models.xdeeponet import DeepONet

    torch.manual_seed(seed)
    branch = torch.nn.Sequential(
        torch.nn.Linear(BRANCH_WIDTH, 32), torch.nn.Tanh(), torch.nn.Linear(32, WIDTH))
    trunk = torch.nn.Sequential(
        torch.nn.Linear(3, 32), torch.nn.Tanh(), torch.nn.Linear(32, WIDTH))
    return DeepONet(branch, trunk=trunk, dimension=3, width=WIDTH, out_channels=1)


def TrainDeepONet(model, records, epochs=DEEPONET_EPOCHS, learning_rate=2e-3):
    """One case per step: (1, 3) parameters and (N, 3) coordinates in."""
    optimizer = torch.optim.Adam(model.parameters(), lr=learning_rate)
    branch = [torch.tensor(r["parameters"], dtype=torch.float32)[None] for r in records]
    trunk = [torch.tensor(r["coordinates"], dtype=torch.float32) for r in records]
    targets = [torch.tensor(r["field"], dtype=torch.float32)[None] for r in records]

    history = []
    for epoch in range(epochs):
        total = 0.0
        for parameters, points, target in zip(branch, trunk, targets):
            optimizer.zero_grad()
            loss = torch.nn.functional.mse_loss(model(parameters, points), target)
            loss.backward()
            optimizer.step()
            total += loss.item()
        history.append(total / len(records))
        if epoch % 100 == 0 or epoch == epochs - 1:
            print(f"[train] deeponet epoch {epoch:3d}: {history[-1]:.3e}")
    return history


def MakeGlobe(seed=0):
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        from physicsnemo.experimental.models.globe import GLOBE

    torch.manual_seed(seed)
    return GLOBE(
        n_spatial_dims=3, output_field_ranks={"u": 0},
        boundary_source_data_ranks={thermal.TOP_BOUNDARY_NAME: {"TEMPERATURE": 0}},
        reference_length_names=list(REFERENCE_LENGTH), reference_area=1.0,
        # NOT the shipped test's 1 hyperlayer / [16]: at that size this model
        # converges to the field's mean and nothing else (see the docstring).
        # The cluster tree is built per forward and CPU is the verified path.
        n_communication_hyperlayers=2, n_latent_scalars=12, n_latent_vectors=6,
        hidden_layer_sizes=[32, 32], tree_build_device="cpu",
        use_gradient_checkpointing=False)


def TrainGlobeModel(model, records, epochs=GLOBE_EPOCHS):
    """GLOBE's own loop: its cases are meshes, which no collate can stack."""
    cases = [(r["meshes"], REFERENCE_LENGTH, r["coordinates"], r["field"])
             for r in records]
    return globe_training.TrainGlobe(model, cases, Kratos.Parameters("""{
        "epochs"        : %d,
        "learning_rate" : 3e-3,
        "device"        : "cpu",
        "seed"          : 0,
        "echo_interval" : 20
    }""" % epochs), output_names=["u"])


def Evaluate(deeponet, globe, train_records, test_records):
    """Both operators on the held-out cases, against the mean predictor."""
    baseline = numpy.mean([r["field"] for r in train_records], axis=0)
    results = []
    for record in test_records:
        with torch.no_grad():
            predicted_deeponet = deeponet(
                torch.tensor(record["parameters"], dtype=torch.float32)[None],
                torch.tensor(record["coordinates"], dtype=torch.float32)
            )[0].numpy().astype(float)
        predicted_globe = globe_bridge.RunGlobeForward(
            globe, record["coordinates"], record["meshes"],
            REFERENCE_LENGTH, ["u"]).numpy()

        truth = record["field"]
        rmse = lambda a: float(numpy.sqrt(numpy.mean((a - truth) ** 2)))
        results.append({"deeponet": rmse(predicted_deeponet),
                        "globe": rmse(predicted_globe),
                        "baseline": rmse(baseline),
                        "truth": truth, "coordinates": record["coordinates"],
                        "predicted_deeponet": predicted_deeponet,
                        "predicted_globe": predicted_globe})
        print(f"[eval] held-out case: deeponet {results[-1]['deeponet']:.4e}  "
              f"globe {results[-1]['globe']:.4e}  "
              f"mean predictor {results[-1]['baseline']:.4e}")
    return results, baseline


def Render(deeponet_history, globe_history, results):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure, axes = plt.subplots(1, 3, figsize=(13.2, 3.8), constrained_layout=True)

    axes[0].semilogy(deeponet_history, label="xDeepONet (parameters in)")
    axes[0].set_xlabel("epoch"), axes[0].set_ylabel("MSE")
    axes[0].set_title("xDeepONet training", fontsize=9)
    axes[0].grid(alpha=0.3), axes[0].legend(fontsize=8)

    axes[1].semilogy(globe_history, color="#c0392b", label="GLOBE (boundary in)")
    axes[1].set_xlabel("epoch"), axes[1].set_ylabel("MSE")
    axes[1].set_title("GLOBE training", fontsize=9)
    axes[1].grid(alpha=0.3), axes[1].legend(fontsize=8)

    index = numpy.arange(len(results))
    axes[2].bar(index - 0.26, [r["deeponet"] for r in results], width=0.26,
                label="xDeepONet")
    axes[2].bar(index, [r["globe"] for r in results], width=0.26,
                color="#c0392b", label="GLOBE")
    axes[2].bar(index + 0.26, [r["baseline"] for r in results], width=0.26,
                color="#7f8c8d", label="mean predictor")
    axes[2].set_xticks(index)
    axes[2].set_xticklabels([f"case {i}" for i in index], fontsize=8)
    axes[2].set_ylabel("field RMSE"), axes[2].set_yscale("log")
    axes[2].set_title("held-out cases", fontsize=9), axes[2].legend(fontsize=8)

    figure.suptitle("Two operators from a boundary condition to the interior field")
    figure.savefig(DATA / "operators_training.png", dpi=130)


if __name__ == "__main__":
    DATA.mkdir(exist_ok=True)
    OUTPUT.mkdir(exist_ok=True)
    Kratos.Logger.GetDefaultOutput().SetSeverity(Kratos.Logger.Severity.WARNING)

    started = time.time()
    kept, train_records, test_records = SolveFamily()
    print(f"[data] {TRAIN_CASES} training and {TEST_CASES} held-out cases, "
          f"{train_records[0]['coordinates'].shape[0]} nodes each")

    deeponet = MakeDeepONet()
    deeponet_history = TrainDeepONet(deeponet, train_records)
    # an xDeepONet is neither .mdlus-saveable nor scriptable; tracing is the
    # supported route and stays valid at any number of query points
    traced = torch.jit.trace(
        deeponet.eval(), (torch.randn(1, BRANCH_WIDTH), torch.rand(7, 3)))
    traced.save(str(OUTPUT / "deeponet.pt"))

    globe = MakeGlobe()
    globe_history = TrainGlobeModel(globe, train_records)
    training_utils.SaveTrainedModel(globe, OUTPUT / "globe.mdlus")
    print(f"[train] checkpoints written; {time.time() - started:.0f}s so far")

    results, baseline = Evaluate(deeponet, globe, train_records, test_records)
    Render(deeponet_history, globe_history, results)

    means = {key: float(numpy.mean([r[key] for r in results]))
             for key in ("deeponet", "globe", "baseline")}
    print(f"[eval] means over {len(results)} held-out cases: "
          f"deeponet {means['deeponet']:.4e}, globe {means['globe']:.4e}, "
          f"mean predictor {means['baseline']:.4e}")

    with open(OUTPUT / "training_summary.json", "w") as handle:
        json.dump({"means": means,
                   "per_case": [{k: r[k] for k in ("deeponet", "globe", "baseline")}
                                for r in results],
                   "deeponet_loss": deeponet_history[-1],
                   "globe_loss": globe_history[-1]}, handle, indent=1)

    # The reproducible claim: both operators beat the predictor that ignores
    # its input, on EVERY held-out case rather than on average - a mean can
    # be carried by one good case. Which of the two wins is reported, not
    # asserted: they take different inputs, this family is far too small to
    # rank architectures, and GLOBE's margin moves by a factor of four
    # between model seeds even while its direction does not.
    for key in ("deeponet", "globe"):
        losses = [r for r in results if r[key] >= r["baseline"]]
        assert not losses, (key, losses)
    assert means["deeponet"] < means["baseline"], means
    assert means["globe"] < means["baseline"], means
    print(f"[done] figure at data/operators_training.png "
          f"({time.time() - started:.0f}s total)")
