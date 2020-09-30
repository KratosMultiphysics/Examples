# Importing the Kratos Library
import KratosMultiphysics

# Import applications
import KratosMultiphysics.FluidDynamicsApplication
import KratosMultiphysics.ExaquteSandboxApplication
from KratosMultiphysics.FluidDynamicsApplication.fluid_dynamics_analysis import FluidDynamicsAnalysis
import KratosMultiphysics.kratos_utilities as kratos_utilities

# Import packages
import numpy as np
import time


class FluidDynamicsAnalysisProblemZero(FluidDynamicsAnalysis):

    def __init__(self,model,project_parameters):
        super(FluidDynamicsAnalysisProblemZero,self).__init__(model,project_parameters)
        self.drag_force_vector = np.zeros([0,7])
        # set model part of interest
        self.interest_model_part = "MainModelPart.NoSlip2D_No_Slip_Auto1"
        # add required nodal variables and END_TIME in process info
        self._GetSolver().main_model_part.ProcessInfo.SetValue(KratosMultiphysics.END_TIME,self.project_parameters["problem_data"]["end_time"].GetDouble())
        self.washout_time_coefficient = 140/project_parameters["problem_data"]["end_time"].GetDouble()
        print("[SCREENING] washout coefficient fluid dynamics analysis",self.washout_time_coefficient)

    def Initialize(self):
        super(FluidDynamicsAnalysisProblemZero,self).Initialize()
        washout_time_parameters = KratosMultiphysics.Parameters("""
        {
            "time_coefficient" : 0.2
        }""")
        washout_time_parameters["time_coefficient"].SetDouble(self.washout_time_coefficient)
        print("[SCREENING] washout parameters Kratos average processes",washout_time_parameters)
        self.weighted_pressure_process = KratosMultiphysics.ExaquteSandboxApplication.WeightedPressureCalculationProcess(self.model.GetModelPart(self.interest_model_part),washout_time_parameters)
        self.weighted_velocity_process = KratosMultiphysics.ExaquteSandboxApplication.WeightedVelocityCalculationProcess(self._GetSolver().main_model_part,washout_time_parameters)
        self.weighted_pressure_process.ExecuteInitialize()
        self.weighted_velocity_process.ExecuteInitialize()

    def FinalizeSolutionStep(self):
        super(FluidDynamicsAnalysisProblemZero,self).FinalizeSolutionStep()
        # compute drag and base moment
        self.reference_point = KratosMultiphysics.Vector(3)
        self.reference_point[0] = self.project_parameters["processes"]["auxiliar_process_list"][0]["Parameters"]["reference_point"][0].GetDouble()
        self.reference_point[1] = self.project_parameters["processes"]["auxiliar_process_list"][0]["Parameters"]["reference_point"][1].GetDouble()
        self.reference_point[2] = self.project_parameters["processes"]["auxiliar_process_list"][0]["Parameters"]["reference_point"][2].GetDouble()
        drag_force_vector = KratosMultiphysics.FluidDynamicsApplication.DragAndMomentUtilities().CalculateBodyFittedDragAndMoment(self.model.GetModelPart(self.interest_model_part),self.reference_point)
        drag_force = [self.time,drag_force_vector[0][0],drag_force_vector[0][1],drag_force_vector[0][2],drag_force_vector[1][0],drag_force_vector[1][1],drag_force_vector[1][2]]
        self.drag_force_vector = np.vstack((self.drag_force_vector,drag_force))
        # store current force x and moment z for updating the time power sums
        self.current_force_x = drag_force_vector[0][0]
        self.current_moment_z = drag_force_vector[1][2]
        pressure = []
        for node in self.model.GetModelPart(self.interest_model_part).Nodes:
            pressure.append(node.GetSolutionStepValue(KratosMultiphysics.PRESSURE))
        # compute time average of velocity and pressure
        self.weighted_pressure_process.ExecuteFinalizeSolutionStep()
        self.weighted_velocity_process.ExecuteFinalizeSolutionStep()

    def Finalize(self):
        super(FluidDynamicsAnalysisProblemZero,self).Finalize()
        washout_time = self.washout_time_coefficient*self.model.GetModelPart(self.interest_model_part).ProcessInfo.GetValue(KratosMultiphysics.END_TIME)
        force_x_no_washout = [self.drag_force_vector[i,1] for i in range (1,len(self.drag_force_vector[:,0])) if (self.drag_force_vector[i-1,0] >= washout_time)] # not even check time step 0
        moment_z_no_washout = [self.drag_force_vector[i,6] for i in range (1,len(self.drag_force_vector[:,0])) if (self.drag_force_vector[i-1,0] >= washout_time)] # not even check time step 0
        self.mean_force_x = np.mean(force_x_no_washout)
        self.mean_moment_z = np.mean(moment_z_no_washout)
        print("[INFO] Final averaged drag value", self.mean_force_x)
        print("[INFO] Final averaged base moment value", self.mean_moment_z)
        ####################################################################################################
        # with open('average_velocity_field_RectangularCylinder_'+str(self.model.GetModelPart(self.interest_model_part).ProcessInfo.GetValue(KratosMultiphysics.END_TIME))+'.dat','w') as dat_file:
        #    for node in self._GetSolver().main_model_part.Nodes:
        #       velocity = node.GetValue(KratosMultiphysics.ExaquteSandboxApplication.VELOCITY_WEIGHTED)
        #         dat_file.write('%f %f %f\n' % (velocity[0],velocity[1],velocity[2]))
        ####################################################################################################

if __name__ == "__main__":
    from sys import argv

    if len(argv) > 2:
        err_msg =  'Too many input arguments!\n'
        err_msg += 'Use this script in the following way:\n'
        err_msg += '- With default parameter file (assumed to be called "ProjectParameters.json"):\n'
        err_msg += '    "python fluid_dynamics_analysis.py"\n'
        err_msg += '- With custom parameter file:\n'
        err_msg += '    "python fluid_dynamics_analysis.py <my-parameter-file>.json"\n'
        raise Exception(err_msg)

    if len(argv) == 2: # ProjectParameters is being passed from outside
        parameter_file_name = argv[1]
    else: # using default name
        parameter_file_name = "problem_settings/ProblemZeroParametersVMS.json"

    with open(parameter_file_name,'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())
    model = KratosMultiphysics.Model()

    ini_time = time.time()
    simulation = FluidDynamicsAnalysisProblemZero(model, parameters)
    simulation.Run()
    print("[TIMER] Total analysis time:", time.time()-ini_time)