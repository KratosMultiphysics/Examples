import KratosMultiphysics
import KratosMultiphysics.FluidDynamicsApplication
import KratosMultiphysics.ExaquteSandboxApplication
from KratosMultiphysics.FluidDynamicsApplication.fluid_dynamics_analysis import FluidDynamicsAnalysis

import sys
import time
import numpy as np
#sys.path.append('/home/kratos105b/DataDisk/src/exaqute-applications/WindGeneration/') ## in order to get access to on-the-fly wind generation


class FluidDynamicsAnalysisMC(FluidDynamicsAnalysis):

    def __init__(self,model,project_parameters):
        super(FluidDynamicsAnalysisMC,self).__init__(model,project_parameters)
        self.drag_force_vector = np.zeros([0,4]) ; self.base_moment_vector = np.zeros([0,4])
        # set model part of interest
        self.interest_model_part = "FluidModelPart.NoSlip3D_structure"
        # add required nodal variables and END_TIME in process info
        self._GetSolver().main_model_part.ProcessInfo.SetValue(KratosMultiphysics.END_TIME,self.project_parameters["problem_data"]["end_time"].GetDouble())
        self.burnin_time_coefficient = 30.0/project_parameters["problem_data"]["end_time"].GetDouble()
        print("[SCREENING] burn-in time coefficient fluid dynamics analysis = Tbt / T =",self.burnin_time_coefficient)

    def Initialize(self):
        super(FluidDynamicsAnalysisMC,self).Initialize()
        burnin_time_parameters = KratosMultiphysics.Parameters("""
        {
            "time_coefficient" : 0.2
        }""")
        burnin_time_parameters["time_coefficient"].SetDouble(self.burnin_time_coefficient)
        print("[SCREENING] burnin parameters Kratos average processes",burnin_time_parameters)
        self.weighted_pressure_process = KratosMultiphysics.ExaquteSandboxApplication.WeightedPressureCalculationProcess(self._GetSolver().main_model_part,burnin_time_parameters)
        self.weighted_velocity_process = KratosMultiphysics.ExaquteSandboxApplication.WeightedVelocityCalculationProcess(self._GetSolver().main_model_part,burnin_time_parameters)
        self.weighted_pressure_process.ExecuteInitialize()
        self.weighted_velocity_process.ExecuteInitialize()

    def FinalizeSolutionStep(self):
        super(FluidDynamicsAnalysisMC,self).FinalizeSolutionStep()
        # compute drag and base moment
        self.reference_point = KratosMultiphysics.Vector(3)
        self.reference_point[0] = self.project_parameters["processes"]["auxiliar_process_list"][0]["Parameters"]["reference_point"][0].GetDouble()
        self.reference_point[1] = self.project_parameters["processes"]["auxiliar_process_list"][0]["Parameters"]["reference_point"][1].GetDouble()
        self.reference_point[2] = self.project_parameters["processes"]["auxiliar_process_list"][0]["Parameters"]["reference_point"][2].GetDouble()
        drag_force_vector,base_moment_vector = KratosMultiphysics.FluidDynamicsApplication.DragAndMomentUtilities().CalculateBodyFittedDragAndMoment(self.model.GetModelPart(self.interest_model_part),self.reference_point)
        drag_force = [self.time,drag_force_vector[0],drag_force_vector[1],drag_force_vector[2]]
        base_moment = [self.time,base_moment_vector[0],base_moment_vector[1],base_moment_vector[2]]
        self.drag_force_vector = np.vstack((self.drag_force_vector,drag_force))
        self.base_moment_vector = np.vstack((self.base_moment_vector,base_moment))
        # store current force x and moment z for updating the time power sums
        self.current_drag_force_x = drag_force_vector[0]
        self.current_base_moment_z = base_moment_vector[2]
        # compute time average of velocity and pressure
        self.weighted_pressure_process.ExecuteFinalizeSolutionStep()
        self.weighted_velocity_process.ExecuteFinalizeSolutionStep()
        # set larger-smaller time step
        if (self.time >= self.burnin_time_coefficient*self.project_parameters["problem_data"]["end_time"].GetDouble()): # burning time
            self.project_parameters["solver_settings"]["time_stepping"]["time_step"].SetDouble(0.2375)
        else:
            self.project_parameters["solver_settings"]["time_stepping"]["time_step"].SetDouble(0.2375*2.5)

    def Finalize(self):
        super(FluidDynamicsAnalysisMC,self).Finalize()
        burnin_time = self.burnin_time_coefficient*self.model.GetModelPart(self.interest_model_part).ProcessInfo.GetValue(KratosMultiphysics.END_TIME)
        drag_force_x_post_burnin = [self.drag_force_vector[i,1] for i in range (1,len(self.drag_force_vector[:,0])) if (self.drag_force_vector[i-1,0] >= burnin_time)] # not even check time step 0
        base_moment_z_post_burnin = [self.base_moment_vector[i,3] for i in range (1,len(self.base_moment_vector[:,0])) if (self.base_moment_vector[i-1,0] >= burnin_time)] # not even check time step 0
        self.mean_drag_force_x = np.mean(drag_force_x_post_burnin)
        self.mean_base_moment_z = np.mean(base_moment_z_post_burnin)
        print("[INFO] Final averaged drag value", self.mean_drag_force_x)
        print("[INFO] Final averaged base moment value", self.mean_base_moment_z)

if __name__ == "__main__":

    if len(sys.argv) == 2: # ProjectParameters is being passed from outside
        parameter_file_name = sys.argv[1]
    else: # using default name
        parameter_file_name = "problem_settings/ProjectParametersCustom.json"

    with open(parameter_file_name,'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())

    model = KratosMultiphysics.Model()
    simulation = FluidDynamicsAnalysisMC(model,parameters)
    simulation.Run()
