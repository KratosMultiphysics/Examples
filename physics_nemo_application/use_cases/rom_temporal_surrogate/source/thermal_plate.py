"""A parametrized stationary heat-conduction case, built entirely in memory.

Unit-square plate, structured triangle mesh, TEMPERATURE = 0 clamped on the
whole boundary, uniform conductivity k and a *spatially varying* volumetric
heat source: a Gaussian bump of amplitude q centered at (cx, cy),

    f(x, y) = q * exp(-||(x, y) - (cx, cy)||^2 / (2 * width^2)),

so each case is the Poisson problem -k lap(u) = f solved by
ConvectionDiffusionApplication's stationary solver. The surrogate learns the
(k-field, f-field) -> u-field map, which makes the input genuinely a
*function* rather than a scalar: the same machinery transfers unchanged to
inputs that come from measurements or another solver.

Self-contained: no fixtures on disk, everything is generated here.
"""

import numpy

import KratosMultiphysics as Kratos
import KratosMultiphysics.ConvectionDiffusionApplication  # registers the thermal variables  # noqa: F401

# The complete variable set the stationary solver's AddVariables adds. With
# use_input_model_part the nodes exist before AddVariables runs, so every
# historical variable must be pre-added.
_HISTORICAL_VARIABLES = (
    "TEMPERATURE", "DENSITY", "SPECIFIC_HEAT", "CONDUCTIVITY", "HEAT_FLUX",
    "FACE_HEAT_FLUX", "PROJECTED_SCALAR1", "CONVECTION_VELOCITY",
    "TEMPERATURE_GRADIENT", "TRANSFER_COEFFICIENT", "REACTION",
    "VELOCITY", "MESH_VELOCITY", "REACTION_FLUX",
)


def _ProjectParameters(echo_level: int = 0) -> Kratos.Parameters:
    return Kratos.Parameters("""{
        "problem_data": {
            "problem_name"  : "thermal_plate",
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


def CreateModelPart(model: Kratos.Model, divisions: int = 32) -> Kratos.ModelPart:
    """The meshed model part (variables added before the mesh exists)."""
    model_part = model.CreateModelPart("ThermalModelPart")
    model_part.ProcessInfo[Kratos.DOMAIN_SIZE] = 2
    model_part.SetBufferSize(2)
    for name in _HISTORICAL_VARIABLES:
        model_part.AddNodalSolutionStepVariable(Kratos.KratosGlobals.GetVariable(name))

    generator_geometry = Kratos.Quadrilateral2D4(
        Kratos.Node(1, 0.0, 0.0, 0.0), Kratos.Node(2, 0.0, 1.0, 0.0),
        Kratos.Node(3, 1.0, 1.0, 0.0), Kratos.Node(4, 1.0, 0.0, 0.0))
    mesh_parameters = Kratos.Parameters("""{
        "number_of_divisions"        : %d,
        "element_name"               : "Element2D3N",
        "condition_name"             : "LineCondition",
        "create_skin_sub_model_part" : false
    }""" % divisions)
    domain = model_part.CreateSubModelPart("Domain")
    Kratos.StructuredMeshGeneratorProcess(generator_geometry, domain, mesh_parameters).Execute()
    return model_part


def ApplyCase(model_part: Kratos.ModelPart, conductivity: float,
              source_amplitude: float, source_center, source_width: float = 0.12,
              tolerance: float = 1e-8) -> None:
    """Material data, the Gaussian source and the Dirichlet boundary."""
    cx, cy = source_center
    for node in model_part.Nodes:
        node.SetSolutionStepValue(Kratos.DENSITY, 1.0)
        node.SetSolutionStepValue(Kratos.SPECIFIC_HEAT, 1.0)
        node.SetSolutionStepValue(Kratos.CONDUCTIVITY, conductivity)
        radius2 = (node.X - cx) ** 2 + (node.Y - cy) ** 2
        node.SetSolutionStepValue(
            Kratos.HEAT_FLUX,
            source_amplitude * numpy.exp(-radius2 / (2.0 * source_width ** 2)))
        on_boundary = (abs(node.X) < tolerance or abs(node.X - 1.0) < tolerance or
                       abs(node.Y) < tolerance or abs(node.Y - 1.0) < tolerance)
        if on_boundary:
            node.Fix(Kratos.TEMPERATURE)
            node.SetSolutionStepValue(Kratos.TEMPERATURE, 0.0)


def _TransientProjectParameters(time_step: float, end_time: float,
                                echo_level: int = 0) -> Kratos.Parameters:
    parameters = _ProjectParameters(echo_level)
    solver = parameters["solver_settings"]
    solver["solver_type"].SetString("transient")
    solver["time_stepping"]["time_step"].SetDouble(time_step)
    parameters["problem_data"]["end_time"].SetDouble(end_time)
    transient = solver.AddEmptyValue("transient_parameters")
    transient.AddEmptyValue("theta").SetDouble(0.5)
    transient.AddEmptyValue("dynamic_tau").SetDouble(0.0)
    transient.AddEmptyValue("cross_wind_stabilization_factor").SetDouble(0.0)
    return parameters


def CreateTransientAnalysis(model: Kratos.Model, conductivity: float,
                            source_amplitude: float, source_center,
                            divisions: int = 32, time_step: float = 0.005,
                            end_time: float = 0.2, echo_level: int = 0):
    """The same case run by the TRANSIENT solver, heating from zero.

    Returns the (not yet Initialized) analysis; drive it with
    RunTransientAnalysis to collect or act per step.
    """
    from KratosMultiphysics.ConvectionDiffusionApplication.convection_diffusion_analysis import (
        ConvectionDiffusionAnalysis)

    model_part = CreateModelPart(model, divisions)
    ApplyCase(model_part, conductivity, source_amplitude, source_center)
    return ConvectionDiffusionAnalysis(
        model, _TransientProjectParameters(time_step, end_time, echo_level))


def RunTransientAnalysis(analysis, per_step=None):
    """AnalysisStage.RunSolutionLoop opened up: per_step(model_part) runs
    after every converged step (collect states, drive processes, ...)."""
    analysis.Initialize()
    model_part = analysis._GetSolver().GetComputingModelPart()
    while analysis.KeepAdvancingSolutionLoop():
        analysis.time = analysis._AdvanceTime()
        analysis.InitializeSolutionStep()
        analysis.SolveSolutionStep()
        analysis.FinalizeSolutionStep()
        analysis.OutputSolutionStep()
        if per_step is not None:
            per_step(model_part)
    analysis.Finalize()


def Solve(conductivity: float, source_amplitude: float, source_center,
          divisions: int = 32, echo_level: int = 0):
    """Runs one stationary solve; returns (model, model_part).

    The model is returned as well because Kratos ties the model part's
    lifetime to it - dropping the model invalidates the part.
    """
    from KratosMultiphysics.ConvectionDiffusionApplication.convection_diffusion_analysis import (
        ConvectionDiffusionAnalysis)

    model = Kratos.Model()
    model_part = CreateModelPart(model, divisions)
    ApplyCase(model_part, conductivity, source_amplitude, source_center)
    ConvectionDiffusionAnalysis(model, _ProjectParameters(echo_level)).Run()
    return model, model_part


def SampleCases(count: int, seed: int):
    """Reproducible parameter draws: k, q and the source center."""
    rng = numpy.random.default_rng(seed)
    return [{
        "conductivity": float(rng.uniform(0.5, 2.0)),
        "source_amplitude": float(rng.uniform(0.5, 1.5)),
        "source_center": (float(rng.uniform(0.3, 0.7)), float(rng.uniform(0.3, 0.7))),
    } for _ in range(count)]
