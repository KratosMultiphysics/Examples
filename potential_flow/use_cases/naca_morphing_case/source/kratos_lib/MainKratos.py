"""Minimal Kratos 'library' for NACA 4-digit airfoil potential flow analysis.

The mesh is imported once and shared by every case, so a series of airfoils
costs one mesh read plus one analysis per airfoil. The helper functions run a series
of airfoils and return the lift coefficient reported by the solver, the solve time
and, on request, the surface pressure coefficient distribution of each of them.
"""

import os
import time
from dataclasses import dataclass
from importlib import import_module

import KratosMultiphysics
import KratosMultiphysics.CompressiblePotentialFlowApplication as CPFApp
import numpy as np

# Silence solver output by default
KratosMultiphysics.Logger.GetDefaultOutput().SetSeverity(KratosMultiphysics.Logger.Severity.WARNING)


# ─── NACA 4-digit geometry ────────────────────────────────────────────────
@dataclass(frozen=True)
class Naca4Digit:
    """NACA 4-digit airfoil defined by max camber, camber position, thickness."""
    max_camber: float
    camber_position: float
    thickness: float

    @property
    def name(self) -> str:
        return (
            f"{int(round(self.max_camber * 100))}"
            f"{int(round(self.camber_position * 10))}"
            f"{int(round(self.thickness * 100)):02d}"
        )

    def mean_camber(self, chord_position: float):
        x = float(np.clip(chord_position, 0.0, 1.0))
        if self.max_camber == 0.0:
            return 0.0, 0.0
        p = self.camber_position
        if x <= p:
            camber = (self.max_camber / p ** 2) * (2.0 * p * x - x ** 2)
            slope = (2.0 * self.max_camber / p ** 2) * (p - x)
        else:
            camber = (self.max_camber / (1.0 - p) ** 2) * ((1.0 - 2.0 * p) + 2.0 * p * x - x ** 2)
            slope = (2.0 * self.max_camber / (1.0 - p) ** 2) * (p - x)
        return camber, slope

    def half_thickness(self, chord_position: float) -> float:
        x = float(np.clip(chord_position, 0.0, 1.0))
        sqrt_term, linear, quadratic, cubic, quartic = (0.2969, -0.1260, -0.3516, 0.2843, -0.1036)
        return 5.0 * self.thickness * (
            sqrt_term * np.sqrt(x)
            + linear * x
            + quadratic * x ** 2
            + cubic * x ** 3
            + quartic * x ** 4
        )

    def surface_point(self, chord_position: float, upper_surface: bool = True):
        camber, slope = self.mean_camber(chord_position)
        half_thickness = self.half_thickness(chord_position)
        inclination = np.arctan(slope)
        sign = 1.0 if upper_surface else -1.0
        x = chord_position - sign * half_thickness * np.sin(inclination)
        y = camber + sign * half_thickness * np.cos(inclination)
        return x, y


# ─── Deformer: resets mesh and imposes airfoil shape ─────────────────────
class NacaMeshDeformer:
    """Impose a NACA 4-digit shape on the airfoil surface of an already imported mesh."""

    def __init__(self, airfoil: Naca4Digit, fluid_model_part_name: str = "FluidModelPart"):
        self.airfoil = airfoil
        self.fluid_model_part_name = fluid_model_part_name
        self.upper_surface_name = f"{fluid_model_part_name}.UpperSurface"
        self.lower_surface_name = f"{fluid_model_part_name}.LowerSurface"
        self.leading_edge_node_name = f"{fluid_model_part_name}.LeadingEdgeNode"
        self.trailing_edge_node_name = f"{fluid_model_part_name}.TrailingEdgeNode"

    def Apply(self, model):
        fluid_model_part = model[self.fluid_model_part_name]
        leading_edge_node, trailing_edge_node = self._GetEdgeNodes(model)
        self._RestoreReferenceMesh(fluid_model_part)
        fixed_node_ids = self._FixEdgeNodes(leading_edge_node, trailing_edge_node)

        chord = trailing_edge_node.X0 - leading_edge_node.X0
        for surface_name, upper_surface in (
            (self.upper_surface_name, True),
            (self.lower_surface_name, False),
        ):
            for node in model[surface_name].Nodes:
                if node.Id in fixed_node_ids:
                    continue
                chord_position = (node.X0 - leading_edge_node.X0) / chord
                target_x, target_y = self.airfoil.surface_point(chord_position, upper_surface)
                node.SetSolutionStepValue(
                    KratosMultiphysics.MESH_DISPLACEMENT_X, target_x - node.X0
                )
                node.SetSolutionStepValue(
                    KratosMultiphysics.MESH_DISPLACEMENT_Y, target_y - node.Y0
                )
                node.Fix(KratosMultiphysics.MESH_DISPLACEMENT_X)
                node.Fix(KratosMultiphysics.MESH_DISPLACEMENT_Y)

    def _GetEdgeNodes(self, model):
        leading_edge_nodes = list(model[self.leading_edge_node_name].Nodes)
        trailing_edge_nodes = list(model[self.trailing_edge_node_name].Nodes)
        if len(leading_edge_nodes) != 1 or len(trailing_edge_nodes) != 1:
            raise ValueError("Expected a single leading/trailing edge node")
        return leading_edge_nodes[0], trailing_edge_nodes[0]

    def _RestoreReferenceMesh(self, fluid_model_part):
        variable_utils = KratosMultiphysics.VariableUtils()
        variable_utils.SetHistoricalVariableToZero(
            KratosMultiphysics.MESH_DISPLACEMENT, fluid_model_part.Nodes
        )
        variable_utils.UpdateCurrentToInitialConfiguration(fluid_model_part.Nodes)

    def _FixEdgeNodes(self, leading_edge_node, trailing_edge_node):
        fixed_node_ids = set()
        for node in (leading_edge_node, trailing_edge_node):
            node.Fix(KratosMultiphysics.MESH_DISPLACEMENT_X)
            node.Fix(KratosMultiphysics.MESH_DISPLACEMENT_Y)
            fixed_node_ids.add(node.Id)
        return fixed_node_ids


# ─── Surface pressure coefficient extraction ─────────────────────────────
@dataclass(frozen=True)
class SurfacePressure:
    """Pressure coefficient distribution read on the surface of the profile."""

    x: np.ndarray
    y: np.ndarray
    cp: np.ndarray
    is_upper: np.ndarray
    is_lower: np.ndarray

    def _surface(self, mask):
        indices = np.flatnonzero(mask)
        order = np.argsort(self.x[indices])
        indices = indices[order]
        return self.x[indices], self.cp[indices]

    def upper_and_lower(self):
        """Pressure distributions of the upper and the lower surface, ordered by x."""

        upper_x, upper_cp = self._surface(self.is_upper)
        lower_x, lower_cp = self._surface(self.is_lower)
        return upper_x, upper_cp, lower_x, lower_cp

    def ordered_contour(self):
        """Nodes of the profile ordered as a closed contour."""

        upper_indices = np.flatnonzero(self.is_upper)
        lower_indices = np.flatnonzero(self.is_lower)
        ordered = np.concatenate((
            upper_indices[np.argsort(self.x[upper_indices])],
            lower_indices[np.argsort(self.x[lower_indices])[::-1]],
        ))
        return self.x[ordered], self.y[ordered]


def ExtractSurfacePressure(model, fluid_model_part_name: str = "FluidModelPart") -> SurfacePressure:
    """Read the pressure coefficient of the deformed profile out of the solved model."""

    body_model_part = model[f"{fluid_model_part_name}.Body"]

    x = [node.X for node in body_model_part.Nodes]
    y = [node.Y for node in body_model_part.Nodes]
    cp = [node.GetValue(KratosMultiphysics.PRESSURE_COEFFICIENT) for node in body_model_part.Nodes]

    upper_node_ids = {node.Id for node in model[f"{fluid_model_part_name}.UpperSurface"].Nodes}
    lower_node_ids = {node.Id for node in model[f"{fluid_model_part_name}.LowerSurface"].Nodes}
    is_upper = np.array([node.Id in upper_node_ids for node in body_model_part.Nodes])
    is_lower = np.array([node.Id in lower_node_ids for node in body_model_part.Nodes])

    return SurfacePressure(x=np.array(x),
                           y=np.array(y),
                           cp=np.array(cp),
                           is_upper=is_upper,
                           is_lower=is_lower)


# ─── Helper functions ────────────────────────────────────────────────────
@dataclass(frozen=True)
class CaseResult:
    airfoil: Naca4Digit
    lift_coefficient: float
    solve_time: float
    surface_pressure: SurfacePressure = None


def AsAirfoil(profile) -> Naca4Digit:
    if isinstance(profile, Naca4Digit):
        return profile
    return Naca4Digit(*profile)


def CreateAnalysisStage(model, parameters, airfoil: Naca4Digit):
    module_name = parameters["analysis_stage"].GetString()
    last_module_part = module_name.split('.')[-1]
    class_name = ''.join(x.title() for x in last_module_part.split('_'))
    analysis_stage_module = import_module(module_name)
    base_analysis_stage_class = getattr(analysis_stage_module, class_name)

    deformer = NacaMeshDeformer(airfoil)

    class AnalysisStageWithDeformer(base_analysis_stage_class):
        def __init__(self, model, project_parameters, flush_frequency=10.0):
            super().__init__(model, project_parameters)
            self.deformer = deformer
            self.flush_frequency = flush_frequency
            self.last_flush = time.time()
            self.solve_time = 0.0

        def ModifyInitialGeometry(self):
            super().ModifyInitialGeometry()
            self.deformer.Apply(self.model)

        def SolveSolutionStep(self):
            start_time = time.perf_counter()
            solution = super().SolveSolutionStep()
            self.solve_time += time.perf_counter() - start_time
            return solution

        @property
        def lift_coefficient(self) -> float:
            return self.model["FluidModelPart.Body"].ProcessInfo[CPFApp.LIFT_COEFFICIENT]

    return AnalysisStageWithDeformer(model, parameters)


def EvaluateAirfoils(airfoils, mesh_name: str, mach_number: float, angle_of_attack: float,
                     gid_output: bool = False, vtk_output: bool = False,
                     pressure_coefficient: bool = False) -> list:
    """Evaluate a series of airfoils over the given mesh, one analysis per airfoil."""

    with open(os.path.join(os.path.dirname(__file__),"ProjectParameters.json"), "r") as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())

    model = KratosMultiphysics.Model()
    results = []
    airfoils_list = list(airfoils)

    for index, airfoil_tuple in enumerate(airfoils_list, start=1):
        airfoil = AsAirfoil(airfoil_tuple)

        # Clone parameters for this case
        case_parameters = parameters.Clone()

        # Set mesh path for first run (when modelers are still present)
        if case_parameters.Has("modelers"):
            mesh_path = os.path.join(os.path.dirname(__file__), mesh_name)
            case_parameters["modelers"][0]["parameters"]["input_filename"].SetString(mesh_path)

        # Set free-stream conditions 
        far_field_params = case_parameters["processes"]["boundary_conditions_process_list"][0]["Parameters"]
        far_field_params["mach_infinity"].SetDouble(float(mach_number))
        far_field_params["angle_of_attack"].SetDouble(float(angle_of_attack))

        # Update output paths with airfoil name if outputs are enabled
        if gid_output and case_parameters["output_processes"].Has("gid_output"):
            gid_params = case_parameters["output_processes"]["gid_output"][0]["Parameters"]
            gid_params["output_name"].SetString(f"gid_output/{airfoil.name}_{mesh_name}")

        if vtk_output and case_parameters["output_processes"].Has("vtk_output"):
            vtk_params = case_parameters["output_processes"]["vtk_output"][0]["Parameters"]
            vtk_params["output_path"].SetString(f"vtk_output/{airfoil.name}_{mesh_name}")

        # Remove output processes unless explicitly enabled
        if not gid_output:
            case_parameters["output_processes"].RemoveValue("gid_output")
        if not vtk_output:
            case_parameters["output_processes"].RemoveValue("vtk_output")

        # For the first airfoil, keep modelers to import mesh; for subsequent, remove them
        if index > 1 and case_parameters.Has("modelers"):
            case_parameters.RemoveValue("modelers")

        analysis_stage = CreateAnalysisStage(model, case_parameters, airfoil)
        analysis_stage.Run()

        surface_pressure = ExtractSurfacePressure(model) if pressure_coefficient else None

        results.append(CaseResult(
            airfoil=airfoil,
            lift_coefficient=analysis_stage.lift_coefficient,
            solve_time=analysis_stage.solve_time,
            surface_pressure=surface_pressure
        ))

    return results