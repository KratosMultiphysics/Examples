"""Geometrically nonlinear cantilever, built entirely in memory.

The same thin strip as the application's structural test fixture (length 1,
height 0.1, plane strain, clamped at x = 0, vertical tip load), but meshed
with TotalLagrangianElement2D3N: finite-strain kinematics make the static
problem genuinely NONLINEAR, so the solver is Newton-Raphson and the
iteration count is a real cost that a warm start can reduce.

Two solver details matter for warm starting and are set here on purpose:

* residual_criterion GOVERNED BY THE ABSOLUTE tolerance (the relative
  tolerance is set unreachably tight). A relative criterion divides by
  the INITIAL residual, so a warm start - whose initial residual is small
  - would face a harsher target than a cold one and can even take MORE
  iterations; only an absolute target makes the two runs comparable.
  (Found by measurement: with the stock relative criterion the warm runs
  saved nothing.)
* NL_ITERATION_NUMBER read from ProcessInfo after the solve: the
  Newton-Raphson strategy stores the iterations it actually spent.
"""

import KratosMultiphysics as Kratos

LENGTH = 1.0
HEIGHT = 0.1

_CORE_HISTORICAL_VARIABLES = (
    "DISPLACEMENT", "REACTION", "POSITIVE_FACE_PRESSURE",
    "NEGATIVE_FACE_PRESSURE", "VOLUME_ACCELERATION", "VELOCITY", "ACCELERATION",
)
_APP_HISTORICAL_VARIABLES = ("POINT_LOAD", "LINE_LOAD", "SURFACE_LOAD")


def _ProjectParameters(echo_level=0):
    return Kratos.Parameters("""{
        "problem_data": {
            "problem_name"  : "hybrid_initialization_cantilever",
            "parallel_type" : "OpenMP",
            "start_time"    : 0.0,
            "end_time"      : 0.99,
            "echo_level"    : %d
        },
        "solver_settings": {
            "solver_type"                  : "Static",
            "analysis_type"                : "non_linear",
            "model_part_name"              : "StructuralModelPart",
            "domain_size"                  : 2,
            "model_import_settings"        : { "input_type" : "use_input_model_part" },
            "material_import_settings"     : { "materials_filename" : "" },
            "echo_level"                   : %d,
            "rotation_dofs"                : false,
            "max_iteration"                : 30,
            "convergence_criterion"        : "residual_criterion",
            "residual_relative_tolerance"  : 1e-12,
            "residual_absolute_tolerance"  : 1e-2,
            "time_stepping"                : { "time_step" : 1.0 }
        },
        "processes"        : {},
        "output_processes" : {}
    }""" % (echo_level, echo_level))


def CreateModelPart(model: Kratos.Model, divisions: int = 8) -> Kratos.ModelPart:
    """The meshed cantilever with TotalLagrangian (finite strain) elements."""
    import KratosMultiphysics.StructuralMechanicsApplication as SMA

    model_part = model.CreateModelPart("StructuralModelPart")
    model_part.ProcessInfo[Kratos.DOMAIN_SIZE] = 2
    model_part.SetBufferSize(2)
    for name in _CORE_HISTORICAL_VARIABLES:
        model_part.AddNodalSolutionStepVariable(Kratos.KratosGlobals.GetVariable(name))
    for name in _APP_HISTORICAL_VARIABLES:
        model_part.AddNodalSolutionStepVariable(getattr(SMA, name))

    generator_geometry = Kratos.Quadrilateral2D4(
        Kratos.Node(1, 0.0, 0.0, 0.0), Kratos.Node(2, 0.0, HEIGHT, 0.0),
        Kratos.Node(3, LENGTH, HEIGHT, 0.0), Kratos.Node(4, LENGTH, 0.0, 0.0))
    mesh_parameters = Kratos.Parameters("""{
        "number_of_divisions"        : %d,
        "element_name"               : "TotalLagrangianElement2D3N",
        "condition_name"             : "LineCondition",
        "create_skin_sub_model_part" : false
    }""" % divisions)
    domain = model_part.CreateSubModelPart("Domain")
    Kratos.StructuredMeshGeneratorProcess(generator_geometry, domain, mesh_parameters).Execute()

    properties = next(iter(domain.Elements)).Properties
    properties.SetValue(Kratos.YOUNG_MODULUS, 210.0e9)
    properties.SetValue(Kratos.POISSON_RATIO, 0.3)
    properties.SetValue(Kratos.CONSTITUTIVE_LAW, SMA.LinearElasticPlaneStrain2DLaw())
    return model_part


def ApplyCaseData(model_part: Kratos.ModelPart, tip_load: float, tolerance: float = 1e-8) -> None:
    """Clamps x = 0 and spreads a downward tip_load over the x = LENGTH edge."""
    import KratosMultiphysics.StructuralMechanicsApplication as SMA

    tip_nodes = [node for node in model_part.Nodes if abs(node.X - LENGTH) < tolerance]
    properties = next(iter(model_part.Elements)).Properties
    condition_id = model_part.NumberOfConditions()
    for node in model_part.Nodes:
        if abs(node.X) < tolerance:
            node.Fix(Kratos.DISPLACEMENT_X)
            node.Fix(Kratos.DISPLACEMENT_Y)
            node.SetSolutionStepValue(Kratos.DISPLACEMENT, [0.0, 0.0, 0.0])
    domain = model_part.GetSubModelPart("Domain")
    for node in tip_nodes:
        node.SetSolutionStepValue(SMA.POINT_LOAD, [0.0, -tip_load / len(tip_nodes), 0.0])
        condition_id += 1
        domain.CreateNewCondition("PointLoadCondition2D1N", condition_id, [node.Id], properties)


def CreateAnalysis(model: Kratos.Model, tip_load: float, divisions: int = 8,
                   echo_level: int = 0, extra_processes=None):
    """Builds the cantilever and returns a ready StructuralMechanicsAnalysis.

    extra_processes: a Parameters LIST appended as an auxiliar_process_list -
    the hook the warm-started runs use to attach HybridInitializationProcess
    exactly the way any Kratos process is attached.
    """
    from KratosMultiphysics.StructuralMechanicsApplication.structural_mechanics_analysis import (
        StructuralMechanicsAnalysis)

    model_part = CreateModelPart(model, divisions)
    ApplyCaseData(model_part, tip_load)
    parameters = _ProjectParameters(echo_level)
    if extra_processes is not None:
        parameters["processes"].AddValue("auxiliar_process_list", extra_processes)
    return StructuralMechanicsAnalysis(model, parameters), model_part


def GetTipDeflection(model_part: Kratos.ModelPart, tolerance: float = 1e-8) -> float:
    tip_values = [node.GetSolutionStepValue(Kratos.DISPLACEMENT_Y)
                  for node in model_part.Nodes if abs(node.X0 - LENGTH) < tolerance]
    return sum(tip_values) / len(tip_values)
