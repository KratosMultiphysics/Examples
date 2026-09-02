"""A transient heat-conduction case with a moving source, built in memory.

Unit-square plate, structured triangle mesh, TEMPERATURE = 0 clamped on the
boundary, uniform conductivity, and a Gaussian volumetric source whose
center travels along a circle - so the temperature field is a genuinely
transient, advecting hot spot: something worth scrubbing through in a
digital twin.

Self-contained: no fixtures on disk, everything is generated here.
"""

import numpy

import KratosMultiphysics as Kratos
import KratosMultiphysics.ConvectionDiffusionApplication  # registers the thermal variables  # noqa: F401

# The complete variable set the transient solver's AddVariables adds. With
# use_input_model_part the nodes exist before AddVariables runs, so every
# historical variable must be pre-added.
_HISTORICAL_VARIABLES = (
    "TEMPERATURE", "DENSITY", "SPECIFIC_HEAT", "CONDUCTIVITY", "HEAT_FLUX",
    "FACE_HEAT_FLUX", "PROJECTED_SCALAR1", "CONVECTION_VELOCITY",
    "TEMPERATURE_GRADIENT", "TRANSFER_COEFFICIENT", "REACTION",
    "VELOCITY", "MESH_VELOCITY", "REACTION_FLUX",
    # the twin's extra passengers: the surrogate's prediction + its spread
    "NODAL_PAUX", "NODAL_ERROR",
)


def ProjectParameters(end_time: float, time_step: float, echo_level: int = 0) -> Kratos.Parameters:
    parameters = Kratos.Parameters("""{
        "problem_data": {
            "problem_name"  : "twin_plate",
            "parallel_type" : "OpenMP",
            "start_time"    : 0.0,
            "end_time"      : 1.0,
            "echo_level"    : 0
        },
        "solver_settings": {
            "solver_type"                        : "transient",
            "analysis_type"                      : "linear",
            "model_part_name"                    : "ThermalModelPart",
            "domain_size"                        : 2,
            "model_import_settings"              : { "input_type" : "use_input_model_part" },
            "material_import_settings"           : { "materials_filename" : "" },
            "echo_level"                         : 0,
            "problem_domain_sub_model_part_list" : ["Domain"],
            "processes_sub_model_part_list"      : [],
            "transient_parameters"               : {
                "theta"                           : 0.5,
                "dynamic_tau"                     : 0.0,
                "cross_wind_stabilization_factor" : 0.0
            },
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
            "time_stepping"                      : { "time_step" : 0.04 }
        },
        "processes"        : {},
        "output_processes" : {}
    }""")
    parameters["problem_data"]["end_time"].SetDouble(end_time)
    parameters["problem_data"]["echo_level"].SetInt(echo_level)
    parameters["solver_settings"]["echo_level"].SetInt(echo_level)
    parameters["solver_settings"]["time_stepping"]["time_step"].SetDouble(time_step)
    return parameters


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


def SourceCenter(time: float, period: float = 1.0):
    """The Gaussian source's center: a circle of radius 0.22 around the middle."""
    angle = 2.0 * numpy.pi * time / period
    return 0.5 + 0.22 * numpy.cos(angle), 0.5 + 0.22 * numpy.sin(angle)


def ApplyMaterialAndBoundary(model_part: Kratos.ModelPart, conductivity: float = 1.0,
                             tolerance: float = 1e-8) -> None:
    for node in model_part.Nodes:
        node.SetSolutionStepValue(Kratos.DENSITY, 1.0)
        node.SetSolutionStepValue(Kratos.SPECIFIC_HEAT, 1.0)
        node.SetSolutionStepValue(Kratos.CONDUCTIVITY, conductivity)
        on_boundary = (abs(node.X) < tolerance or abs(node.X - 1.0) < tolerance or
                       abs(node.Y) < tolerance or abs(node.Y - 1.0) < tolerance)
        if on_boundary:
            node.Fix(Kratos.TEMPERATURE)
            node.SetSolutionStepValue(Kratos.TEMPERATURE, 0.0)


def UpdateSource(model_part: Kratos.ModelPart, time: float,
                 amplitude: float = 25.0, width: float = 0.1) -> None:
    """The moving Gaussian source at the given time."""
    cx, cy = SourceCenter(time)
    for node in model_part.Nodes:
        radius2 = (node.X - cx) ** 2 + (node.Y - cy) ** 2
        node.SetSolutionStepValue(
            Kratos.HEAT_FLUX, amplitude * numpy.exp(-radius2 / (2.0 * width ** 2)))


def CreateAnalysis(model: Kratos.Model, end_time: float, time_step: float,
                   divisions: int = 32, echo_level: int = 0, processes=None):
    """(analysis, model_part), initialized and ready for a manual time loop.

    processes: optional Kratos Parameters LIST attached as the analysis's
    process list - the ordinary ProjectParameters way, so the twin exporter
    and the surrogate run exactly as they would in a production case.
    """
    from KratosMultiphysics.ConvectionDiffusionApplication.convection_diffusion_analysis import (
        ConvectionDiffusionAnalysis)

    model_part = CreateModelPart(model, divisions)
    ApplyMaterialAndBoundary(model_part)
    UpdateSource(model_part, 0.0)
    parameters = ProjectParameters(end_time, time_step, echo_level)
    if processes is not None:
        parameters["processes"].AddValue("auxiliar_process_list", processes)
    analysis = ConvectionDiffusionAnalysis(model, parameters)
    analysis.Initialize()
    return analysis, model_part


def RunTimeLoop(analysis, model_part, per_step=None) -> None:
    """AnalysisStage.RunSolutionLoop's own sequence, opened up so the moving
    source is refreshed each step (and a hook can record extras after each
    converged step). Same pattern as the application's transient_harness.
    """
    while analysis.KeepAdvancingSolutionLoop():
        analysis.time = analysis._AdvanceTime()
        # refresh the source BEFORE InitializeSolutionStep, so processes that
        # gather at initialize_solution_step (the surrogate) see this step's q
        UpdateSource(model_part, model_part.ProcessInfo[Kratos.TIME])
        analysis.InitializeSolutionStep()
        analysis.SolveSolutionStep()
        analysis.FinalizeSolutionStep()
        analysis.OutputSolutionStep()
        if per_step is not None:
            per_step(model_part)
    analysis.Finalize()
