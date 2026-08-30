"""Stage 1 - deterministic superresolution between two model parts.

SuperResolutionProcess maps a field living on a COARSE model part onto a
FINE one through a learned upsampler (PhysicsNeMo's SRResNet, upscaling
8^3 -> 16^3 voxel grids): sample coarse part -> model -> scatter onto the
fine part's nodes. The two meshes need not be related - only their
bounding boxes matter.

The field family is analytic (a parametrized smooth 3D field), which keeps
this stage focused on the resolution-transfer machinery; the companion
script 02 conditions a diffusion model on genuine coarse-mesh SOLVER
fields instead.

Run time: ~1 minute.
"""

import json
import pathlib

import numpy
import torch
from matplotlib import pyplot
from physicsnemo.models.srrn import SRResNet

import KratosMultiphysics as Kratos
from KratosMultiphysics.PhysicsNeMoApplication import superresolution_process

OUTPUT = pathlib.Path("output")
DATA = pathlib.Path("..") / "data"

COARSE_DIVISIONS, FINE_DIVISIONS = 7, 15   # nodes: 8^3 and 16^3
TRAIN_CASES = 24

_HEX_TO_TETS = ((0, 1, 2, 6), (0, 2, 3, 6), (0, 3, 7, 6),
                (0, 7, 4, 6), (0, 4, 5, 6), (0, 5, 1, 6))


def Field(x, y, z, a, b):
    """The parametrized family the upsampler learns across (a, b)."""
    return (a * numpy.sin(numpy.pi * x) * numpy.sin(numpy.pi * y)
            + b * numpy.cos(numpy.pi * z) * numpy.sin(2.0 * numpy.pi * x))


def CreateTetCube(model, name, divisions):
    model_part = model.CreateModelPart(name)
    model_part.AddNodalSolutionStepVariable(Kratos.PRESSURE)
    model_part.AddNodalSolutionStepVariable(Kratos.TEMPERATURE)
    properties = model_part.CreateNewProperties(1)
    n = divisions + 1
    for i in range(n):
        for j in range(n):
            for k in range(n):
                model_part.CreateNewNode(i * n * n + j * n + k + 1,
                                         i / divisions, j / divisions, k / divisions)
    def node_id(i, j, k):
        return i * n * n + j * n + k + 1
    element = 0
    for i in range(divisions):
        for j in range(divisions):
            for k in range(divisions):
                corners = [node_id(i, j, k), node_id(i + 1, j, k),
                           node_id(i + 1, j + 1, k), node_id(i, j + 1, k),
                           node_id(i, j, k + 1), node_id(i + 1, j, k + 1),
                           node_id(i + 1, j + 1, k + 1), node_id(i, j + 1, k + 1)]
                for tet in _HEX_TO_TETS:
                    element += 1
                    model_part.CreateNewElement(
                        "Element3D4N", element, [corners[c] for c in tet], properties)
    return model_part


def SetField(model_part, a, b):
    for node in model_part.Nodes:
        node.SetSolutionStepValue(Kratos.PRESSURE, Field(node.X, node.Y, node.Z, a, b))


def GridOf(model_part, divisions):
    n = divisions + 1
    values = numpy.array([node.GetSolutionStepValue(Kratos.PRESSURE)
                          for node in model_part.Nodes])
    return values.reshape(n, n, n)  # node ordering is (i, j, k)


def main():
    OUTPUT.mkdir(exist_ok=True)
    DATA.mkdir(exist_ok=True)
    Kratos.Logger.GetDefaultOutput().SetSeverity(Kratos.Logger.Severity.WARNING)

    model = Kratos.Model()
    coarse = CreateTetCube(model, "Coarse", COARSE_DIVISIONS)
    fine = CreateTetCube(model, "Fine", FINE_DIVISIONS)

    # ---- training pairs ---------------------------------------------------
    rng = numpy.random.default_rng(0)
    pairs = []
    for _ in range(TRAIN_CASES):
        a, b = rng.uniform(0.5, 1.5), rng.uniform(0.2, 1.0)
        SetField(coarse, a, b)
        SetField(fine, a, b)
        pairs.append((torch.from_numpy(GridOf(coarse, COARSE_DIVISIONS)[None]).float(),
                      torch.from_numpy(GridOf(fine, FINE_DIVISIONS)[None]).float()))

    torch.manual_seed(0)
    upsampler = SRResNet(in_channels=1, out_channels=1, conv_layer_size=8,
                         n_resid_blocks=2, scaling_factor=2)
    optimizer = torch.optim.Adam(upsampler.parameters(), lr=2e-3)
    inputs = torch.stack([pair[0] for pair in pairs])
    targets = torch.stack([pair[1] for pair in pairs])
    losses = []
    for step in range(250):
        optimizer.zero_grad()
        loss = torch.nn.functional.mse_loss(upsampler(inputs), targets)
        loss.backward()
        optimizer.step()
        losses.append(loss.item())
    upsampler.save(str(OUTPUT / "srresnet.mdlus"))
    print(f"final loss: {losses[-1]:.3e}")

    # ---- deploy on an unseen (a, b) through the process -------------------
    a_test, b_test = 1.25, 0.65
    SetField(coarse, a_test, b_test)
    process = superresolution_process.Factory(Kratos.Parameters("""{
        "Parameters": {
            "coarse_model_part_name" : "Coarse",
            "fine_model_part_name"   : "Fine",
            "model_settings"         : {
                "checkpoint_file" : "output/srresnet.mdlus",
                "checkpoint_type" : "physicsnemo",
                "device"          : "auto"
            },
            "input_fields"           : [ { "variable_name" : "PRESSURE",    "data_location" : "node_historical" } ],
            "output_fields"          : [ { "variable_name" : "TEMPERATURE", "data_location" : "node_historical" } ],
            "coarse_grid_shape"      : [8, 8, 8],
            "output_interval"        : 1
        }
    }"""), model)
    coarse.ProcessInfo[Kratos.STEP] = 1
    process.ExecuteFinalizeSolutionStep()

    predicted = numpy.array([node.GetSolutionStepValue(Kratos.TEMPERATURE)
                             for node in fine.Nodes])
    exact = numpy.array([Field(node.X, node.Y, node.Z, a_test, b_test)
                         for node in fine.Nodes])
    sr_rmse = float(numpy.sqrt(numpy.mean((predicted - exact) ** 2)))

    # baseline: trilinear interpolation of the coarse grid onto the fine nodes
    from scipy.interpolate import RegularGridInterpolator
    axes = numpy.linspace(0.0, 1.0, COARSE_DIVISIONS + 1)
    interpolator = RegularGridInterpolator(
        (axes, axes, axes), GridOf(coarse, COARSE_DIVISIONS))
    fine_points = numpy.array([[node.X, node.Y, node.Z] for node in fine.Nodes])
    trilinear = interpolator(fine_points)
    trilinear_rmse = float(numpy.sqrt(numpy.mean((trilinear - exact) ** 2)))
    print(f"unseen (a, b) = ({a_test}, {b_test}): "
          f"SRResNet rmse {sr_rmse:.4f} vs trilinear {trilinear_rmse:.4f}")

    # ---- figure: mid-plane slices -----------------------------------------
    n_fine = FINE_DIVISIONS + 1
    mid = n_fine // 2
    slices = [(exact.reshape(n_fine, n_fine, n_fine)[:, :, mid], "exact fine field"),
              (trilinear.reshape(n_fine, n_fine, n_fine)[:, :, mid],
               f"trilinear (rmse {trilinear_rmse:.3f})"),
              (predicted.reshape(n_fine, n_fine, n_fine)[:, :, mid],
               f"SRResNet (rmse {sr_rmse:.3f})")]
    limits = dict(vmin=float(exact.min()), vmax=float(exact.max()))
    figure, axes_row = pyplot.subplots(1, 3, figsize=(12.6, 3.9))
    for axis, (plane, title) in zip(axes_row, slices):
        image = axis.imshow(plane.T, origin="lower", cmap="viridis", **limits)
        axis.set_title(title)
        figure.colorbar(image, ax=axis, shrink=0.85)
    figure.suptitle("Superresolution, mid-plane slice, unseen parameters")
    figure.tight_layout()
    figure.savefig(DATA / "superresolution_slices.png", dpi=130)

    with open(OUTPUT / "sr_summary.json", "w") as handle:
        json.dump({"sr_rmse": sr_rmse, "trilinear_rmse": trilinear_rmse,
                   "final_loss": losses[-1]}, handle, indent=1)
    print(f"figure : {DATA / 'superresolution_slices.png'}")


if __name__ == "__main__":
    main()
