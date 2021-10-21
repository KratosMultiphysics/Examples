# Import Python libraries
import sys
import time
import numpy as np

# Import Kratos
import KratosMultiphysics
import KratosMultiphysics.FluidDynamicsApplication
import KratosMultiphysics.ExaquteSandboxApplication
from KratosMultiphysics.FluidDynamicsApplication.fluid_dynamics_analysis import FluidDynamicsAnalysis

# coarse mesh:
# minimal size: 0.0759m

# finer mesh
# minimal size: 0.1928m

class FluidDynamicsAnalysisMC(FluidDynamicsAnalysis):

    def __init__(self,model,project_parameters):
        super().__init__(model,project_parameters)
        self.drag_force_vector = np.zeros([0,4]) ; self.base_moment_vector = np.zeros([0,4])
        # set model part of interest
        self.interest_model_part = "FluidModelPart.Drag_Structure"
        self.default_time_step = self.project_parameters["solver_settings"]["time_stepping"]["time_step"].GetDouble()

    def ModifyInitialProperties(self):
        """
        function changing process settings
        input:  self: an instance of the class
        """
        super().ModifyInitialProperties()
        for aux_process in self.project_parameters["processes"]["auxiliar_process_list"]:
            if aux_process["python_module"].GetString() == "temporal_statistics_process":
                aux_process["Parameters"]["statistics_start_point_control_value"].SetDouble(self.project_parameters["problem_data"]["burnin_time"].GetDouble())


    def FinalizeSolutionStep(self):
        super().FinalizeSolutionStep()
        # calculate NODAL_H
        find_nodal_h = KratosMultiphysics.FindNodalHNonHistoricalProcess(self.model.GetModelPart("FluidModelPart"))
        find_nodal_h.Execute()
        # Get number of OMP threads
        KratosMultiphysics.Logger.PrintInfo(self._GetSimulationName(),"[SCREENING] Running task with OMP_NUM_THREADS =",KratosMultiphysics.ParallelUtilities.GetNumThreads())
        # compute drag and base moment
        self.reference_point = KratosMultiphysics.Vector(3)
        self.reference_point[0] = self.project_parameters["processes"]["auxiliar_process_list"][0]["Parameters"]["reference_point"][0].GetDouble()
        self.reference_point[1] = self.project_parameters["processes"]["auxiliar_process_list"][0]["Parameters"]["reference_point"][1].GetDouble()
        self.reference_point[2] = self.project_parameters["processes"]["auxiliar_process_list"][0]["Parameters"]["reference_point"][2].GetDouble()
        drag_force_vector,base_moment_vector = KratosMultiphysics.ExaquteSandboxApplication.DragAndMomentUtilities().CalculateBodyFittedDragAndMoment(self.model.GetModelPart(self.interest_model_part),self.reference_point)
        KratosMultiphysics.Logger.PrintInfo(drag_force_vector,base_moment_vector)
        drag_force = [self.time,drag_force_vector[0],drag_force_vector[1],drag_force_vector[2]]
        base_moment = [self.time,base_moment_vector[0],base_moment_vector[1],base_moment_vector[2]]
        self.drag_force_vector = np.vstack((self.drag_force_vector,drag_force))
        self.base_moment_vector = np.vstack((self.base_moment_vector,base_moment))
        # store current force x and moment z for updating the time power sums
        self.current_drag_force_x = drag_force_vector[0]
        self.current_base_moment_z = base_moment_vector[2]
        # set larger-smaller time step
        if (self.time >= self.project_parameters["problem_data"]["burnin_time"].GetDouble()): # burning time
            self.project_parameters["solver_settings"]["time_stepping"]["time_step"].SetDouble(self.default_time_step)
        else:
            self.project_parameters["solver_settings"]["time_stepping"]["time_step"].SetDouble(self.default_time_step)
            # self.project_parameters["solver_settings"]["time_stepping"]["time_step"].SetDouble(2.5*self.default_time_step)

    def Finalize(self):
        super().Finalize()
        burnin_time = self.project_parameters["problem_data"]["burnin_time"].GetDouble()
        drag_force_x_post_burnin = [self.drag_force_vector[i,1] for i in range (1,len(self.drag_force_vector[:,0])) if (self.drag_force_vector[i-1,0] >= burnin_time)] # not even check time step 0
        base_moment_z_post_burnin = [self.base_moment_vector[i,3] for i in range (1,len(self.base_moment_vector[:,0])) if (self.base_moment_vector[i-1,0] >= burnin_time)] # not even check time step 0
        self.mean_drag_force_x = np.mean(drag_force_x_post_burnin)
        self.mean_base_moment_z = np.mean(base_moment_z_post_burnin)
        KratosMultiphysics.Logger.PrintInfo("[INFO] Final averaged drag value", self.mean_drag_force_x)
        KratosMultiphysics.Logger.PrintInfo("[INFO] Final averaged base moment value", self.mean_base_moment_z)

if __name__ == "__main__":

    if len(sys.argv) == 2: # ProjectParameters is being passed from outside
        parameter_file_name = sys.argv[1]
    else: # using default name
        parameter_file_name = "problem_settings/ProjectParameters_FractionalStep_finer.json"

    with open(parameter_file_name,'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())

    model = KratosMultiphysics.Model()
    simulation = FluidDynamicsAnalysisMC(model,parameters)
    simulation.Run()
