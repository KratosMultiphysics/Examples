"""Stage 1 - a family of generated geometries, solved and learned.

Six hole positions/radii, each generated from its SDF and solved for the
heated-hole conduction field (~400 nodes each, 0.2 s per generation).
Four surrogates are trained on the pooled nodal data - identical nets,
differing only in how much of the geometry they are shown:

    (x, y)                        geometry-blind ablation
    (x, y, phi)                   the signed distance value
    (x, y, phi, grad phi)         + direction to the hole
    (x, y, phi, grad phi, lap)    + curvature: the SDF's full 2-jet

Each derivative order removes ambiguity the previous encoding could not
resolve (two shapes can agree on (x, y, phi) at a node and still have
different fields). The 2-jet localizes the disc exactly - see
thermal_hole_case.FeatureLadder - and lands near the single-shape
capacity floor. Stage 2 shows the same ladder on a shape none of them
ever saw.

Run time: ~2 minutes (most of it the four LBFGS polishes).
"""

import json
import pathlib

import numpy
import torch
from matplotlib import pyplot

import KratosMultiphysics as Kratos

import thermal_hole_case

OUTPUT = pathlib.Path("output")
DATA = pathlib.Path("..") / "data"

TRAIN_SHAPES = ((0.35, 0.35, 0.15), (0.65, 0.35, 0.12), (0.35, 0.65, 0.12),
                (0.65, 0.65, 0.15), (0.50, 0.50, 0.20), (0.45, 0.60, 0.10))
# encoding name -> feature columns of the ladder matrix
ENCODINGS = {"blind (x, y)": 2, "+ phi": 3, "+ grad phi": 5, "+ laplacian": 6}


def TrainNet(inputs, targets):
    torch.manual_seed(0)
    net = torch.nn.Sequential(
        torch.nn.Linear(inputs.shape[1], 64), torch.nn.Tanh(),
        torch.nn.Linear(64, 64), torch.nn.Tanh(), torch.nn.Linear(64, 1)).double()
    optimizer = torch.optim.Adam(net.parameters(), lr=2e-3)
    for _ in range(3000):
        optimizer.zero_grad()
        torch.nn.functional.mse_loss(net(inputs), targets).backward()
        optimizer.step()
    lbfgs = torch.optim.LBFGS(net.parameters(), max_iter=300, history_size=40,
                              tolerance_grad=1e-14, tolerance_change=1e-16)

    def Closure():
        lbfgs.zero_grad()
        loss = torch.nn.functional.mse_loss(net(inputs), targets)
        loss.backward()
        return loss

    lbfgs.step(Closure)
    net.eval()
    with torch.no_grad():
        rmse = float(torch.sqrt(((net(inputs) - targets) ** 2).mean()))
    return net, rmse


def main():
    OUTPUT.mkdir(exist_ok=True)
    DATA.mkdir(exist_ok=True)
    Kratos.Logger.GetDefaultOutput().SetSeverity(Kratos.Logger.Severity.WARNING)

    rows, temps, shapes_meta = [], [], []
    figure, axes = pyplot.subplots(2, 3, figsize=(11.4, 7.2))
    for axis, (cx, cy, radius) in zip(axes.ravel(), TRAIN_SHAPES):
        model = Kratos.Model()
        part = thermal_hole_case.GenerateAndSolve(model, (cx, cy), radius)
        rows.append(thermal_hole_case.FeatureLadder(part, (cx, cy), radius))
        values = thermal_hole_case.Temperatures(part)
        temps.append(values)
        shapes_meta.append({"center": [cx, cy], "radius": radius,
                            "nodes": part.NumberOfNodes(),
                            "elements": part.NumberOfElements()})
        print(f"  shape ({cx}, {cy}, r={radius}): {part.NumberOfNodes()} nodes, "
              f"{part.NumberOfElements()} triangles")

        points, triangles = thermal_hole_case.Triangulation(part)
        contour = axis.tricontourf(points[:, 0], points[:, 1], triangles, values,
                                   levels=21, cmap="inferno")
        axis.triplot(points[:, 0], points[:, 1], triangles,
                     color="white", linewidth=0.25, alpha=0.45)
        axis.set_title(f"hole ({cx}, {cy}), r = {radius}", fontsize=10)
        axis.set_aspect("equal")
        axis.set_xticks([])
        axis.set_yticks([])
    figure.colorbar(contour, ax=axes, shrink=0.8, label="TEMPERATURE")
    figure.suptitle("Generated geometry family: SDF -> mesh -> solve", y=0.98)
    figure.savefig(DATA / "generated_family.png", dpi=130, bbox_inches="tight")

    ladder = torch.tensor(numpy.concatenate(rows), dtype=torch.float64)
    targets = torch.tensor(numpy.concatenate(temps), dtype=torch.float64)[:, None]

    results = {}
    for name, columns in ENCODINGS.items():
        net, rmse = TrainNet(ladder[:, :columns], targets)
        results[name] = {"columns": columns, "train_rmse": rmse}
        stem = f"encoding_{columns}"
        torch.jit.script(net).save(str(OUTPUT / f"{stem}.pt"))
        print(f"  {name:14s}: train RMSE {rmse:.2e}")

    with open(OUTPUT / "training_summary.json", "w") as handle:
        json.dump({"shapes": shapes_meta, "rows": len(ladder),
                   "encodings": results}, handle, indent=1)
    print(f"figure : {DATA / 'generated_family.png'}")


if __name__ == "__main__":
    main()
