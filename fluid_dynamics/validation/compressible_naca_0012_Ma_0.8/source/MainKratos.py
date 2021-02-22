from __future__ import print_function, absolute_import, division #makes KratosMultiphysics backward compatible with python 2.6 and 2.7

import KratosMultiphysics
import KratosMultiphysics.FluidDynamicsApplication as KratosFluid
import KratosMultiphysics.CompressiblePotentialFlowApplication as KratosPotential
from KratosMultiphysics.FluidDynamicsApplication.fluid_dynamics_analysis import FluidDynamicsAnalysis
from KratosMultiphysics.CompressiblePotentialFlowApplication.potential_flow_analysis import PotentialFlowAnalysis

import sys
import time

class FluidDynamicsAnalysisWithFlush(FluidDynamicsAnalysis):

    def __init__(self,model,project_parameters,flush_frequency=10.0):
        super(FluidDynamicsAnalysisWithFlush,self).__init__(model,project_parameters)
        self.flush_frequency = flush_frequency
        self.last_flush = time.time()

    def ModifyAfterSolverInitialize(self):
        super(FluidDynamicsAnalysisWithFlush,self).ModifyAfterSolverInitialize()

        # Solve a potential problem to initialize the problem
        parameters = KratosMultiphysics.Parameters('''{
            "problem_data"     : {
                "problem_name"  : "naca_0012_potential_flow",
                "parallel_type" : "OpenMP",
                "echo_level"    : 0,
                "start_time"    : 0.0,
                "end_time"      : 1
            },
            "output_processes" : {
            },
            "solver_settings"  : {
                "model_part_name"          : "FluidModelPart",
                "domain_size"              : 2,
                "solver_type"              : "potential_flow",
                "model_import_settings"    : {
                    "input_type"     : "mdpa",
                    "input_filename" : "naca_0012_geom"
                },
                "material_import_settings" : {
                    "materials_filename" : "FluidMaterials.json"
                },
                "formulation": {
                    "element_type" : "incompressible"
                },
                "maximum_iterations"       : 10,
                "echo_level"               : 0,
                "volume_model_part_name"   : "FluidParts_Fluid",
                "skin_parts"               : ["AutomaticInlet2D_Left","Outlet2D_Right","NoSlip2D_Aerofoil"],
                "no_skin_parts"            : [],
                "reform_dofs_at_each_step" : false
            },
            "processes"        : {
                "boundary_conditions_process_list" : [{
                    "python_module" : "apply_far_field_process",
                    "kratos_module" : "KratosMultiphysics.CompressiblePotentialFlowApplication",
                    "process_name"  : "FarFieldProcess",
                    "Parameters"    : {
                        "model_part_name" : "FluidModelPart.AutomaticInlet2D_Left",
                        "angle_of_attack" : 0.0,
                        "mach_infinity"   : 0.8,
                        "speed_of_sound"  : 332.0
                    }
                },{
                    "python_module" : "apply_far_field_process",
                    "kratos_module" : "KratosMultiphysics.CompressiblePotentialFlowApplication",
                    "process_name"  : "FarFieldProcess",
                    "Parameters"    : {
                        "model_part_name" : "FluidModelPart.Outlet2D_Right",
                        "angle_of_attack" : 0.0,
                        "mach_infinity"   : 0.8,
                        "speed_of_sound"  : 332.0
                    }
                },{
                    "python_module" : "define_wake_process_2d",
                    "kratos_module" : "KratosMultiphysics.CompressiblePotentialFlowApplication",
                    "process_name"  : "DefineWakeProcess2D",
                    "Parameters"    : {
                        "model_part_name" : "FluidModelPart.NoSlip2D_Aerofoil"
                    }
                }],
                "auxiliar_process_list"            : []
            }
        }''')
        aux_model = KratosMultiphysics.Model()
        pot_flow_simulation = PotentialFlowAnalysis(aux_model,parameters)
        pot_flow_simulation.Run()

        # Calculate the velocity and pressure nodal projections
        nodal_variables = ["VELOCITY","PRESSURE"]
        pot_model_part = pot_flow_simulation._GetSolver().GetComputingModelPart()
        nodal_value_process = KratosPotential.ComputeNodalValueProcess(pot_model_part, nodal_variables)
        nodal_value_process.Execute()

        # Transfer the potential flow values as initial condition for the compressible problem
        tem_0 = 273
        gamma = 1.4
        c_v = 722.14
        c = (gamma*(gamma-1.0)*c_v*tem_0)**0.5
        free_stream_rho = 1.0
        free_stream_mach = 0.8

        pot_nodes = pot_model_part.Nodes
        comp_nodes = self._GetSolver().GetComputingModelPart().Nodes
        for pot_node, comp_node in zip(pot_nodes, comp_nodes):
            pot_v = pot_node.GetValue(KratosMultiphysics.VELOCITY)
            pot_v_norm_2 = pot_v[0] * pot_v[0] + pot_v[1] * pot_v[1]
            pot_v_norm = pot_v_norm_2**0.5
            mach = pot_v_norm / c
            num = 1.0 + 0.5 * (gamma - 1.0) * free_stream_mach**2
            det = 1.0 + 0.5 * (gamma - 1.0) * mach**2
            pot_rho = free_stream_rho * (num / det)**(1.0 / (gamma - 1.0))
            aux_tot_ener = pot_rho * (c_v * tem_0 + 0.5 * pot_v_norm_2)

            # Density initial condition
            comp_node.SetSolutionStepValue(KratosMultiphysics.DENSITY, 0, pot_rho)
            comp_node.SetSolutionStepValue(KratosMultiphysics.DENSITY, 1, pot_rho)
            # Momentum initial condition
            comp_node.SetSolutionStepValue(KratosMultiphysics.VELOCITY, 0, pot_v)
            comp_node.SetSolutionStepValue(KratosMultiphysics.VELOCITY, 1, pot_v)
            comp_node.SetSolutionStepValue(KratosMultiphysics.MOMENTUM, 0, pot_rho * pot_v)
            comp_node.SetSolutionStepValue(KratosMultiphysics.MOMENTUM, 1, pot_rho * pot_v)
            # Total energy initial condition
            comp_node.SetSolutionStepValue(KratosMultiphysics.TOTAL_ENERGY, 0, aux_tot_ener)
            comp_node.SetSolutionStepValue(KratosMultiphysics.TOTAL_ENERGY, 1, aux_tot_ener)

    def ApplyBoundaryConditions(self):
        super(FluidDynamicsAnalysisWithFlush,self).ApplyBoundaryConditions()

        # Fix momentum to zero in the trailing edge node
        zero_mom = KratosMultiphysics.Vector(3)
        zero_mom[0] = 0.0
        zero_mom[1] = 0.0
        zero_mom[2] = 0.0
        trailing_edge_node = self._GetSolver().GetComputingModelPart().GetNode(5058)
        trailing_edge_node.Fix(KratosMultiphysics.MOMENTUM_X)
        trailing_edge_node.Fix(KratosMultiphysics.MOMENTUM_Y)
        trailing_edge_node.SetSolutionStepValue(KratosMultiphysics.MOMENTUM, 0, zero_mom)

    def FinalizeSolutionStep(self):
        super(FluidDynamicsAnalysisWithFlush,self).FinalizeSolutionStep()

        # Calculate and set PRESSURE and TEMPERATURE
        for node in self._GetSolver().GetComputingModelPart().Nodes:
            rho = node.GetSolutionStepValue(KratosMultiphysics.DENSITY)
            mom = node.GetSolutionStepValue(KratosMultiphysics.MOMENTUM)
            tot_ener = node.GetSolutionStepValue(KratosMultiphysics.TOTAL_ENERGY)
            vel = mom / rho
            vel_norm = (vel[0]**2 + vel[1]**2)**0.5
            temp = (tot_ener / rho - 0.5 * vel_norm**2) / 722.14
            node.SetSolutionStepValue(KratosMultiphysics.TEMPERATURE, 0, temp)
            p = (1.4 - 1.0) * rho * 722.14 * temp
            if (rho < 0.0 or p < 0.0 or temp < 0.0):
                print("Node: ", node.Id, " p: ", p, " rho: ", rho, " vel_norm: ", vel_norm, " tot_ener: ", tot_ener, " temp: ", temp)
            c = (1.4 * p / rho)**0.5
            node.SetValue(KratosFluid.MACH, vel_norm / c)
            node.SetValue(KratosMultiphysics.SOUND_VELOCITY, c)
            node.SetSolutionStepValue(KratosMultiphysics.PRESSURE, 0, p)
            node.SetSolutionStepValue(KratosMultiphysics.VELOCITY, 0, vel)

        if self.parallel_type == "OpenMP":
            now = time.time()
            if now - self.last_flush > self.flush_frequency:
                sys.stdout.flush()
                self.last_flush = now

if __name__ == "__main__":

    with open("ProjectParameters.json",'r') as parameter_file:
    #with open("ProjectParametersRestart.json",'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())

    model = KratosMultiphysics.Model()
    simulation = FluidDynamicsAnalysisWithFlush(model,parameters)
    simulation.Run()
