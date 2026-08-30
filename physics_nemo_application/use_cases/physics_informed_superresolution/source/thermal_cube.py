"""Stationary 3D heat conduction on a unit cube, built entirely in memory.

-k lap(u) = f with u = 0 on all six faces, uniform conductivity k and
uniform source f, on a structured tetrahedral mesh (each hex cell split
into six tets). The 3D counterpart of the 2D plate used by the other
examples; the uniform coefficients make the PDE residual expressible by
physicsnemo.sym's builtin diffusion PDE, which the physics-informed
training uses.
"""

import numpy

import KratosMultiphysics as Kratos
import KratosMultiphysics.ConvectionDiffusionApplication  # registers the thermal variables  # noqa: F401

_HISTORICAL_VARIABLES = (
    "TEMPERATURE", "DENSITY", "SPECIFIC_HEAT", "CONDUCTIVITY", "HEAT_FLUX",
    "FACE_HEAT_FLUX", "PROJECTED_SCALAR1", "CONVECTION_VELOCITY",
    "TEMPERATURE_GRADIENT", "TRANSFER_COEFFICIENT", "REACTION",
    "VELOCITY", "MESH_VELOCITY", "REACTION_FLUX",
)

_HEX_TO_TETS = ((0, 1, 2, 6), (0, 2, 3, 6), (0, 3, 7, 6),
                (0, 7, 4, 6), (0, 4, 5, 6), (0, 5, 1, 6))


def _ProjectParameters(echo_level: int = 0) -> Kratos.Parameters:
    return Kratos.Parameters("""{
        "problem_data": {
            "problem_name"  : "thermal_cube",
            "parallel_type" : "OpenMP",
            "start_time"    : 0.0,
            "end_time"      : 0.99,
            "echo_level"    : %d
        },
        "solver_settings": {
            "solver_type"                        : "stationary",
            "analysis_type"                      : "linear",
            "model_part_name"                    : "ThermalModelPart",
            "domain_size"                        : 3,
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


def CreateModelPart(model: Kratos.Model, divisions: int) -> Kratos.ModelPart:
    """A tet-filled unit cube with (divisions + 1)^3 nodes, (i, j, k) order."""
    model_part = model.CreateModelPart("ThermalModelPart")
    model_part.ProcessInfo[Kratos.DOMAIN_SIZE] = 3
    model_part.SetBufferSize(2)
    for name in _HISTORICAL_VARIABLES:
        model_part.AddNodalSolutionStepVariable(Kratos.KratosGlobals.GetVariable(name))

    domain = model_part.CreateSubModelPart("Domain")
    properties = model_part.CreateNewProperties(1)
    n = divisions + 1
    for i in range(n):
        for j in range(n):
            for k in range(n):
                domain.CreateNewNode(i * n * n + j * n + k + 1,
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
                    domain.CreateNewElement(
                        "Element3D4N", element, [corners[c] for c in tet], properties)
    return model_part


def ApplyCase(model_part: Kratos.ModelPart, conductivity: float,
              heat_flux: float, tolerance: float = 1e-8) -> None:
    for node in model_part.Nodes:
        node.SetSolutionStepValue(Kratos.DENSITY, 1.0)
        node.SetSolutionStepValue(Kratos.SPECIFIC_HEAT, 1.0)
        node.SetSolutionStepValue(Kratos.CONDUCTIVITY, conductivity)
        node.SetSolutionStepValue(Kratos.HEAT_FLUX, heat_flux)
        on_boundary = any(abs(value) < tolerance or abs(value - 1.0) < tolerance
                          for value in (node.X, node.Y, node.Z))
        if on_boundary:
            node.Fix(Kratos.TEMPERATURE)
            node.SetSolutionStepValue(Kratos.TEMPERATURE, 0.0)


def Solve(conductivity: float, heat_flux: float, divisions: int, echo_level: int = 0):
    """One stationary 3D solve; returns (model, model_part)."""
    from KratosMultiphysics.ConvectionDiffusionApplication.convection_diffusion_analysis import (
        ConvectionDiffusionAnalysis)

    model = Kratos.Model()
    model_part = CreateModelPart(model, divisions)
    ApplyCase(model_part, conductivity, heat_flux)
    ConvectionDiffusionAnalysis(model, _ProjectParameters(echo_level)).Run()
    return model, model_part


def NodeGrid(model_part, divisions):
    """The solved TEMPERATURE as an (n, n, n) grid in (i, j, k) node order."""
    n = divisions + 1
    values = numpy.array([node.GetSolutionStepValue(Kratos.TEMPERATURE)
                          for node in model_part.Nodes])
    return values.reshape(n, n, n)
