from __future__ import absolute_import, division  # makes KratosMultiphysics backward compatible with python 2.6 and 2.7

# Importing the Kratos Library
import KratosMultiphysics

# Check that applications were imported in the main script
KratosMultiphysics.CheckRegisteredApplications("FluidDynamicsApplication")

# Import applications
import KratosMultiphysics.FluidDynamicsApplication as KratosCFD

# Import base class file
from fluid_solver import FluidSolver
from navier_stokes_solver_vmsmonolithic import NavierStokesSolverMonolithic, StabilizedFormulation

class FluidSolverNoReplace(NavierStokesSolverMonolithic):

    def _ValidateSettings(self, settings):
#            "formulation": {
#                "formulation": "vms",
#                "dynamic_tau": 1.0
#            },

        ##settings string in json format
        default_settings = KratosMultiphysics.Parameters("""
        {
            "solver_type": "navier_stokes_solver_vmsmonolithic",
            "model_part_name": "FluidModelPart",
            "domain_size": 2,
            "model_import_settings": {
                "input_type": "mdpa",
                "input_filename": "unknown_name"
            },
            "formulation": {
                "element_type": "vms",
                "dynamic_tau": 0.0
            },
            "maximum_iterations": 10,
            "echo_level": 0,
            "consider_periodic_conditions": false,
            "compute_reactions": false,
            "reform_dofs_at_each_step": false,
            "relative_velocity_tolerance": 1e-3,
            "absolute_velocity_tolerance": 1e-5,
            "relative_pressure_tolerance": 1e-3,
            "absolute_pressure_tolerance": 1e-5,
            "linear_solver_settings"        : {
                "solver_type" : "AMGCL",
                "krylov_type" : "gmres",
                "tolerance"   : 1e-8,
                "max_iteration" : 200,
                "verbosity" : 1
            },
            "volume_model_part_name" : "volume_model_part",
            "skin_parts": [""],
            "no_skin_parts":[""],
            "time_stepping"                : {
                "automatic_time_step" : false,
                "CFL_number"          : 1,
                "minimum_delta_time"  : 1e-4,
                "maximum_delta_time"  : 0.01,
                "time_step"           : 0.0
            },
            "time_scheme":"bossak",
            "alpha":-0.3,
            "velocity_relaxation":0.9,
            "pressure_relaxation":0.9,
            "move_mesh_strategy": 0,
            "periodic": "periodic",
            "move_mesh_flag": false,
            "turbulence_model": "None",
            "reorder": false
        }""")

        ## Backwards compatibility -- deprecation warnings
        if settings.Has("oss_switch"):
            msg  = "Input JSON data contains deprecated setting \'oss_switch\' (int).\n"
            msg += "Please define \'formulation/formulation\' (set it to \'vms\')\n"
            msg += "and set \'formulation/use_orthogonal_subscales\' (bool) instead."
            KratosMultiphysics.Logger.PrintWarning("NavierStokesVMSMonolithicSolver",msg)
            if not settings.Has("formulation"):
                settings.AddValue("formulation",KratosMultiphysics.Parameters(r'{"formulation":"vms"}'))
            settings["formulation"].AddEmptyValue("use_orthogonal_subscales")
            settings["formulation"]["use_orthogonal_subscales"].SetBool(bool(settings["oss_switch"].GetInt()))
            settings.RemoveValue("oss_switch")
        if settings.Has("dynamic_tau"):
            msg  = "Input JSON data contains deprecated setting \'dynamic_tau\' (float).\n"
            msg += "Please define \'formulation/formulation\' (set it to \'vms\') and \n"
            msg += "set \'formulation/dynamic_tau\' (float) instead."
            KratosMultiphysics.Logger.PrintWarning("NavierStokesVMSMonolithicSolver",msg)
            if not settings.Has("formulation"):
                settings.AddValue("formulation",KratosMultiphysics.Parameters(r'{"formulation":"vms"}'))
            settings["formulation"].AddEmptyValue("dynamic_tau")
            settings["formulation"]["dynamic_tau"].SetDouble(settings["dynamic_tau"].GetDouble())
            settings.RemoveValue("dynamic_tau")

        settings.ValidateAndAssignDefaults(default_settings)
        return settings


    def __init__(self, model, custom_settings):
        super(NavierStokesSolverMonolithic,self).__init__(model,custom_settings)

        # There is only a single rank in OpenMP, we always print
        self._is_printing_rank = True

        self.formulation = StabilizedFormulation(self.settings["formulation"])
        self.element_name = self.formulation.element_name
        self.condition_name = self.formulation.condition_name

        scheme_type = self.settings["time_scheme"].GetString()
        if scheme_type == "bossak":
            self.min_buffer_size = 2
        elif scheme_type == "bdf2":
            self.min_buffer_size = 3
        elif scheme_type == "steady":
            self.min_buffer_size = 1
            self._SetUpSteadySimulation()
        else:
            msg  = "Unknown time_scheme option found in project parameters:\n"
            msg += "\"" + scheme_type + "\"\n"
            msg += "Accepted values are \"bossak\", \"bdf2\" or \"steady\".\n"
            raise Exception(msg)

        ## Construct the linear solver
        import linear_solver_factory
        self.linear_solver = linear_solver_factory.ConstructSolver(self.settings["linear_solver_settings"])

        KratosMultiphysics.Logger.PrintInfo("NavierStokesSolverMonolithic", "Construction of NavierStokesSolverMonolithic finished.")

    def PrepareModelPart(self):
        if not self.main_model_part.ProcessInfo[KratosMultiphysics.IS_RESTARTED]:
            ## Set buffer size
            self.main_model_part.SetBufferSize(self.min_buffer_size)
            self._set_physical_properties()

        if not self.model.HasModelPart(self.settings["model_part_name"].GetString()):
            self.model.AddModelPart(self.main_model_part)

        if self._IsPrintingRank():
            KratosMultiphysics.Logger.PrintInfo("FluidSolverNoReplace", "Model reading finished.")

    def GetComputingModelPart(self):
        return self.main_model_part

    def SolveSolutionStep(self):
        super(FluidSolverNoReplace,self).SolveSolutionStep()


