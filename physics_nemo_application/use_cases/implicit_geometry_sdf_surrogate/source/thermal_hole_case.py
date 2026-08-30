"""Heat conduction on GENERATED geometry: a plate with a heated hole.

The geometry never touches a mesher input file: it is a signed distance
function (unit box minus a disc, physicsnemo's differentiable SDF
primitives composed by mesh_bridge.generate.SdfPrimitives), turned into a
solvable Kratos model part by GenerateImplicitDomain +
PopulateModelPartFromMesh. The hole boundary is held at T = 1, the outer
square at T = 0, and ConvectionDiffusion's stationary solver does the
rest - a real solve on geometry that started as math.

Boundary selection uses the geometry's own definition: the generator
projects boundary nodes EXACTLY onto the zero level set, so hole nodes
are the ones at distance r from the hole center to 1e-6.
"""

import numpy
import torch

import KratosMultiphysics as Kratos
import KratosMultiphysics.ConvectionDiffusionApplication  # registers thermal variables  # noqa: F401
from KratosMultiphysics.ConvectionDiffusionApplication.convection_diffusion_analysis import (
    ConvectionDiffusionAnalysis)
from KratosMultiphysics.PhysicsNeMoApplication.mesh_bridge import generate

_HISTORICAL_VARIABLES = (
    "TEMPERATURE", "DENSITY", "SPECIFIC_HEAT", "CONDUCTIVITY", "HEAT_FLUX",
    "FACE_HEAT_FLUX", "PROJECTED_SCALAR1", "CONVECTION_VELOCITY",
    "TEMPERATURE_GRADIENT", "TRANSFER_COEFFICIENT", "REACTION",
    "VELOCITY", "MESH_VELOCITY", "REACTION_FLUX",
)


def _ProjectParameters(echo_level=0):
    return Kratos.Parameters("""{
        "problem_data": {
            "problem_name"  : "implicit_geometry_thermal",
            "parallel_type" : "OpenMP",
            "start_time"    : 0.0,
            "end_time"      : 0.99,
            "echo_level"    : %d
        },
        "solver_settings": {
            "solver_type"                        : "stationary",
            "analysis_type"                      : "linear",
            "model_part_name"                    : "ThermalModelPart",
            "domain_size"                        : 2,
            "model_import_settings"              : { "input_type" : "use_input_model_part" },
            "material_import_settings"           : { "materials_filename" : "" },
            "echo_level"                         : %d,
            "problem_domain_sub_model_part_list" : ["Domain"],
            "processes_sub_model_part_list"      : [],
            "convection_diffusion_variables"     : {
                "unknown_variable"       : "TEMPERATURE",
                "density_variable"       : "DENSITY",
                "specific_heat_variable" : "SPECIFIC_HEAT",
                "diffusion_variable"     : "CONDUCTIVITY",
                "volume_source_variable" : "HEAT_FLUX",
                "velocity_variable"      : "VELOCITY",
                "mesh_velocity_variable" : "MESH_VELOCITY",
                "reaction_variable"      : "REACTION_FLUX"
            },
            "time_stepping"                      : { "time_step" : 1.0 }
        },
        "processes"        : {},
        "output_processes" : {}
    }""" % (echo_level, echo_level))


def MakeShape(hole_center, hole_radius):
    """The family's SDF: unit box minus a disc. Negative inside the solid."""
    sdf = generate.SdfPrimitives()
    box = sdf["box"]((0.0, 0.0), (1.0, 1.0))
    hole = sdf["sphere"](tuple(hole_center), hole_radius)
    return sdf["difference"](box, hole)


def GenerateAndSolve(model: Kratos.Model, hole_center, hole_radius, h=0.05,
                     tolerance=1e-6):
    """SDF -> generated mesh -> Kratos model part -> stationary solve.

    Returns the solved model part (TEMPERATURE on its nodes).
    """
    phi = MakeShape(hole_center, hole_radius)
    mesh = generate.GenerateImplicitDomain(phi, ((0.0, 0.0), (1.0, 1.0)), h)
    part = generate.PopulateModelPartFromMesh(
        model, "ThermalModelPart", mesh, Kratos.Parameters(
            '{"historical_variables": %s, "buffer_size": 2}'
            % str(list(_HISTORICAL_VARIABLES)).replace("'", '"')))
    part.ProcessInfo[Kratos.DOMAIN_SIZE] = 2
    domain = part.CreateSubModelPart("Domain")
    domain.AddNodes([node.Id for node in part.Nodes])
    domain.AddElements([element.Id for element in part.Elements])

    center = numpy.asarray(hole_center, dtype=float)
    for node in part.Nodes:
        node.SetSolutionStepValue(Kratos.DENSITY, 1.0)
        node.SetSolutionStepValue(Kratos.SPECIFIC_HEAT, 1.0)
        node.SetSolutionStepValue(Kratos.CONDUCTIVITY, 1.0)
        node.SetSolutionStepValue(Kratos.HEAT_FLUX, 0.0)
        on_outer = (abs(node.X) < tolerance or abs(node.X - 1.0) < tolerance or
                    abs(node.Y) < tolerance or abs(node.Y - 1.0) < tolerance)
        on_hole = abs(numpy.hypot(node.X - center[0], node.Y - center[1])
                      - hole_radius) < tolerance
        if on_outer:
            node.Fix(Kratos.TEMPERATURE)
            node.SetSolutionStepValue(Kratos.TEMPERATURE, 0.0)
        elif on_hole:
            node.Fix(Kratos.TEMPERATURE)
            node.SetSolutionStepValue(Kratos.TEMPERATURE, 1.0)

    ConvectionDiffusionAnalysis(model, _ProjectParameters()).Run()
    return part


def FeatureLadder(part, hole_center, hole_radius):
    """(N, 6) surrogate inputs: x, y, phi, dphi/dx, dphi/dy, lap(phi).

    The geometry encoding is the 2-JET of the hole's signed distance
    function, computed entirely by autograd (the SDF primitives are
    differentiable closures): value = distance to the hole surface,
    gradient = unit direction away from the hole, Laplacian = 1/distance
    to the CENTER (in 2D) - together they localize the disc exactly, so
    the surrogate is never told (cx, cy, r) and still has no ambiguity.
    Column subsets give the ladder stage 1 compares: (x, y) blind,
    + value, + gradient, + Laplacian.

    The jet is taken on the HOLE's own SDF, not the composed shape: the
    box boundary is common to the whole family (nothing to encode), and
    min/max combinators have kinks whose second derivatives autograd
    NaNs on - measured, not theorized.
    """
    from KratosMultiphysics.PhysicsNeMoApplication.mesh_bridge import generate as _generate
    phi_hole = _generate.SdfPrimitives()["sphere"](tuple(hole_center), hole_radius)
    points = torch.tensor([[node.X, node.Y] for node in part.Nodes],
                          dtype=torch.float64, requires_grad=True)
    values = phi_hole(points)
    gradients = torch.autograd.grad(values.sum(), points, create_graph=True)[0]
    laplacian = torch.zeros(len(points), dtype=torch.float64)
    for direction in range(2):
        laplacian = laplacian + torch.autograd.grad(
            gradients[:, direction].sum(), points, retain_graph=True)[0][:, direction]
    return numpy.column_stack([
        points.detach().numpy(), values.detach().numpy()[:, None],
        gradients.detach().numpy(), laplacian.detach().numpy()[:, None]])


def Temperatures(part):
    return numpy.array([node.GetSolutionStepValue(Kratos.TEMPERATURE)
                        for node in part.Nodes])


def Triangulation(part):
    """matplotlib-ready (points, triangles) of the generated mesh."""
    ids = {node.Id: index for index, node in enumerate(part.Nodes)}
    points = numpy.array([[node.X, node.Y] for node in part.Nodes])
    triangles = numpy.array([[ids[node.Id] for node in element.GetGeometry()]
                             for element in part.Elements])
    return points, triangles
