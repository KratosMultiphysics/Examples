"""A parametrized 3D heat-conduction case, built entirely in memory.

Unit cube, structured tetrahedral mesh, TEMPERATURE = 0 clamped on the whole
boundary, uniform conductivity and a Gaussian volumetric source at a
parametrized 3D center - the Poisson problem in three dimensions, solved by
ConvectionDiffusionApplication's stationary solver. The diffusion model
learns coarse-field -> fine-field on full 3D voxel grids, which is exactly
what the volumetric DiffusionUNet3D denoiser exists for.

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


def CreateModelPart(model: Kratos.Model, divisions: int = 12) -> Kratos.ModelPart:
    """The meshed model part (variables added before the mesh exists)."""
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
    return model_part


def ApplyCase(model_part: Kratos.ModelPart, conductivity: float,
              source_amplitude: float, source_center, source_width: float = 0.15,
              tolerance: float = 1e-8) -> None:
    """Material data, the 3D Gaussian source and the Dirichlet boundary."""
    cx, cy, cz = source_center
    for node in model_part.Nodes:
        node.SetSolutionStepValue(Kratos.DENSITY, 1.0)
        node.SetSolutionStepValue(Kratos.SPECIFIC_HEAT, 1.0)
        node.SetSolutionStepValue(Kratos.CONDUCTIVITY, conductivity)
        radius2 = ((node.X - cx) ** 2 + (node.Y - cy) ** 2 + (node.Z - cz) ** 2)
        node.SetSolutionStepValue(
            Kratos.HEAT_FLUX,
            source_amplitude * numpy.exp(-radius2 / (2.0 * source_width ** 2)))
        on_boundary = (abs(node.X) < tolerance or abs(node.X - 1.0) < tolerance or
                       abs(node.Y) < tolerance or abs(node.Y - 1.0) < tolerance or
                       abs(node.Z) < tolerance or abs(node.Z - 1.0) < tolerance)
        if on_boundary:
            node.Fix(Kratos.TEMPERATURE)
            node.SetSolutionStepValue(Kratos.TEMPERATURE, 0.0)


def Solve(conductivity: float, source_amplitude: float, source_center,
          divisions: int = 12, echo_level: int = 0):
    """Runs one stationary 3D solve; returns (model, model_part)."""
    from KratosMultiphysics.ConvectionDiffusionApplication.convection_diffusion_analysis import (
        ConvectionDiffusionAnalysis)

    model = Kratos.Model()
    model_part = CreateModelPart(model, divisions)
    ApplyCase(model_part, conductivity, source_amplitude, source_center)
    ConvectionDiffusionAnalysis(model, _ProjectParameters(echo_level)).Run()
    return model, model_part


def SampleCases(count: int, seed: int):
    """Reproducible parameter draws: k, q and the 3D source center."""
    rng = numpy.random.default_rng(seed)
    return [{
        "conductivity": float(rng.uniform(0.5, 2.0)),
        "source_amplitude": float(rng.uniform(0.5, 1.5)),
        "source_center": tuple(float(v) for v in rng.uniform(0.35, 0.65, size=3)),
    } for _ in range(count)]
