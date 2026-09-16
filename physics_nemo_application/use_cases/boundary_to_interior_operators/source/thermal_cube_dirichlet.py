"""A 3D Laplace problem driven entirely by its top-face boundary data.

Unit cube, structured tetrahedral mesh, TEMPERATURE fixed on the whole
skin: zero on five faces, and on the top face a Gaussian bump

    T(x, y, 1) = A * exp(-((x - cx)^2 + (y - cy)^2) / (2 w^2)),

so the interior field is determined by nothing but the boundary values -
which is exactly the structure GLOBE's Green's-function-like kernels are
built for, and what makes this a fair test of "boundary in, interior out".
The same cases also serve the parameters-in operator (xDeepONet), whose
branch input is the triple (cx, cy, A).

Two details found by probing rather than assumed:

* `StructuredMeshGeneratorProcess` is handed the `Domain` SUB-model-part
  here, so the skin it creates is nested as `Domain.Skin`, not `Skin` on
  the root. Looking for it at the root finds nothing and silently leaves
  the boundary empty.
* The generated `SurfaceCondition` elements do not disturb the thermal
  assembly - the stationary solver runs with them present (verified: the
  interior of a 0/1 Dirichlet cube settles at a mean of 0.235).

Self-contained: no fixtures on disk, everything is generated here.
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

TOP_BOUNDARY_NAME = "Top"


def _ProjectParameters(echo_level: int = 0) -> Kratos.Parameters:
    return Kratos.Parameters("""{
        "problem_data": {
            "problem_name"  : "thermal_cube_dirichlet",
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


def CreateModelPart(model: Kratos.Model, divisions: int = 6) -> Kratos.ModelPart:
    """The meshed unit cube, with its skin and a named top boundary."""
    model_part = model.CreateModelPart("ThermalModelPart")
    model_part.ProcessInfo[Kratos.DOMAIN_SIZE] = 3
    model_part.SetBufferSize(2)
    for name in _HISTORICAL_VARIABLES:
        model_part.AddNodalSolutionStepVariable(Kratos.KratosGlobals.GetVariable(name))

    generator_geometry = Kratos.Hexahedra3D8(
        Kratos.Node(1, 0.0, 0.0, 0.0), Kratos.Node(2, 1.0, 0.0, 0.0),
        Kratos.Node(3, 1.0, 1.0, 0.0), Kratos.Node(4, 0.0, 1.0, 0.0),
        Kratos.Node(5, 0.0, 0.0, 1.0), Kratos.Node(6, 1.0, 0.0, 1.0),
        Kratos.Node(7, 1.0, 1.0, 1.0), Kratos.Node(8, 0.0, 1.0, 1.0))
    mesh_parameters = Kratos.Parameters("""{
        "number_of_divisions"        : %d,
        "element_name"               : "Element3D4N",
        "condition_name"             : "SurfaceCondition",
        "create_skin_sub_model_part" : true
    }""" % divisions)
    domain = model_part.CreateSubModelPart("Domain")
    Kratos.StructuredMeshGeneratorProcess(generator_geometry, domain, mesh_parameters).Execute()
    _CreateTopBoundary(model_part, domain)
    return model_part


def _CreateTopBoundary(model_part: Kratos.ModelPart, domain: Kratos.ModelPart,
                       tolerance: float = 1e-9) -> Kratos.ModelPart:
    """The z = 1 face as its own sub-model-part, for GLOBE to read.

    The generator nests its skin under the part it was given, so the skin
    is `Domain.Skin`; a lookup on the root silently finds nothing.
    """
    skin = domain.GetSubModelPart("Skin") if domain.HasSubModelPart("Skin") else domain
    top = model_part.CreateSubModelPart(TOP_BOUNDARY_NAME)
    condition_ids = [condition.Id for condition in skin.Conditions
                     if all(abs(node.Z - 1.0) < tolerance for node in condition.GetNodes())]
    if not condition_ids:
        raise ValueError("No skin conditions found on the z = 1 face; the mesh is not "
                         "what this case expects.")
    node_ids = sorted({node.Id for condition in skin.Conditions
                       if condition.Id in set(condition_ids)
                       for node in condition.GetNodes()})
    top.AddNodes(node_ids)
    top.AddConditions(condition_ids)
    return top


def ApplyCase(model_part: Kratos.ModelPart, center, amplitude: float,
              width: float = 0.18, conductivity: float = 1.0,
              tolerance: float = 1e-9) -> None:
    """Dirichlet data: a Gaussian bump on the top face, zero elsewhere."""
    cx, cy = center
    for node in model_part.Nodes:
        node.SetSolutionStepValue(Kratos.DENSITY, 1.0)
        node.SetSolutionStepValue(Kratos.SPECIFIC_HEAT, 1.0)
        node.SetSolutionStepValue(Kratos.CONDUCTIVITY, conductivity)
        node.SetSolutionStepValue(Kratos.HEAT_FLUX, 0.0)   # no source: boundary-driven
        on_boundary = (abs(node.X) < tolerance or abs(node.X - 1.0) < tolerance or
                       abs(node.Y) < tolerance or abs(node.Y - 1.0) < tolerance or
                       abs(node.Z) < tolerance or abs(node.Z - 1.0) < tolerance)
        if not on_boundary:
            continue
        if abs(node.Z - 1.0) < tolerance:
            radius2 = (node.X - cx) ** 2 + (node.Y - cy) ** 2
            value = amplitude * numpy.exp(-radius2 / (2.0 * width ** 2))
        else:
            value = 0.0
        node.Fix(Kratos.TEMPERATURE)
        node.SetSolutionStepValue(Kratos.TEMPERATURE, float(value))


def Solve(center, amplitude: float, divisions: int = 6, width: float = 0.18,
          conductivity: float = 1.0, echo_level: int = 0):
    """Runs one boundary-driven solve; returns (model, model_part).

    The model is returned as well because Kratos ties the model part's
    lifetime to it - dropping the model invalidates the part.
    """
    from KratosMultiphysics.ConvectionDiffusionApplication.convection_diffusion_analysis import (
        ConvectionDiffusionAnalysis)

    model = Kratos.Model()
    model_part = CreateModelPart(model, divisions)
    ApplyCase(model_part, center, amplitude, width, conductivity)
    ConvectionDiffusionAnalysis(model, _ProjectParameters(echo_level)).Run()
    return model, model_part


def SampleCases(count: int, seed: int):
    """Reproducible draws of the boundary parameters (cx, cy, A).

    These are both the GLOBE boundary data and the xDeepONet branch input,
    so the two operators see exactly the same family.
    """
    rng = numpy.random.default_rng(seed)
    return [{
        "center": (float(rng.uniform(0.3, 0.7)), float(rng.uniform(0.3, 0.7))),
        "amplitude": float(rng.uniform(0.6, 1.4)),
    } for _ in range(count)]
