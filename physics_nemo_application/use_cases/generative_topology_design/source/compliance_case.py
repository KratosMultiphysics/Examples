"""A SIMP compliance case, and an optimality-criteria loop over real solves.

The ground truth behind generative topology design. Each element of a
plane-stress square carries its own Young's modulus through the SIMP
interpolation E = E_min + rho^p (E_0 - E_min), so a DENSITY FIELD is the
design variable and the structure's compliance f.u is what a design is
judged by. That gives a generative model something real to be conditioned
on and scored against, with no optimization application required.

`OptimizeSimp` is the classical optimality-criteria loop - filter the
sensitivities, update the densities, bisect on the volume multiplier -
with Kratos solving every iteration. Its output is the training data: a
family of genuine SIMP optima, one per load position, rather than pictures
of structures.

TWO LAYOUT FACTS, because getting either wrong is silent. The element
array runs two triangles per structured cell, so a per-cell field is
`numpy.repeat(cells, 2)`. And `DensityGrid`'s FIRST index runs along x,
the second along y - the clamped edge (x = 0) is a row of the first index.
`ConstraintChannels` is written in that same layout; writing it the other
way round transposes the conditioning against the design image without
changing either channel's sum, which is exactly the kind of mistake a
sum-only check cannot see.

Built entirely in memory, like the other cases here, so every
solution-step variable is added before the mesh exists. Per-element
properties are the mechanism: the structured mesh generator gives every
element ONE shared Properties object, so each element is given a fresh one
(the constitutive law included, since the law lives on the properties)
before its modulus is set.
"""

import numpy

import KratosMultiphysics as Kratos

_LENGTH = 1.0
_HEIGHT = 1.0
_YOUNG_MODULUS = 1.0e9
_MINIMUM_MODULUS = 1.0e6      # keeps the void stiff enough to stay solvable
_POISSON_RATIO = 0.3
_PENALIZATION = 3.0           # the "p" of SIMP
_TIP_LOAD = -1.0e4
_MINIMUM_DENSITY = 0.2

_CORE_HISTORICAL_VARIABLES = (
    "DISPLACEMENT", "REACTION", "POSITIVE_FACE_PRESSURE",
    "NEGATIVE_FACE_PRESSURE", "VOLUME_ACCELERATION", "VELOCITY", "ACCELERATION",
)
_APP_HISTORICAL_VARIABLES = ("POINT_LOAD", "LINE_LOAD", "SURFACE_LOAD")


def _CreateProjectParameters(echo_level: int = 0) -> Kratos.Parameters:
    return Kratos.Parameters("""{
        "problem_data" : {
            "problem_name"  : "compliance",
            "parallel_type" : "OpenMP",
            "echo_level"    : %d,
            "start_time"    : 0.0,
            "end_time"      : 1.0
        },
        "solver_settings" : {
            "solver_type"              : "Static",
            "model_part_name"          : "ComplianceModelPart",
            "domain_size"              : 2,
            "echo_level"               : %d,
            "analysis_type"            : "linear",
            "model_import_settings"    : { "input_type" : "use_input_model_part" },
            "material_import_settings" : { "materials_filename" : "" },
            "time_stepping"            : { "time_step" : 1.0 },
            "rotation_dofs"            : false
        },
        "processes" : {}
    }""" % (echo_level, echo_level))


def SmoothRandomDensities(divisions: int, seed: int = 0, threshold: float = 0.5,
                          minimum_density: float = _MINIMUM_DENSITY):
    """A smooth random density field on the element grid, in [rho_min, 1].

    Smoothed rather than white, because a per-element coin flip is not a
    structure and gives a generative model nothing to learn. These are the
    vf-matched controls a sampled design is scored against.
    """
    generator = numpy.random.default_rng(seed)
    field = generator.standard_normal((divisions, divisions))
    for _ in range(3):
        field = (field
                 + numpy.roll(field, 1, 0) + numpy.roll(field, -1, 0)
                 + numpy.roll(field, 1, 1) + numpy.roll(field, -1, 1)) / 5.0
    field = (field - field.mean()) / (field.std() + 1e-12)
    densities = numpy.where(field > threshold, 1.0, minimum_density)
    return numpy.repeat(densities.reshape(-1), 2)   # two triangles per cell


def CreateComplianceModelPart(model: Kratos.Model, divisions: int = 8) -> Kratos.ModelPart:
    """The meshed plane-stress square, one Properties object per element."""
    import KratosMultiphysics.StructuralMechanicsApplication as SMA

    model_part = model.CreateModelPart("ComplianceModelPart")
    model_part.ProcessInfo[Kratos.DOMAIN_SIZE] = 2
    model_part.SetBufferSize(2)
    for name in _CORE_HISTORICAL_VARIABLES:
        model_part.AddNodalSolutionStepVariable(Kratos.KratosGlobals.GetVariable(name))
    for name in _APP_HISTORICAL_VARIABLES:
        model_part.AddNodalSolutionStepVariable(getattr(SMA, name))

    generator_geometry = Kratos.Quadrilateral2D4(
        Kratos.Node(1, 0.0, 0.0, 0.0), Kratos.Node(2, 0.0, _HEIGHT, 0.0),
        Kratos.Node(3, _LENGTH, _HEIGHT, 0.0), Kratos.Node(4, _LENGTH, 0.0, 0.0))
    mesh_parameters = Kratos.Parameters("""{
        "number_of_divisions"        : %d,
        "element_name"               : "SmallDisplacementElement2D3N",
        "condition_name"             : "LineCondition",
        "create_skin_sub_model_part" : false
    }""" % divisions)
    domain = model_part.CreateSubModelPart("Domain")
    Kratos.StructuredMeshGeneratorProcess(generator_geometry, domain, mesh_parameters).Execute()

    for element in model_part.Elements:
        properties = model_part.CreateNewProperties(1000 + element.Id)
        properties.SetValue(Kratos.YOUNG_MODULUS, _YOUNG_MODULUS)
        properties.SetValue(Kratos.POISSON_RATIO, _POISSON_RATIO)
        properties.SetValue(Kratos.CONSTITUTIVE_LAW, SMA.LinearElasticPlaneStress2DLaw())
        element.Properties = properties
    return model_part


def SimpModulus(density):
    """E = E_min + rho^p (E_0 - E_min), the standard penalization."""
    return _MINIMUM_MODULUS + (numpy.asarray(density) ** _PENALIZATION) * (
        _YOUNG_MODULUS - _MINIMUM_MODULUS)


def ApplyDensities(model_part: Kratos.ModelPart, densities) -> None:
    """Writes a density field onto the elements through SIMP."""
    densities = numpy.asarray(densities, dtype=float).reshape(-1)
    if densities.size != model_part.NumberOfElements():
        raise ValueError(
            f"Got {densities.size} densities for {model_part.NumberOfElements()} elements.")
    for element, density in zip(model_part.Elements, densities):
        element.Properties.SetValue(Kratos.YOUNG_MODULUS, float(SimpModulus(density)))
        element.SetValue(Kratos.DENSITY, float(density))


def ApplyCaseData(model_part: Kratos.ModelPart, tip_load: float = _TIP_LOAD,
                  load_row: float = 0.5, tolerance: float = 1e-8) -> None:
    """Clamps the left edge and hangs a point load on the right edge.

    `load_row` is the height of the load as a fraction of the edge, and it
    is what makes a FAMILY of cases rather than one: each position has a
    different optimum, which is what a conditional generative model needs
    something to be conditional on.
    """
    import KratosMultiphysics.StructuralMechanicsApplication as SMA

    for node in model_part.Nodes:
        if node.X0 < tolerance:
            node.Fix(Kratos.DISPLACEMENT_X)
            node.Fix(Kratos.DISPLACEMENT_Y)

    target = load_row * _HEIGHT
    loaded = min((node for node in model_part.Nodes if node.X0 > _LENGTH - tolerance),
                 key=lambda node: abs(node.Y0 - target), default=None)
    if loaded is None:
        raise ValueError("No node on the loaded edge; the mesh is not what this case expects.")
    loaded.SetSolutionStepValue(SMA.POINT_LOAD, [0.0, tip_load, 0.0])
    # the nodal POINT_LOAD value alone does nothing: it enters the system
    # through a point-load CONDITION, without which the solve returns a zero
    # displacement field and a compliance of exactly zero
    domain = model_part.GetSubModelPart("Domain")
    domain.CreateNewCondition(
        "PointLoadCondition2D1N", model_part.NumberOfConditions() + 1,
        [loaded.Id], next(iter(model_part.Elements)).Properties)
    model_part.ProcessInfo[Kratos.STEP] = 0


def CreateComplianceAnalysis(model: Kratos.Model, densities=None, divisions: int = 8,
                             tip_load: float = _TIP_LOAD, load_row: float = 0.5,
                             echo_level: int = 0):
    """A ready-to-Run() analysis of one density design."""
    from KratosMultiphysics.StructuralMechanicsApplication.structural_mechanics_analysis import (
        StructuralMechanicsAnalysis)

    model_part = CreateComplianceModelPart(model, divisions)
    if densities is None:
        densities = numpy.ones(model_part.NumberOfElements())
    ApplyDensities(model_part, densities)
    ApplyCaseData(model_part, tip_load, load_row)
    return StructuralMechanicsAnalysis(model, _CreateProjectParameters(echo_level))


def ComputeCompliance(model_part: Kratos.ModelPart, tolerance: float = 1e-8) -> float:
    """The structure's compliance, f.u over the loaded nodes. Lower is stiffer."""
    import KratosMultiphysics.StructuralMechanicsApplication as SMA

    compliance = 0.0
    for node in model_part.Nodes:
        load = node.GetSolutionStepValue(SMA.POINT_LOAD)
        if abs(load[0]) < tolerance and abs(load[1]) < tolerance:
            continue
        displacement = node.GetSolutionStepValue(Kratos.DISPLACEMENT)
        compliance += sum(load[i] * displacement[i] for i in range(3))
    return float(compliance)


def SolveCompliance(model: Kratos.Model, densities, divisions: int = 8,
                    tip_load: float = _TIP_LOAD, load_row: float = 0.5):
    """Solves one design and returns (compliance, model_part)."""
    analysis = CreateComplianceAnalysis(model, densities, divisions, tip_load, load_row)
    analysis.Run()
    model_part = model["ComplianceModelPart"]
    return ComputeCompliance(model_part), model_part


def ElementStrainEnergies(model_part: Kratos.ModelPart):
    """Per-element 0.5 u^T K u, from each element's own local system.

    The SIMP sensitivity needs u_e^T k0 u_e, the strain energy at unit
    modulus. What the element gives is its local system at its CURRENT
    modulus, so the caller divides by E(rho) - see `ComplianceSensitivity`.
    """
    info = model_part.ProcessInfo
    lhs, rhs = Kratos.Matrix(), Kratos.Vector()
    energies = numpy.empty(model_part.NumberOfElements())
    for index, element in enumerate(model_part.Elements):
        element.CalculateLocalSystem(lhs, rhs, info)
        # The element's DOFs run node-major, X then Y (verified against
        # GetDofList). DISPLACEMENT comes back as a Kratos.Array3, which
        # does NOT accept a [:2] slice - its pybind overload wants a real
        # slice object - so the two components are read by index.
        displacement = numpy.array(
            [node.GetSolutionStepValue(Kratos.DISPLACEMENT)[component]
             for node in element.GetNodes() for component in (0, 1)])
        stiffness = numpy.array(lhs)          # (6, 6) for a 3-node plane element
        energies[index] = 0.5 * float(displacement @ stiffness @ displacement)
    return energies


def ComplianceSensitivity(densities, strain_energies):
    """dc/drho = -p rho^(p-1) (E_0 - E_min) * 2 W_e / E(rho), per element."""
    densities = numpy.asarray(densities, dtype=float)
    modulus = SimpModulus(densities)
    return -(_PENALIZATION * densities ** (_PENALIZATION - 1.0)
             * (_YOUNG_MODULUS - _MINIMUM_MODULUS)
             * 2.0 * numpy.asarray(strain_energies) / modulus)


def _FilterWeights(divisions: int, radius: float):
    """Neighbourhood weights on the cell grid - the standard checkerboard cure."""
    coordinates = numpy.stack(numpy.meshgrid(
        numpy.arange(divisions), numpy.arange(divisions), indexing="ij"), axis=-1)
    flat = coordinates.reshape(-1, 2).astype(float)
    distance = numpy.linalg.norm(flat[:, None, :] - flat[None, :, :], axis=-1)
    weights = numpy.maximum(0.0, radius - distance)
    return weights / numpy.maximum(weights.sum(axis=1, keepdims=True), 1e-12)


def OptimizeSimp(divisions: int = 16, volume_fraction: float = 0.4,
                 load_row: float = 0.5, iterations: int = 30,
                 filter_radius: float = 1.5, move: float = 0.2,
                 tip_load: float = _TIP_LOAD):
    """The optimality-criteria loop, with Kratos solving every iteration.

    Returns:
        (cells, history): the optimized (divisions, divisions) cell density
        field in DensityGrid's layout, and the compliance at each iteration.
    """
    weights = _FilterWeights(divisions, filter_radius)
    cells = numpy.full(divisions * divisions, volume_fraction)
    history = []

    for _ in range(iterations):
        model = Kratos.Model()
        compliance, model_part = SolveCompliance(
            model, numpy.repeat(cells, 2), divisions, tip_load, load_row)
        history.append(compliance)

        elements = ElementStrainEnergies(model_part)
        sensitivity = ComplianceSensitivity(numpy.repeat(cells, 2), elements)
        per_cell = sensitivity.reshape(-1, 2).sum(axis=1)     # two triangles per cell
        per_cell = weights @ (per_cell * cells) / numpy.maximum(cells, 1e-3)

        # bisection on the volume multiplier: the OC update is monotone in
        # lambda, so the bracket always contains the feasible design
        low, high = 1e-9, 1e9
        target = volume_fraction * cells.size
        while (high - low) / (0.5 * (high + low)) > 1e-4:
            middle = 0.5 * (low + high)
            candidate = cells * numpy.sqrt(numpy.maximum(-per_cell, 0.0) / middle)
            candidate = numpy.clip(candidate, cells - move, cells + move)
            candidate = numpy.clip(candidate, _MINIMUM_DENSITY, 1.0)
            if candidate.sum() > target:
                low = middle
            else:
                high = middle
        cells = candidate

    return cells.reshape(divisions, divisions), history


def DensityGrid(densities, divisions: int):
    """The element densities as the (divisions, divisions) image a grid model
    consumes - the two triangles of a cell share its density.

    The FIRST index runs along x and the second along y.
    """
    densities = numpy.asarray(densities, dtype=float).reshape(-1, 2)
    return densities[:, 0].reshape(divisions, divisions)


def LoadRowFraction(divisions: int, index: int) -> float:
    """The `load_row` fraction that lands the load mask on cell row `index`.

    `ConstraintChannels` places the mask at `round(load_row * (d - 1))`, so
    this is its inverse. Both the image and the solve have to agree on
    where the load is; without this the conditioning channel a generative
    model is trained on can point somewhere the load is not, and nothing
    in either the training loop or the figure would reveal it.
    """
    return index / (divisions - 1)


def ConstraintChannels(divisions: int, volume_fraction: float, load_row: float = 0.5):
    """The conditioning a generative design model is given: where the
    structure is held, where it is loaded, and how much material it may use.

    Written in DensityGrid's layout - first index x, second y - so the
    clamped edge (x = 0, see ApplyCaseData) is a row of the first index and
    the loaded cell sits at the far x at the requested height.

    Returns:
        (3, divisions, divisions) float array - support mask, load mask and
        a constant volume-fraction plane.
    """
    supports = numpy.zeros((divisions, divisions))
    supports[0, :] = 1.0                       # the clamped edge, x = 0
    loads = numpy.zeros((divisions, divisions))
    row = int(numpy.clip(round(load_row * (divisions - 1)), 0, divisions - 1))
    loads[-1, row] = 1.0                       # the loaded cell, far x
    fraction = numpy.full((divisions, divisions), float(volume_fraction))
    return numpy.stack([supports, loads, fraction])
