import time
import sys
import pathlib
import math

import KratosMultiphysics
import KratosMultiphysics.FluidDynamicsApplication
from KratosMultiphysics.FluidDynamicsApplication.fluid_dynamics_analysis \
    import FluidDynamicsAnalysis


def abs_filepath(relative_filepath: str) -> str:
    return str(pathlib.Path(__file__).parent.resolve()) + "/" \
        + relative_filepath


class FluidDynamicsAnalysisCompressible(FluidDynamicsAnalysis):
    """
    Modified FluidDynamicsAnalysis in order to:
    - Print at the first step
    - Force stdout to flush at regular intervals
    """

    def __init__(self, model, parameters, flush_frequency=10.0):
        super().__init__(model, parameters)
        self.flush_frequency = flush_frequency
        self.last_flush = time.time()
        sys.stdout.flush()

    def Initialize(self):
        super().Initialize()
        sys.stdout.flush()
        self.OutputSolutionStep()

    def OutputSolutionStep(self):
        """This function printes / writes output files after the solution
        of a step
        """
        self.Flush()
        super().OutputSolutionStep()

    def Flush(self):
        if self.parallel_type == "OpenMP":
            now = time.time()
            if now - self.last_flush > self.flush_frequency:
                KratosMultiphysics.Logger.Flush()
                sys.stdout.flush()
                self.last_flush = now


def set_conditions(project_parameters, density: float, mach: float, AoA: float, temperature) -> None:
    """
    This function modifies a project parameters to set a desired density, mach, angle of attack
    and temperature.
    """
    gamma = 1.4
    cv = 722.14
    R = cv * (gamma - 1)

    sound_speed = math.sqrt(gamma * R * temperature)
    pressure = density * R * temperature
    velocity = sound_speed * mach

    momentum_x = velocity * density * math.cos(AoA * math.pi / 180)
    momentum_y = velocity * density * math.sin(AoA * math.pi / 180)

    total_energy = density * (0.5 * velocity * velocity + cv * temperature)

    variables = {
        "DENSITY": density,
        "MOMENTUM_X": momentum_x,
        "MOMENTUM_Y": momentum_y,
        "TOTAL_ENERGY": total_energy
    }

    blank_condition = KratosMultiphysics.Parameters("""{
        "python_module" : "assign_scalar_variable_process",
        "kratos_module" : "KratosMultiphysics",
        "process_name"  : "AssignScalarVariableProcess",
        "Parameters"    : {
            "model_part_name" : "MODEL_PART_NOT_SPECIFIED",
            "variable_name"   : "VARIABLE_NOT_SPECIFIED",
            "interval"        : [0.0, 0.0],
            "value"           : 1.0,
            "constrained"     : false
        }
    }""")

    for (variable, value) in variables.items():
        initial_condition = blank_condition.Clone()
        initial_condition["Parameters"]["model_part_name"].SetString("FluidModelPart.FluidParts_Fluid")
        initial_condition["Parameters"]["variable_name"].SetString(variable)
        initial_condition["Parameters"]["value"].SetDouble(value)
        initial_condition["Parameters"]["constrained"].SetBool(False)
        initial_condition["Parameters"]["interval"][1].SetDouble(0.0)
        project_parameters["processes"]["initial_conditions_process_list"].Append(initial_condition)

        boundary_condition = blank_condition.Clone()
        boundary_condition["Parameters"]["model_part_name"].SetString("FluidModelPart.Inlet")
        boundary_condition["Parameters"]["variable_name"].SetString(variable)
        boundary_condition["Parameters"]["value"].SetDouble(value)
        boundary_condition["Parameters"]["constrained"].SetBool(True)
        boundary_condition["Parameters"]["interval"][1].SetDouble(1e30)
        project_parameters["processes"]["boundary_conditions_process_list"].Append(boundary_condition)

    for variable in ["MOMENTUM_Y"]:
        kutta_condition = blank_condition.Clone()
        kutta_condition["Parameters"]["model_part_name"].SetString("FluidModelPart.GENERIC_Kutta")
        kutta_condition["Parameters"]["variable_name"].SetString(variable)
        kutta_condition["Parameters"]["value"].SetDouble(0.0)
        kutta_condition["Parameters"]["constrained"].SetBool(True)
        kutta_condition["Parameters"]["interval"][1].SetDouble(1e30)
        project_parameters["processes"]["boundary_conditions_process_list"].Append(kutta_condition)

    project_parameters["processes"]["auxiliar_process_list"][0]["Parameters"]["freestream_density"].SetDouble(density)
    project_parameters["processes"]["auxiliar_process_list"][0]["Parameters"]["freestream_pressure"].SetDouble(pressure)
    project_parameters["processes"]["auxiliar_process_list"][0]["Parameters"]["freestream_velocity"].SetDouble(velocity)


if __name__ == "__main__":
    with open(abs_filepath("ProjectParameters.json"), 'r') as parameter_file:
        project_parameters = KratosMultiphysics.Parameters(parameter_file.read())

    density = 1.0
    mach = 0.8
    angle = 3.0
    temperature = 293

    set_conditions(project_parameters, density, mach, angle, temperature)
    print(project_parameters)

    global_model = KratosMultiphysics.Model()
    simulation = FluidDynamicsAnalysisCompressible(global_model, project_parameters)
    simulation.Run()
