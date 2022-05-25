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
    This function modifies a project parameters to set a desired
    - density (kg/m3)
    - Mach
    - Angle of attack (degrees)
    - Temperature (K).
    """
    gamma = 1.4
    cv = 722.14
    R = cv * (gamma - 1)
    angle_of_attack = AoA * math.pi / 180  # deg -> rad

    sound_speed = math.sqrt(gamma * R * temperature)
    pressure = density * R * temperature
    velocity = sound_speed * mach

    momentum = density * velocity
    momentum_x = momentum * math.cos(angle_of_attack)
    momentum_y = momentum * math.sin(angle_of_attack)

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
        inlet_condition = blank_condition.Clone()
        inlet_condition["Parameters"]["model_part_name"].SetString("FluidModelPart.Inlet")
        inlet_condition["Parameters"]["variable_name"].SetString(variable)
        inlet_condition["Parameters"]["value"].SetDouble(value)
        inlet_condition["Parameters"]["constrained"].SetBool(True)
        inlet_condition["Parameters"]["interval"][1].SetDouble(1e30)
        project_parameters["processes"]["boundary_conditions_process_list"].Append(inlet_condition)

    for variable in ["DENSITY", "TOTAL_ENERGY"]:
        outlet_condition = blank_condition.Clone()
        outlet_condition["Parameters"]["model_part_name"].SetString("FluidModelPart.Outlet")
        outlet_condition["Parameters"]["variable_name"].SetString(variable)
        outlet_condition["Parameters"]["value"].SetDouble(variables[variable])
        outlet_condition["Parameters"]["constrained"].SetBool(True)
        outlet_condition["Parameters"]["interval"][1].SetDouble(1e30)
        project_parameters["processes"]["boundary_conditions_process_list"].Append(outlet_condition)

    for variable in ["MOMENTUM_X", "MOMENTUM_Y"]:
        kutta_condition = blank_condition.Clone()
        kutta_condition["Parameters"]["model_part_name"].SetString("FluidModelPart.GENERIC_Kutta")
        kutta_condition["Parameters"]["variable_name"].SetString(variable)
        kutta_condition["Parameters"]["value"].SetDouble(0.0)
        kutta_condition["Parameters"]["constrained"].SetBool(True)
        kutta_condition["Parameters"]["interval"][1].SetDouble(1e30)
        project_parameters["processes"]["boundary_conditions_process_list"].Append(kutta_condition)

    pressure_coeff_params = project_parameters["processes"]["auxiliar_process_list"][0]["Parameters"]
    pressure_coeff_params["freestream_density"].SetDouble(density)
    pressure_coeff_params["freestream_pressure"].SetDouble(pressure)
    pressure_coeff_params["freestream_velocity"].SetDouble(velocity)

    initial_condition_params = project_parameters["processes"]["initial_conditions_process_list"][0]["Parameters"]
    initial_condition_params["properties"]["free_stream_density"].SetDouble(density)
    initial_condition_params["properties"]["free_stream_momentum"].SetDouble(momentum)
    initial_condition_params["properties"]["free_stream_energy"].SetDouble(total_energy)

    for params in initial_condition_params["boundary_conditions_process_list"]:
        if params["process_name"].GetString() != "FarFieldProcess":
            continue
        params["Parameters"]["angle_of_attack"].SetDouble(angle_of_attack)
        params["Parameters"]["mach_infinity"].SetDouble(mach)
        params["Parameters"]["speed_of_sound"].SetDouble(sound_speed)


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
