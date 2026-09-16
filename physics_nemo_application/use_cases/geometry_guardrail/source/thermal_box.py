"""A parametrized 3D heat-conduction case on a box of variable proportions.

The same stationary Poisson problem as the other 3D thermal helpers - a
Gaussian volumetric source, TEMPERATURE = 0 clamped on the whole boundary -
but the DOMAIN's side lengths are the parameter. That is what the geometry
guardrail exists to notice: a surrogate trained on a family of nearly cubic
boxes has no way of knowing it has been handed a slab, because the field
VALUES it reads stay perfectly in range.

The mesh is generated on the unit cube and then scaled, which keeps the
element count and node ordering identical across the family - so any
difference the guardrail reports is a difference in SHAPE, not in
discretization.

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


def _ProjectParameters(echo_level: int = 0) -> Kratos.Parameters:
    return Kratos.Parameters("""{
        "problem_data": {
            "problem_name"  : "thermal_box",
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


def CreateModelPart(model: Kratos.Model, scale, divisions: int = 6) -> Kratos.ModelPart:
    """A box of the given side lengths, meshed on the unit cube and scaled.

    Scaling after generation (rather than generating on the box directly)
    keeps the topology identical for every member of the family, so the
    guardrail's verdicts cannot be explained by a changed mesh.
    """
    scale = numpy.asarray(scale, dtype=float)
    if scale.shape != (3,) or (scale <= 0.0).any():
        raise ValueError(f"scale must be three positive side lengths; got {scale}.")

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
        "create_skin_sub_model_part" : false
    }""" % divisions)
    domain = model_part.CreateSubModelPart("Domain")
    Kratos.StructuredMeshGeneratorProcess(generator_geometry, domain, mesh_parameters).Execute()

    # both the reference and the current configuration, or the solver and
    # the mesh bridge would disagree about where the nodes are
    for node in model_part.Nodes:
        node.X0, node.Y0, node.Z0 = (node.X0 * scale[0], node.Y0 * scale[1],
                                     node.Z0 * scale[2])
        node.X, node.Y, node.Z = node.X0, node.Y0, node.Z0
    return model_part


def ApplyCase(model_part: Kratos.ModelPart, scale, conductivity: float,
              source_amplitude: float, tolerance: float = 1e-8) -> None:
    """Material data, a centred Gaussian source and the Dirichlet boundary."""
    scale = numpy.asarray(scale, dtype=float)
    center = 0.5 * scale
    width = 0.15 * float(scale.min())   # the source stays inside the thinnest axis
    for node in model_part.Nodes:
        node.SetSolutionStepValue(Kratos.DENSITY, 1.0)
        node.SetSolutionStepValue(Kratos.SPECIFIC_HEAT, 1.0)
        node.SetSolutionStepValue(Kratos.CONDUCTIVITY, conductivity)
        radius2 = ((node.X - center[0]) ** 2 + (node.Y - center[1]) ** 2
                   + (node.Z - center[2]) ** 2)
        node.SetSolutionStepValue(
            Kratos.HEAT_FLUX,
            source_amplitude * numpy.exp(-radius2 / (2.0 * width ** 2)))
        on_boundary = (abs(node.X) < tolerance or abs(node.X - scale[0]) < tolerance or
                       abs(node.Y) < tolerance or abs(node.Y - scale[1]) < tolerance or
                       abs(node.Z) < tolerance or abs(node.Z - scale[2]) < tolerance)
        if on_boundary:
            node.Fix(Kratos.TEMPERATURE)
            node.SetSolutionStepValue(Kratos.TEMPERATURE, 0.0)


def Solve(scale, conductivity: float = 1.0, source_amplitude: float = 1.0,
          divisions: int = 6, echo_level: int = 0):
    """Runs one stationary solve on a box; returns (model, model_part).

    The model is returned as well because Kratos ties the model part's
    lifetime to it - dropping the model invalidates the part.
    """
    from KratosMultiphysics.ConvectionDiffusionApplication.convection_diffusion_analysis import (
        ConvectionDiffusionAnalysis)

    model = Kratos.Model()
    model_part = CreateModelPart(model, scale, divisions)
    ApplyCase(model_part, scale, conductivity, source_amplitude)
    ConvectionDiffusionAnalysis(model, _ProjectParameters(echo_level)).Run()
    return model, model_part


def SampleFamily(count: int, seed: int, spread: float = 0.15):
    """The training family: boxes whose sides are 1 +/- spread.

    Nearly cubic, but not a repeated cube - a density model fitted to a
    family with no variation at all has nothing to measure distance against.
    """
    rng = numpy.random.default_rng(seed)
    return [{
        "scale": tuple(float(v) for v in rng.uniform(1.0 - spread, 1.0 + spread, size=3)),
        "conductivity": float(rng.uniform(0.8, 1.2)),
        "source_amplitude": float(rng.uniform(0.8, 1.2)),
    } for _ in range(count)]
