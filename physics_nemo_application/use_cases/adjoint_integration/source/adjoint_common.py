"""Shared pieces for the adjoint-integration stages.

Two things every stage needs: a way to run a Kratos response function (which
insists on the case's own working directory), and the FFD-parameterized
thermal design family the surrogate is trained on.
"""

import contextlib
import os
import pathlib

import numpy
import torch

import KratosMultiphysics as Kratos
from KratosMultiphysics.PhysicsNeMoApplication.bridges.mesh_bridge import deformation
from KratosMultiphysics.PhysicsNeMoApplication.physics import differentiable_residual
from KratosMultiphysics.PhysicsNeMoApplication.physics import sensitivity_utils

import thermal_case

CASES = pathlib.Path(__file__).resolve().parent / "cases"

# an FFD lattice spanning the unit square; the z extent is non-degenerate on
# purpose, since the mesh's own bounding box is flat in z
ORIGIN = [0.0, 0.0, -0.5]
EXTENT = [1.0, 1.0, 1.0]
DIVISIONS = 8


@contextlib.contextmanager
def Quiet():
    """Silences Kratos' solver chatter around a block.

    WARNING is Kratos' highest severity, so its own deprecation notices
    cannot be turned off through the logger - and because the logging is in
    C++, contextlib.redirect_stdout never sees it. The file descriptor
    itself has to be redirected. Python exceptions are unaffected.
    """
    saved = os.dup(1)
    with open(os.devnull, "w") as null:
        os.dup2(null.fileno(), 1)
    try:
        yield
    finally:
        os.dup2(saved, 1)
        os.close(saved)


@contextlib.contextmanager
def InCaseDirectory():
    """A Kratos response function reads its primal settings from a file by
    name and re-reads the mdpa for its own adjoint model part, so it only
    works from the case's own directory."""
    previous = pathlib.Path.cwd()
    os.chdir(CASES)
    try:
        yield CASES
    finally:
        os.chdir(previous)


# --------------------------------------------------------------- the design

def ControlFromTheta(theta):
    """Two design parameters into the FFD lattice's control displacements.

    Control values are DISPLACEMENTS, not destination coordinates: zero is
    the identity.
    """
    control = numpy.zeros((2, 2, 2, 3))
    control[1, :, :, 0] = theta[0]      # move the right face in x
    control[:, 1, :, 1] = theta[1]      # move the top face in y
    return control


def ThetaGradient(control_gradient):
    """dJ/dtheta from dJ/d(control). The map above is linear with 0/1
    entries, so its chain rule is a sum over the entries each theta feeds."""
    return numpy.array([control_gradient[1, :, :, 0].sum(),
                        control_gradient[:, 1, :, 1].sum()])


def SolveThermal(theta=None, reference=None, divisions=DIVISIONS):
    """The stationary thermal case, optionally on an FFD-deformed mesh."""
    model = Kratos.Model()
    with Quiet():
        analysis = thermal_case.CreateThermalAnalysis(
            model, conductivity=2.0, heat_flux=1.0, divisions=divisions)
        analysis.Initialize()
    model_part = model["ThermalModelPart"]

    if theta is not None and reference is not None:
        points = torch.as_tensor(reference, dtype=torch.float64)
        deformed = deformation.DeformPoints(
            points, torch.as_tensor(ControlFromTheta(theta), dtype=torch.float64),
            "ffd", origin=ORIGIN, extent=EXTENT).numpy()
        for node, position in zip(model_part.Nodes, deformed):
            node.X0, node.Y0, node.Z0 = (float(position[0]), float(position[1]),
                                         float(position[2]))
            node.X, node.Y, node.Z = node.X0, node.Y0, node.Z0

    with Quiet():
        analysis.RunSolutionLoop()
    return model, model_part


def TotalTemperature(model_part):
    """J = sum of the nodal temperatures."""
    return sum(node.GetSolutionStepValue(Kratos.TEMPERATURE)
               for node in model_part.Nodes)


def ReferenceCoordinates(model_part):
    return numpy.array([[node.X0, node.Y0, node.Z0] for node in model_part.Nodes])


def ShapeSensitivityField(model_part, fd_step=1e-6):
    """Exact dJ/dX at every node for J = sum(T), from one mesh pass."""
    assembler = differentiable_residual.TangentAssembler(model_part)
    dof_map = differentiable_residual.DofFieldMap(
        assembler, [("TEMPERATURE", "node_historical")])
    return sensitivity_utils.ComputeShapeSensitivityField(
        assembler, dof_map, numpy.ones(dof_map.n_equations), fd_step=fd_step)


def Sample(theta, reference):
    """One gradient-augmented sample: (J, dJ/dtheta) at one design.

    The adjoint costs one extra mesh pass on top of the solve and is exact -
    which is what makes gradient-augmented data cheap enough to be worth
    collecting at all.
    """
    _, model_part = SolveThermal(theta, reference)
    value = TotalTemperature(model_part)
    field = ShapeSensitivityField(model_part)
    control_gradient = sensitivity_utils.ComputeControlSensitivities(
        field, reference, ControlFromTheta(theta), "ffd",
        origin=ORIGIN, extent=EXTENT)
    return value, ThetaGradient(control_gradient)


def BuildDataset(thetas, reference):
    """(inputs (n, 2), targets (n, 3) = [J, dJ/dtheta_0, dJ/dtheta_1])."""
    values, gradients = [], []
    for theta in thetas:
        value, gradient = Sample(theta, reference)
        values.append(value)
        gradients.append(gradient)
    return (torch.tensor(numpy.asarray(thetas), dtype=torch.float64),
            torch.tensor(numpy.column_stack([values, numpy.asarray(gradients)]),
                         dtype=torch.float64))


def MakeModel(seed=1):
    torch.manual_seed(seed)
    return torch.nn.Sequential(
        torch.nn.Linear(2, 32), torch.nn.Tanh(),
        torch.nn.Linear(32, 32), torch.nn.Tanh(),
        torch.nn.Linear(32, 1)).double()
