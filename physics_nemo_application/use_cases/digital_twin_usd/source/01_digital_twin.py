"""A running solve, its surrogate and its uncertainty as one USD digital twin.

Three acts:

1. A transient heat-conduction solve (moving Gaussian source) is recorded
   once, and a small one-step surrogate f(T_prev, q) -> T is trained on the
   trajectory - MLP with dropout, so MC dropout gives per-node error bars.
2. A second, longer run deploys everything the ordinary ProjectParameters
   way: `InferenceProcess` predicts each step BEFORE the solver runs
   (execution_point initialize_solution_step) and writes prediction +
   MC-dropout spread into nodal variables; `UsdExportProcess` then writes
   solver truth, prediction and spread as one time-sampled OpenUSD stage.
3. The stage is REOPENED with pxr and the figure is drawn purely from what
   the twin carries - points, triangles and primvars - proving the .usda
   file alone holds the whole story. Open it in usdview / Omniverse /
   Blender and scrub.

Run from this directory:  python3 01_digital_twin.py
Outputs: ../data/twin.usda, ../data/digital_twin_panels.png
"""

import pathlib
import sys

import numpy
import torch

import KratosMultiphysics as Kratos

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import transient_plate  # noqa: E402

from KratosMultiphysics.PhysicsNeMoApplication.training import training_utils  # noqa: E402

HERE = pathlib.Path(__file__).parent
DATA = HERE.parent / "data"
DATA.mkdir(exist_ok=True)

DIVISIONS = 32
TIME_STEP = 0.04
TRAIN_END_TIME = 1.0     # one full revolution of the source
DEPLOY_END_TIME = 1.2    # the deployment run scrubs a bit further
CHECKPOINT = HERE / "one_step_surrogate.pt"
STAGE_FILE = DATA / "twin.usda"


# ---------------------------------------------------------------- act 1: train
def RecordTrajectory():
    model = Kratos.Model()
    analysis, model_part = transient_plate.CreateAnalysis(
        model, TRAIN_END_TIME, TIME_STEP, DIVISIONS)
    inputs, targets = [], []

    def record(part):
        previous = [node.GetSolutionStepValue(Kratos.TEMPERATURE, 1) for node in part.Nodes]
        source = [node.GetSolutionStepValue(Kratos.HEAT_FLUX) for node in part.Nodes]
        current = [node.GetSolutionStepValue(Kratos.TEMPERATURE) for node in part.Nodes]
        inputs.append(numpy.stack([previous, source], axis=1))
        targets.append(numpy.asarray(current)[:, None])

    transient_plate.RunTimeLoop(analysis, model_part, per_step=record)
    return numpy.concatenate(inputs), numpy.concatenate(targets)


def TrainSurrogate(features, labels):
    torch.manual_seed(0)
    surrogate = torch.nn.Sequential(
        torch.nn.Linear(2, 64), torch.nn.SiLU(), torch.nn.Dropout(0.1),
        torch.nn.Linear(64, 64), torch.nn.SiLU(), torch.nn.Dropout(0.1),
        torch.nn.Linear(64, 1))
    dataset = torch.utils.data.TensorDataset(
        torch.tensor(features, dtype=torch.float32),
        torch.tensor(labels, dtype=torch.float32))
    history = training_utils.TrainModel(surrogate, dataset, Kratos.Parameters("""{
        "epochs"        : 60,
        "batch_size"    : 8192,
        "learning_rate" : 3e-3,
        "device"        : "cpu",
        "seed"          : 1
    }"""))
    print(f"[train] {len(history)} epochs, loss {history[0]:.3e} -> {history[-1]:.3e}")
    # Kratos fields gather as float64; save the deployed model in the same dtype
    training_utils.SaveTrainedModel(surrogate.double(), CHECKPOINT)
    return history


# --------------------------------------------- act 2: deploy with the exporter
def DeployWithTwin():
    processes = Kratos.Parameters("""[
        {
            "python_module" : "inference_process",
            "kratos_module" : "KratosMultiphysics.PhysicsNeMoApplication.processes.inference",
            "Parameters"    : {
                "model_part_name" : "ThermalModelPart",
                "model_settings"  : {
                    "checkpoint_file" : "%s",
                    "checkpoint_type" : "torchscript",
                    "device"          : "cpu"
                },
                "execution_point" : "initialize_solution_step",
                "input_fields"    : [
                    { "variable_name" : "TEMPERATURE", "data_location" : "node_historical" },
                    { "variable_name" : "HEAT_FLUX",   "data_location" : "node_historical" }
                ],
                "output_fields"   : [
                    { "variable_name" : "NODAL_PAUX",  "data_location" : "node_historical" }
                ],
                "uncertainty"     : {
                    "method"             : "mc_dropout",
                    "num_samples"        : 16,
                    "seed"               : 5,
                    "uncertainty_fields" : [
                        { "variable_name" : "NODAL_ERROR", "data_location" : "node_historical" }
                    ]
                }
            }
        },
        {
            "python_module" : "usd_export_process",
            "kratos_module" : "KratosMultiphysics.PhysicsNeMoApplication.processes.export",
            "Parameters"    : {
                "model_part_name" : "ThermalModelPart",
                "list_of_fields"  : [
                    { "variable_name" : "TEMPERATURE", "data_location" : "node_historical" },
                    { "variable_name" : "NODAL_PAUX",  "data_location" : "node_historical" },
                    { "variable_name" : "NODAL_ERROR", "data_location" : "node_historical" }
                ],
                "output_file"           : "%s",
                "prim_path"             : "/Kratos/Plate",
                "time_source"           : "time",
                "time_codes_per_second" : 1.0
            }
        }
    ]""" % (CHECKPOINT, STAGE_FILE))

    model = Kratos.Model()
    analysis, model_part = transient_plate.CreateAnalysis(
        model, DEPLOY_END_TIME, TIME_STEP, DIVISIONS, processes=processes)
    transient_plate.RunTimeLoop(analysis, model_part)


# ------------------------------------- act 3: the figure, from the twin alone
def RenderFromTwin():
    from pxr import Usd, UsdGeom
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import matplotlib.tri as mtri

    stage = Usd.Stage.Open(str(STAGE_FILE))
    mesh = UsdGeom.Mesh(stage.GetPrimAtPath("/Kratos/Plate"))
    primvars = UsdGeom.PrimvarsAPI(mesh.GetPrim())
    sample_times = mesh.GetPointsAttr().GetTimeSamples()
    print(f"[twin] {STAGE_FILE.name}: time codes {stage.GetStartTimeCode()} .. "
          f"{stage.GetEndTimeCode()} ({len(sample_times)} samples)")

    times = [sample_times[2], sample_times[len(sample_times) // 2], sample_times[-1]]
    points = numpy.array(mesh.GetPointsAttr().Get(times[0]))
    faces = numpy.array(mesh.GetFaceVertexIndicesAttr().Get(times[0])).reshape(-1, 3)
    triangulation = mtri.Triangulation(points[:, 0], points[:, 1], faces)

    columns = [("TEMPERATURE", "solver T"), ("NODAL_PAUX", "surrogate T̂"),
               (None, "|T − T̂|"), ("NODAL_ERROR", "MC-dropout spread")]
    figure, axes = plt.subplots(len(times), len(columns),
                                figsize=(3.1 * len(columns), 2.8 * len(times)),
                                constrained_layout=True)
    correlations = []
    for row, time_code in enumerate(times):
        fields = {name: numpy.array(primvars.GetPrimvar(name).Get(time_code))
                  for name, _ in columns if name}
        fields[None] = numpy.abs(fields["TEMPERATURE"] - fields["NODAL_PAUX"])
        correlations.append(numpy.corrcoef(
            fields["TEMPERATURE"], fields["NODAL_PAUX"])[0, 1])
        for column, (name, label) in enumerate(columns):
            axis = axes[row][column]
            image = axis.tripcolor(triangulation, fields[name], shading="gouraud",
                                   cmap="inferno" if column < 2 else "viridis")
            figure.colorbar(image, ax=axis, shrink=0.85)
            axis.set_aspect("equal")
            axis.set_xticks([]), axis.set_yticks([])
            if row == 0:
                axis.set_title(label)
            if column == 0:
                axis.set_ylabel(f"t = {time_code:.2f}")
    figure.suptitle("Everything below is read back from twin.usda - "
                    "the .usda file alone carries the whole story")
    figure.savefig(DATA / "digital_twin_panels.png", dpi=130)
    print(f"[twin] solver/surrogate correlation at plotted times: "
          + ", ".join(f"{value:.3f}" for value in correlations))
    return min(correlations)


if __name__ == "__main__":
    features, labels = RecordTrajectory()
    print(f"[train] trajectory: {features.shape[0]} node-step samples")
    TrainSurrogate(features, labels)
    DeployWithTwin()
    worst_correlation = RenderFromTwin()
    # the reproducible numeric claim: the one-step surrogate the twin carries
    # genuinely tracks the solver (everything is seeded)
    assert worst_correlation > 0.95, worst_correlation
    print("[done] open data/twin.usda in usdview / Omniverse / Blender and scrub.")
