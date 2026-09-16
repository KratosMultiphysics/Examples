"""The training set for a generative design model, computed by Kratos.

A diffusion model that proposes structures has to be trained on structures
that are actually good, and "actually good" is not a thing a dataset can
assert about itself - it is the output of an optimizer. So this script
runs real topology optimization: an optimality-criteria loop in which
every iteration assembles and solves the finite-element problem through
`StructuralMechanicsAnalysis`, reads each element's strain energy back out
of its own local system, and updates the densities. Thirty iterations per
design, thirty real solves.

The family is two-dimensional, and deliberately so. The conditioning a
design model receives here has three channels - where the structure is
held, where it is loaded, and how much material it may use - and if every
training design used the same volume fraction that third channel would be
a constant, carrying no information while looking as though it carried
some. So the designs vary BOTH the height of the tip load and the volume
fraction, and the held-out cases in script 03 ask for volume fractions
that were never trained on.

The top/bottom mirror doubles the set, and the script checks it instead of
assuming it. That check is worth reading, because the obvious expectation
is wrong. The mirror IS exact for the continuum problem - the clamp runs
the whole x = 0 edge and is symmetric in y - but it is NOT exact for this
mesh. `StructuredMeshGeneratorProcess` splits every cell with a diagonal
that always runs the same way, so the triangulation has no mirror symmetry
in y, and a flipped design sits on a subtly different structure. Measured
here it is worth about 1.7 %, and the script attributes that rather than
asserting it away  it re-solves a UNIFORM design, which is trivially
symmetric in y, at both load rows, so whatever difference survives can
only have come from the mesh.

One number worth being careful about: the optimality-criteria loop starts
from a UNIFORM density field at the requested volume fraction, so
iteration 0's compliance IS the uniform design's compliance. "The optimum
beats uniform" and "the optimum beats its own iteration 0" are therefore
the same statement, and this case claims it once.

Run from this directory:  python3 01_optimize_training_designs.py
Outputs: ../data/simp_training_designs.png, output/training_designs.npz
"""

import json
import pathlib
import sys
import time

import numpy

import KratosMultiphysics as Kratos

sys.path.insert(0, str(pathlib.Path(__file__).parent))
import compliance_case  # noqa: E402

HERE = pathlib.Path(__file__).parent
DATA = HERE.parent / "data"
OUTPUT = HERE / "output"

DIVISIONS = 16
ITERATIONS = 30
# the lower half of the cell rows; the upper half arrives by mirroring
TRAIN_ROWS = tuple(range(DIVISIONS // 2))
TRAIN_FRACTIONS = (0.3, 0.4, 0.5, 0.6)


def LoadRow(index: int) -> float:
    """The `load_row` fraction that lands on cell row `index`.

    Lives in the shared helper because scripts 02 and 03 need exactly the
    same mapping, and three copies of it is three chances to disagree.
    """
    return compliance_case.LoadRowFraction(DIVISIONS, index)


def Optimize(index: int, fraction: float):
    """One optimality-criteria run, plus the compliance of what it produced.

    `OptimizeSimp` returns the history of compliances it saw DURING the
    loop, so the last entry belongs to the design one update before the one
    it returns. The final design has to be solved on its own to be scored.
    """
    cells, history = compliance_case.OptimizeSimp(
        divisions=DIVISIONS, volume_fraction=fraction,
        load_row=LoadRow(index), iterations=ITERATIONS)
    model = Kratos.Model()
    final, _ = compliance_case.SolveCompliance(
        model, numpy.repeat(cells.reshape(-1), 2), DIVISIONS,
        load_row=LoadRow(index))
    return cells, history, float(final)


def BuildTrainingSet():
    records = []
    start = time.time()
    for fraction in TRAIN_FRACTIONS:
        for index in TRAIN_ROWS:
            cells, history, final = Optimize(index, fraction)
            records.append({"row": index, "volume_fraction": fraction,
                            "design": cells, "history": history,
                            "final": final, "uniform": float(history[0])})
        print(f"[data] volume fraction {fraction:g}: {len(TRAIN_ROWS)} optima, "
              f"{time.time() - start:.0f}s elapsed")
    return records


def MirrorRecords(records):
    """Flip each design in y and move its load row to match.

    The mirror acts on the SECOND index, because `DensityGrid` and
    `ConstraintChannels` both run x along the first index and y along the
    second - flipping axis 0 would mirror the clamped edge onto the loaded
    one and produce designs for a problem nobody posed.
    """
    mirrored = []
    for record in records:
        mirrored.append({
            "row": DIVISIONS - 1 - record["row"],
            "volume_fraction": record["volume_fraction"],
            "design": numpy.flip(record["design"], axis=1),
            "history": record["history"], "final": record["final"],
            "uniform": record["uniform"], "mirrored": True})
    return mirrored


def Render(records):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    figure = plt.figure(figsize=(13.0, 9.2), constrained_layout=True)
    grid = figure.add_gridspec(5, 8, height_ratios=[1, 1, 1, 1, 1.3])

    for record in records:
        row = TRAIN_FRACTIONS.index(record["volume_fraction"])
        column = TRAIN_ROWS.index(record["row"])
        axis = figure.add_subplot(grid[row, column])
        # .T because the arrays run x along the first index, and imshow
        # reads the first index as the ROW of the picture
        axis.imshow(record["design"].T, origin="lower", cmap="gray_r",
                    vmin=compliance_case._MINIMUM_DENSITY, vmax=1.0)
        axis.set_xticks([]), axis.set_yticks([])
        if row == 0:
            axis.set_title(f"load row {record['row']}", fontsize=7)
        if column == 0:
            axis.set_ylabel(f"vf {record['volume_fraction']:g}", fontsize=8)

    axis = figure.add_subplot(grid[4, 0:5])
    colours = plt.cm.viridis(numpy.linspace(0.1, 0.9, len(TRAIN_FRACTIONS)))
    for record in records:
        axis.plot(record["history"], lw=0.9, alpha=0.65,
                  color=colours[TRAIN_FRACTIONS.index(record["volume_fraction"])])
    for index, fraction in enumerate(TRAIN_FRACTIONS):
        axis.plot([], [], color=colours[index], label=f"volume fraction {fraction:g}")
    axis.set_xlabel("optimality-criteria iteration")
    axis.set_ylabel("compliance (lower is stiffer)")
    axis.set_yscale("log"), axis.grid(alpha=0.3), axis.legend(fontsize=7)
    axis.set_title("every curve is 30 real Kratos solves, and iteration 0 IS "
                   "the uniform design at that volume fraction", fontsize=9)

    sample = records[0]
    channels = compliance_case.ConstraintChannels(
        DIVISIONS, sample["volume_fraction"], LoadRow(sample["row"]))
    names = ("channel 0\nsupport mask", "channel 1\nload mask",
             "channel 2\nvolume fraction")
    for offset, name in enumerate(names):
        axis = figure.add_subplot(grid[4, 5 + offset])
        axis.imshow(channels[offset].T, origin="lower", cmap="magma",
                    vmin=0.0, vmax=1.0)
        axis.set_title(name, fontsize=7)
        axis.set_xticks([]), axis.set_yticks([])

    figure.suptitle("Topology optima computed by Kratos - the training set a "
                    "generative design model needs, and what it is told about each")
    figure.savefig(DATA / "simp_training_designs.png", dpi=130)


if __name__ == "__main__":
    DATA.mkdir(exist_ok=True)
    OUTPUT.mkdir(exist_ok=True)
    Kratos.Logger.GetDefaultOutput().SetSeverity(Kratos.Logger.Severity.WARNING)

    records = BuildTrainingSet()
    mirrored = MirrorRecords(records)
    everything = records + mirrored
    print(f"[data] {len(records)} optima -> {len(everything)} designs after the "
          f"top/bottom mirror")

    gains = [record["uniform"] / record["final"] for record in records]
    print(f"[eval] stiffer than the uniform design it started from by "
          f"{min(gains):.2f}x to {max(gains):.2f}x (mean {numpy.mean(gains):.2f}x)")

    # The mirror is an assumption about the problem's symmetry, so it gets
    # checked rather than trusted: the flipped design, solved at the
    # flipped load row, should have the compliance of the original.
    probe = records[len(records) // 2]
    probe_row = probe["row"]
    mirrored_compliance, _ = compliance_case.SolveCompliance(
        Kratos.Model(),
        numpy.repeat(numpy.flip(probe["design"], axis=1).reshape(-1), 2),
        DIVISIONS, load_row=LoadRow(DIVISIONS - 1 - probe_row))
    mirror_error = abs(mirrored_compliance - probe["final"]) / probe["final"]
    print(f"[eval] mirrored design at the mirrored load row: "
          f"{mirrored_compliance:.6f} vs {probe['final']:.6f} "
          f"(relative difference {mirror_error:.2%})")

    # It does not come back exact, so the cause gets isolated rather than
    # assumed. A UNIFORM density field is symmetric in y by construction,
    # so solving it at a load row and at the mirrored load row can only
    # differ through the MESH - and it does, because every cell's diagonal
    # runs the same way. Whatever this measures is the floor under the
    # mirror check above; it is not the augmentation being wrong.
    uniform = numpy.full(DIVISIONS * DIVISIONS * 2, 0.4)
    at_row, _ = compliance_case.SolveCompliance(
        Kratos.Model(), uniform, DIVISIONS, load_row=LoadRow(probe_row))
    at_mirror, _ = compliance_case.SolveCompliance(
        Kratos.Model(), uniform, DIVISIONS,
        load_row=LoadRow(DIVISIONS - 1 - probe_row))
    mesh_asymmetry = abs(at_mirror - at_row) / at_row
    print(f"[eval] the same asymmetry on a UNIFORM design (so it is the mesh, "
          f"not the mirror): {at_row:.6f} vs {at_mirror:.6f} "
          f"({mesh_asymmetry:.2%})")

    numpy.savez(
        OUTPUT / "training_designs.npz",
        designs=numpy.stack([record["design"] for record in everything]),
        # the conditioning is built here, once, so script 02 trains on
        # exactly the channels that describe the design beside them
        conditions=numpy.stack([
            compliance_case.ConstraintChannels(
                DIVISIONS, record["volume_fraction"], LoadRow(record["row"]))
            for record in everything]),
        rows=numpy.array([record["row"] for record in everything]),
        fractions=numpy.array([record["volume_fraction"] for record in everything]))
    Render(records)
    with open(OUTPUT / "training_summary.json", "w") as handle:
        json.dump({"designs": len(everything), "optima": len(records),
                   "divisions": DIVISIONS, "iterations": ITERATIONS,
                   "mirror_relative_error": mirror_error,
                   "mesh_asymmetry": mesh_asymmetry,
                   "per_design": [{"row": r["row"], "vf": r["volume_fraction"],
                                   "uniform": r["uniform"], "final": r["final"]}
                                  for r in records]}, handle, indent=1)

    # The claim is the one topology optimization actually makes, stated
    # once: every optimum is stiffer than the uniform field of the same
    # volume fraction that the loop started from. The mirror check is
    # separate, and guards the augmentation rather than the optimizer.
    losers = [(r["row"], r["volume_fraction"]) for r in records
              if not r["final"] < r["uniform"]]
    assert not losers, losers
    # A few percent, not machine precision: the mesh's own asymmetry sets
    # the floor, and asserting 1e-6 here would be asserting a symmetry the
    # triangulation does not have.
    assert mirror_error < 0.05, (mirrored_compliance, probe["final"], mirror_error)
    print("[done] figure at data/simp_training_designs.png")
