from __future__ import absolute_import, division #makes KratosMultiphysics backward compatible with python 2.6 and 2.7

# Importing the Kratos Library
import KratosMultiphysics

# Import applications
import KratosMultiphysics.FluidDynamicsApplication
import KratosMultiphysics.ExaquteSandboxApplication
from FluidDynamicsAnalysisProblemZero import FluidDynamicsAnalysisProblemZero

# Import packages
import numpy as np
import time
import sys
import os

class FluidDynamicsAnalysisProblemZero_TimeScreening(FluidDynamicsAnalysisProblemZero):

    def __init__(self,model,project_parameters):
        self.initial_time = time.time()
        super(FluidDynamicsAnalysisProblemZero_TimeScreening,self).__init__(model,project_parameters)

    def RunSolutionLoop(self):
        """This function executes the solution loop of the AnalysisStage
        It can be overridden by derived classes
        """
        while self.KeepAdvancingSolutionLoop():
            self.time = self._GetSolver().AdvanceInTime(self.time)
            ini_time = time.time()
            self.InitializeSolutionStep()
            self.initialize_step_time += time.time() - ini_time
            self._GetSolver().Predict()
            ini_time = time.time()
            is_converged = self._GetSolver().SolveSolutionStep()
            self.solve_time += time.time() - ini_time
            ini_time = time.time()
            self.FinalizeSolutionStep()
            self.finalize_step_time += time.time() - ini_time
            ini_time = time.time()
            self.OutputSolutionStep()
            self.output_time += time.time() - ini_time
            print("[TIMER] Current TOTAL time:", time.time() - self.initial_time)
            print("[TIMER] Current TOTAL time:", time.time() - self.initial_time)
            print("[TIMER] time step time:",time.time()-ini_time,"of time step:",self.time)
            sys.stdout.flush()

    def Initialize(self):
        self.initialize_time=0.0
        self.initialize_step_time=0.0
        self.solve_time = 0.0
        self.finalize_step_time = 0.0
        self.output_time = 0.0
        self.cpp_average_time = 0.0
        ini_time = time.time()
        super(FluidDynamicsAnalysisProblemZero_TimeScreening,self).Initialize()
        print("[INFO] Number of nodes:", self._GetSolver().main_model_part.NumberOfNodes())
        self.initialize_time=time.time()-ini_time



    def Finalize(self):
        ini_time = time.time()
        super(FluidDynamicsAnalysisProblemZero_TimeScreening,self).Finalize()
        # screening
        print("[TIMER] Time spent Initialize:", self.initialize_time)
        print("[TIMER] Time spent InitializeSolutionStep:", self.initialize_step_time)
        print("[TIMER] Time spent SolveSolutionStep:", self.solve_time)
        print("[TIMER] Time spent FinalizeSolutionStep:", self.finalize_step_time)
        # print("[TIMER] Time spent cpp_average_time:", self.cpp_average_time)
        # print("[TIMER] Time spent computing drag:", self.drag_time +finalize_drag_time)
        print("[TIMER] Time spent OutputSolutionStep:", self.output_time)
        print("[TIMER] Time spent Finalize:", time.time() - ini_time)


if __name__ == "__main__":
    from sys import argv
    from sys import stdout
    if len(argv) == 2: # ProjectParameters is being passed from outside
        parameter_file_name = argv[1]
    elif len(argv) == 5:
        parameter_file_name = argv[1]
        mdpa_file_name = argv[2]
        end_time = argv[3]
        time_step = argv[4]
    elif len(argv) == 6:
        parameter_file_name = argv[1]
        mdpa_file_name = argv[2]
        end_time = argv[3]
        time_step = argv[4]
        output_name = argv[5]
    elif len(argv) == 7:
        parameter_file_name = argv[1]
        mdpa_file_name = argv[2]
        end_time = argv[3]
        time_step = argv[4]
        output_name = argv[5] 
        dyn_visc = argv[6] 
    else: # using default name
        parameter_file_name = "problem_settings/ProblemZeroParametersVMS.json"

    with open(parameter_file_name,'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())
    model = KratosMultiphysics.Model()

    if len(argv) == 5:
        parameters["solver_settings"]["model_import_settings"]["input_filename"].SetString(mdpa_file_name)
        parameters["problem_data"]["end_time"].SetDouble(float(end_time))
        parameters["solver_settings"]["time_stepping"]["time_step"].SetDouble(float(time_step))
    if len(argv) == 6:
        parameters["solver_settings"]["model_import_settings"]["input_filename"].SetString(mdpa_file_name)
        parameters["problem_data"]["end_time"].SetDouble(float(end_time))
        parameters["solver_settings"]["time_stepping"]["time_step"].SetDouble(float(time_step))
        if not os.path.exists('./drag/'):
            os.makedirs('./drag/')
        if not os.path.exists('./gid_output/'):
            os.makedirs('./gid_output/')

        parameters["processes"]["auxiliar_process_list"][0]["Parameters"]["output_file_settings"]["file_name"].SetString(output_name+"_dragseries")
        if parameters.Has("output_processes"):
            parameters["output_processes"]["gid_output"][0]["Parameters"]["output_name"].SetString("gid_output/"+output_name)
        else:
            print("[WARNING] No output processes in the settings!!!")
    if len(argv) == 7:
        parameters["solver_settings"]["model_import_settings"]["input_filename"].SetString(mdpa_file_name)
        parameters["problem_data"]["end_time"].SetDouble(float(end_time))
        parameters["solver_settings"]["time_stepping"]["time_step"].SetDouble(float(time_step))
        parameters["solver_settings"]["formulation"]["dynamic_tau"].SetDouble(float(dyn_visc))
        if not os.path.exists('./drag/'):
            os.makedirs('./drag/')
        if not os.path.exists('./gid_output/'):
            os.makedirs('./gid_output/')

        parameters["processes"]["auxiliar_process_list"][0]["Parameters"]["output_file_settings"]["file_name"].SetString(output_name+"_dragseries")
        if parameters.Has("output_processes"):
            parameters["output_processes"]["gid_output"][0]["Parameters"]["output_name"].SetString("gid_output/"+output_name)
        else:
            print("[WARNING] No output processes in the settings!!!")

    print(parameters)
    print("[INFO] MDPA filename:", parameters["solver_settings"]["model_import_settings"]["input_filename"].GetString())
    print("[INFO] Total analysis time:", parameters["problem_data"]["end_time"].GetDouble())
    print("[INFO] Time step:", parameters["solver_settings"]["time_stepping"]["time_step"].GetDouble())
    if parameters.Has("output_processes"):
        print("[INFO] Output filename:", parameters["output_processes"]["gid_output"][0]["Parameters"]["output_name"].GetString())

    stdout.flush()
    ini_time = time.time()
    simulation = FluidDynamicsAnalysisProblemZero_TimeScreening(model, parameters)
    simulation.Run()
    print("[TIMER] Total analysis time:", time.time()-ini_time)

