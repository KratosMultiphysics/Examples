"""The out-of-distribution question a field guard cannot answer.

A surrogate trained on one family of geometries has two quite different
ways of being handed something it should refuse. The shipped OOD guard
(`ood_guard_utils`) watches the model's INPUT VALUES: conductivity, heat
flux, whatever is gathered per node. That catches a case driven outside the
range it was trained on. It cannot catch a change of SHAPE, and here is why
that matters concretely: `PointCloudInferenceProcess` normalizes
coordinates per axis against the cloud's own bounding box, so a 5 x 1 x 0.2
slab arrives at the model looking exactly like a unit cube. Every value the
field guard inspects is perfectly in range. The geometry is nonsense.

`geometry_guard_utils` asks the other question - it fits a density model to
descriptors of the outward-oriented boundary surface the mesh bridge
already builds, and scores a new geometry against the training family.
Both guards attach to the same process through their own settings blocks
(`"ood_guard"` and `"geometry_guard"`), so this costs one block, not a
rewrite.

FOR THE COMPARISON TO MEAN ANYTHING, only the shape may vary. The source
here is uniform, so both nodal inputs are constants drawn from the same
ranges whatever the box's proportions - the values carry no information
about the geometry, and any flag is attributable to shape alone. That is a
deliberate choice, and the first version of this case got it wrong: with a
Gaussian source of width 0.15 * min(side), the slab's source is four times
sharper than the family's, the flux distribution changes with the geometry,
and the field guard flags the slab - correctly, and for the wrong reason.
Measured that way it fired on both the slab and the rod. If the case data
ties the inputs to the geometry, the field guard is not blind at all; it is
blind to shape only when the inputs genuinely do not encode it.

What this script does:

1. solves a family of 60 nearly-cubic boxes and trains a pointwise
   surrogate (normalized position, heat flux, conductivity) -> temperature;
2. calibrates the FIELD guard on the gathered inputs and fits the GEOMETRY
   guard on the 60 boundary surfaces;
3. deploys the surrogate on four probe geometries - a held-out member of
   the family, a slab, a rod and a perfect cube - with both guards in
   "advisory" mode, and records what each guard says and how wrong the
   surrogate actually is;
4. repeats the slab under "strict", where the process refuses to run.

WHY SIXTY, which is the practical lesson. The descriptor is 22 numbers
wide (`FeatureWidth`), and the shipped `CheckFamilySize` warns below that.
Measured here, 22 is necessary but not sufficient: fitted on 24 geometries
the guard rejects its own HELD-OUT family members (percentile 100), and
`CheckFamilySize` reports no problem at that size. Held-out members are
accepted from about 40 upward. Fit on too few and the guard rejects
everything, which is indistinguishable from a guard that is working until
you test it on data it should accept.

The reproducible claim (everything seeded): the slab is REJECTed by the
geometry guard, the field guard does NOT flag it, and a held-out member of
the training family is accepted.

Run from this directory:  python3 01_geometry_guardrail.py
Outputs: ../data/geometry_guardrail.png
"""

import json
import pathlib
import sys

import numpy
import torch

import KratosMultiphysics as Kratos
import KratosMultiphysics.PhysicsNeMoApplication  # registers the application  # noqa: F401

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import thermal_box  # noqa: E402

from KratosMultiphysics.PhysicsNeMoApplication.deployment import (  # noqa: E402
    geometry_guard_utils, ood_guard_utils)
from KratosMultiphysics.PhysicsNeMoApplication.processes.inference import (  # noqa: E402
    point_cloud_inference_process)
from KratosMultiphysics.PhysicsNeMoApplication.training import training_utils  # noqa: E402

HERE = pathlib.Path(__file__).parent
DATA = HERE.parent / "data"
OUTPUT = HERE / "output"

FAMILY_SIZE = 60            # measured: held-out members are accepted from ~40 up
DIVISIONS = 4
SPREAD = 0.15               # sides drawn uniformly from 1 +/- spread
MODEL_WIDTH = 5             # what the MODEL sees: x, y, z (normalized) + the two fields
# What the FIELD guard sees is narrower, and that is the point of this case:
# the process checks the guard against the GATHERED INPUT FIELDS only, before
# RunPointCloudForward prepends the coordinates. The guard is handed
# (N, 2) - heat flux and conductivity - and never sees a coordinate at all.
GUARD_WIDTH = 2

PROBES = (
    ("held-out family box", (1.07, 0.95, 1.03)),
    ("slab 5 x 1 x 0.2", (5.0, 1.0, 0.2)),
    ("rod 0.3 x 0.3 x 4", (0.3, 0.3, 4.0)),
    ("perfect cube", (1.0, 1.0, 1.0)),
)


class PointwiseSurrogate(torch.nn.Module):
    """The "generic" point-cloud contract: (1, N, 5) in, (1, N, 1) out.

    The process calls `model(cat([coordinates, features], dim=-1)[None])`,
    so the column order here is exactly (x, y, z, heat flux, conductivity)
    and the batch axis is part of the contract - a model returning (N, 1)
    is rejected.
    """

    def __init__(self, width: int = 48):
        super().__init__()
        self.net = torch.nn.Sequential(
            torch.nn.Linear(MODEL_WIDTH, width), torch.nn.Tanh(),
            torch.nn.Linear(width, width), torch.nn.Tanh(),
            torch.nn.Linear(width, 1))

    def forward(self, rows):
        return self.net(rows)


def NormalizedCoordinates(model_part):
    """What the process feeds the model: per-axis min-max of this cloud.

    This is the whole reason a field guard is blind to shape - the slab and
    the cube arrive as the same unit box.
    """
    coordinates = numpy.array(
        [[node.X, node.Y, node.Z] for node in model_part.Nodes], dtype=float)
    low = coordinates.min(axis=0)
    extent = coordinates.max(axis=0) - low
    extent[extent == 0.0] = 1.0
    return (coordinates - low) / extent


def GatherRows(model_part):
    """The model's (N, 5) rows, the guard's (N, 2) values, and (N, 1) targets.

    Two different widths on purpose: the model is fed coordinates prepended
    to the fields, while the process checks the field guard against the
    gathered fields alone.
    """
    values = numpy.array([[node.GetSolutionStepValue(Kratos.HEAT_FLUX),
                           node.GetSolutionStepValue(Kratos.CONDUCTIVITY)]
                          for node in model_part.Nodes], dtype=float)
    temperature = numpy.array([[node.GetSolutionStepValue(Kratos.TEMPERATURE)]
                               for node in model_part.Nodes], dtype=float)
    rows = numpy.hstack([NormalizedCoordinates(model_part), values])
    return rows, values, temperature


def BuildFamily():
    """Solve the training family, keeping each model alive for its part.

    The per-box row blocks are kept separately as well as pooled: the
    surrogate trains on the pool, but the OOD guard is calibrated with ONE
    (N, C) block per geometry - it treats each element of the iterable it
    is given as a training sample, and handing it a single pooled block
    instead makes it read each row as a sample of width one.
    """
    cases = thermal_box.SampleFamily(FAMILY_SIZE, seed=0, spread=SPREAD)
    kept, parts, blocks, value_blocks, targets = [], [], [], [], []
    for index, case in enumerate(cases):
        model, model_part = thermal_box.Solve(divisions=DIVISIONS, **case)
        kept.append(model), parts.append(model_part)
        row, values, target = GatherRows(model_part)
        blocks.append(row), value_blocks.append(values), targets.append(target)
        if (index + 1) % 20 == 0:
            print(f"[data] solved {index + 1}/{FAMILY_SIZE} boxes")
    return (kept, parts, value_blocks, numpy.vstack(blocks), numpy.vstack(targets))


def TrainSurrogate(rows, targets):
    torch.manual_seed(0)
    model = PointwiseSurrogate().double()
    dataset = torch.utils.data.TensorDataset(
        torch.from_numpy(rows), torch.from_numpy(targets))
    history = training_utils.TrainModel(model, dataset, Kratos.Parameters("""{
        "epochs"        : 150,
        "batch_size"    : 256,
        "learning_rate" : 3e-3,
        "device"        : "cpu",
        "seed"          : 0,
        "echo_interval" : 50
    }"""))
    checkpoint = OUTPUT / "box_surrogate.pt"
    training_utils.SaveTrainedModel(model, checkpoint, card={
        "input_fields":  [{"variable_name": "HEAT_FLUX", "data_location": "node_historical"},
                          {"variable_name": "CONDUCTIVITY", "data_location": "node_historical"}],
        "output_fields": [{"variable_name": "NODAL_PAUX",
                           "data_location": "node_non_historical"}]})
    print(f"[train] final loss {history[-1]:.3e}; checkpoint at {checkpoint.name}")
    return model, checkpoint, history


def FitGuards(parts, value_blocks):
    """The field guard on the INPUT VALUES, the geometry guard on the SHAPES.

    Two calling conventions worth stating, both of which fail loudly rather
    than silently: `CalibrateGuardFromTensors` wants an iterable of (N, C)
    blocks, ONE PER TRAINING SAMPLE (handing it a single pooled array makes
    it read each row as a sample of width one), and C must be the width the
    process will later hand it - the gathered fields, not the model input.
    """
    field_guard = ood_guard_utils.CreateOODGuard(
        buffer_size=sum(block.shape[0] for block in value_blocks),
        feature_width=GUARD_WIDTH)
    ood_guard_utils.CalibrateGuardFromTensors(
        field_guard, [torch.from_numpy(block) for block in value_blocks])
    field_file = OUTPUT / "field_guard.pt"
    ood_guard_utils.SaveGuard(field_guard, field_file)

    geometry_guard = geometry_guard_utils.CreateGeometryGuard(Kratos.Parameters("{}"))
    geometry_guard_utils.FitGeometryGuard(geometry_guard, parts)
    geometry_file = geometry_guard_utils.SaveGeometryGuard(
        geometry_guard, OUTPUT / "geometry_guard.npz")   # the extension is required

    surface = geometry_guard_utils.SurfaceOfModelPart(parts[0])
    width = geometry_guard_utils.FeatureWidth(surface)
    verdict = geometry_guard_utils.CheckFamilySize(
        [geometry_guard_utils.SurfaceOfModelPart(part) for part in parts])
    print(f"[guard] descriptor width {width}; fitted on {len(parts)} surfaces; "
          f"CheckFamilySize says: {verdict or 'adequate'}")
    return field_guard, field_file, geometry_guard, geometry_file


def Deploy(checkpoint, field_file, geometry_file, scale, policy="advisory"):
    """One probe geometry through the process, with both guards attached."""
    model, model_part = thermal_box.Solve(divisions=DIVISIONS, scale=scale,
                                          conductivity=1.0, source_amplitude=1.0)
    process = point_cloud_inference_process.Factory(Kratos.Parameters('''{
        "Parameters": {
            "model_part_name"       : "ThermalModelPart",
            "model_settings"        : { "checkpoint_file" : "%s",
                                        "checkpoint_type" : "torchscript",
                                        "device" : "cpu" },
            "model_interface"       : "generic",
            "normalize_coordinates" : true,
            "input_fields"          : [
                { "variable_name" : "HEAT_FLUX",    "data_location" : "node_historical" },
                { "variable_name" : "CONDUCTIVITY", "data_location" : "node_historical" } ],
            "output_fields"         : [
                { "variable_name" : "NODAL_PAUX",   "data_location" : "node_non_historical" } ],
            "ood_guard"             : { "guard_file" : "%s", "policy" : "%s" },
            "geometry_guard"        : { "guard_file" : "%s", "policy" : "%s" }
        }
    }''' % (checkpoint, field_file, policy, geometry_file, policy)), model)

    process.ExecuteInitialize()
    process.ExecuteFinalizeSolutionStep()

    predicted = numpy.array([node.GetValue(Kratos.NODAL_PAUX) for node in model_part.Nodes])
    reference = numpy.array([node.GetSolutionStepValue(Kratos.TEMPERATURE)
                             for node in model_part.Nodes])
    scale_of_field = max(float(numpy.abs(reference).max()), 1e-12)
    # the two guards expose their outcome differently: the field guard keeps a
    # bool, the geometry guard keeps the status STRING and its percentile as
    # two separate attributes (there is no verdict dict to unpack here)
    return {
        "rmse": float(numpy.sqrt(numpy.mean((predicted - reference) ** 2))),
        "field_scale": scale_of_field,
        "field_flagged": bool(process._ood_guard.last_flagged),
        "geometry_status": process._geometry_guard.last_status,
        "geometry_percentile": process._geometry_guard.last_percentile,
        "model": model, "model_part": model_part,
        "predicted": predicted, "reference": reference,
    }


def FieldGuardControl(field_file, conductivity=50.0, scale=(1.05, 0.97, 1.01)):
    """The control this case needs: can the field guard fire AT ALL?

    "The field guard stayed silent" only means something if that guard is
    capable of speaking. With a uniform source each calibration block is N
    identical rows, which is exactly the shape of a degenerate density
    model - so before claiming blindness-to-shape, hand the guard values
    that ARE out of range (the family's conductivity spans about
    [0.81, 1.19]; this is 50x that) and check it flags them.
    """
    guard = ood_guard_utils.LoadGuard(field_file)
    model = Kratos.Model()
    model_part = thermal_box.CreateModelPart(model, scale, DIVISIONS)
    thermal_box.ApplyCase(model_part, scale, conductivity, 1.0)
    _, values, _ = GatherRows(model_part)
    return bool(ood_guard_utils.CheckFeatures(guard, torch.from_numpy(values))), model


def Render(results, control_fired):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure, axes = plt.subplots(1, 3, figsize=(13.4, 3.9), constrained_layout=True)
    names = [name for name, _ in PROBES]
    percentiles = [results[name]["geometry_percentile"] or 0.0 for name in names]
    colours = ["#c0392b" if results[name]["geometry_status"] == "REJECT"
               else "#27ae60" for name in names]

    axes[0].barh(range(len(names)), percentiles, color=colours)
    axes[0].axvline(99.0, color="#f39c12", lw=1, label="warn (99.0)")
    axes[0].axvline(99.9, color="#c0392b", lw=1, ls="--", label="reject (99.9)")
    axes[0].set_yticks(range(len(names)))
    axes[0].set_yticklabels(names, fontsize=8)
    axes[0].set_xlabel("geometry-guard percentile")
    axes[0].set_title("the guard that sees SHAPE", fontsize=9)
    axes[0].legend(fontsize=7), axes[0].invert_yaxis()

    # The field guard is silent on every probe, so a bar chart of its verdicts
    # is four zero-height bars - an empty panel, indistinguishable from one
    # that failed to draw. Label the verdicts instead, and include the CONTROL
    # (values genuinely out of range) so the panel shows a guard that works
    # rather than merely one that says nothing.
    control_label = "control: conductivity x50\n(values genuinely out of range)"
    field_rows = [(name, results[name]["field_flagged"]) for name in names]
    field_rows.append((control_label, control_fired))
    for row, (label, flagged) in enumerate(field_rows):
        axes[1].barh(row, 1.0, color="#c0392b" if flagged else "#dfe6e9",
                     edgecolor="#b2bec3")
        axes[1].text(0.5, row, "FLAGGED" if flagged else "silent",
                     ha="center", va="center", fontsize=9,
                     color="white" if flagged else "#2d3436",
                     fontweight="bold" if flagged else "normal")
    axes[1].set_yticks(range(len(field_rows)))
    axes[1].set_yticklabels([label for label, _ in field_rows], fontsize=7)
    axes[1].set_xlim(0, 1), axes[1].set_xticks([])
    axes[1].axhline(len(names) - 0.5, color="#2d3436", lw=1)
    axes[1].set_title("the guard that sees VALUES\n(blind to shape - but not broken)",
                      fontsize=9)
    axes[1].invert_yaxis()

    relative = [100.0 * results[name]["rmse"] / results[name]["field_scale"] for name in names]
    axes[2].barh(range(len(names)), relative, color=colours)
    axes[2].set_yticks(range(len(names))), axes[2].set_yticklabels(names, fontsize=8)
    axes[2].set_xlabel("surrogate error, % of the field's own range")
    axes[2].set_title("how wrong the surrogate actually is", fontsize=9)
    axes[2].invert_yaxis()

    figure.suptitle("A shape the field guard cannot see: geometry guardrails on "
                    "PointCloudInferenceProcess")
    figure.savefig(DATA / "geometry_guardrail.png", dpi=130)


if __name__ == "__main__":
    DATA.mkdir(exist_ok=True)
    OUTPUT.mkdir(exist_ok=True)
    Kratos.Logger.GetDefaultOutput().SetSeverity(Kratos.Logger.Severity.WARNING)

    kept, parts, value_blocks, rows, targets = BuildFamily()
    print(f"[data] {rows.shape[0]} nodal rows from {FAMILY_SIZE} boxes")
    model, checkpoint, history = TrainSurrogate(rows, targets)
    field_guard, field_file, geometry_guard, geometry_file = FitGuards(parts, value_blocks)

    results = {}
    for name, scale in PROBES:
        outcome = Deploy(checkpoint, field_file, geometry_file, scale)
        results[name] = outcome
        print(f"[eval] {name:<22} geometry {str(outcome['geometry_status']):<7} "
              f"@ {outcome['geometry_percentile']:5.1f}  "
              f"field guard {'FLAGGED' if outcome['field_flagged'] else 'silent ':<8}  "
              f"surrogate error {100.0 * outcome['rmse'] / outcome['field_scale']:.1f}% of range")

    # the same slab again, with the policy that refuses instead of warning
    refused, refused_by = False, None
    try:
        Deploy(checkpoint, field_file, geometry_file, (5.0, 1.0, 0.2), policy="strict")
    except RuntimeError as error:
        refused = True
        # which guard stopped it matters: the point of the case is that the
        # GEOMETRY guard is the one with something to say about a slab
        refused_by = "geometry" if "geometry" in str(error).lower() else "field"
        print(f"[eval] strict policy on the slab: refused by the {refused_by} guard")
    if not refused:
        print("[eval] strict policy on the slab: NOT refused")

    control_fired, _control_model = FieldGuardControl(field_file)
    print(f"[eval] control - conductivity 50x out of range: field guard "
          f"{'FLAGGED (so its silence above is meaningful)' if control_fired else 'SILENT - the guard is degenerate'}")

    Render(results, control_fired)
    with open(OUTPUT / "guardrail_summary.json", "w") as handle:
        json.dump({name: {"geometry_status": r["geometry_status"],
                          "geometry_percentile": r["geometry_percentile"],
                          "field_flagged": r["field_flagged"],
                          "rmse": r["rmse"], "field_scale": r["field_scale"]}
                   for name, r in results.items()}
                  | {"strict_refused": refused, "strict_refused_by": refused_by,
                     "field_guard_control_fired": control_fired},
                  handle, indent=1)

    slab, family = results["slab 5 x 1 x 0.2"], results["held-out family box"]
    # the reproducible claim, and it is a claim about the DIFFERENCE between
    # the two guards: the slab's shape is rejected, its values are not
    # remarkable at all, and a geometry the family does cover is accepted
    assert slab["geometry_status"] == "REJECT", slab["geometry_status"]
    assert not slab["field_flagged"], "the field guard flagged the slab's values"
    assert family["geometry_status"] != "REJECT", family["geometry_status"]
    # and the control, without which "the field guard stayed silent" would be
    # an unfalsifiable claim about a possibly-degenerate guard
    assert control_fired, "the field guard never fires - its silence proves nothing"
    print("[done] figure at data/geometry_guardrail.png")
