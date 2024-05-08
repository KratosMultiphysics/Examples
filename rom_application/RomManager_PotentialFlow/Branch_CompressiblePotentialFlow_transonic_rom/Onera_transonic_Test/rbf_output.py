import os
import importlib
import numpy as np
import KratosMultiphysics
import KratosMultiphysics.kratos_utilities
import KratosMultiphysics.CompressiblePotentialFlowApplication as CPFApp
from KratosMultiphysics.vtk_output_process import VtkOutputProcess


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# save parameters
#
def LaunchFakeSimulation(data_set, mu):
    with open('ProjectParameters.json','r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())
        model = KratosMultiphysics.Model()
        parameters_copy = FakeProjectParameters(parameters.Clone(), mu)
        analysis_stage_class = _GetAnalysisStageClass(parameters_copy)
        simulation = FakeSimulation(analysis_stage_class, model, parameters_copy, data_set)
        simulation.Run()

        for process in simulation._GetListOfOutputProcesses():
                if isinstance(process, VtkOutputProcess):
                    output = process
        parameters_output = parameters_copy["output_processes"]["vtk_output"][0]["Parameters"]
        output = VtkOutputProcess(  simulation.model,
                                    parameters_output)
        output.ExecuteInitialize()
        output.ExecuteBeforeSolutionLoop()
        output.ExecuteInitializeSolutionStep()
        output.PrintOutput()
        output.ExecuteFinalizeSolutionStep()
        output.ExecuteFinalize()

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# save parameters
#
def FakeSimulation(cls, global_model, parameters, data_set):

    class CustomSimulation(cls):
        def __init__(self, model,project_parameters):
            super().__init__(model,project_parameters)

        def Run(self):
            self.Initialize()
            self.FinalizeSolutionStep()
            self.OutputSolutionStep()
            self.Finalize()

        def Initialize(self):
            super().Initialize()
            model_part = self.model["FluidModelPart"]
            for node in model_part.Nodes:
                offset = np.where(np.arange(1,model_part.NumberOfNodes()+1, dtype=int) == node.Id)[0][0]*2

                node.SetSolutionStepValue(CPFApp.AUXILIARY_VELOCITY_POTENTIAL, data_set[offset])
                node.SetSolutionStepValue(CPFApp.VELOCITY_POTENTIAL, data_set[offset+1])

        def InitializeSolutionStep(self):
            super().InitializeSolutionStep()

        def FinalizeSolutionStep(self):
            super().FinalizeSolutionStep()

    return CustomSimulation(global_model, parameters)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# load parameters
#
def load_mu_parameters():
    if os.path.exists("mu_train.npy") and os.path.exists("mu_test.npy"):
        mu_train = np.load('mu_train.npy')
        mu_test = np.load('mu_test.npy')
        mu_train =  [mu.tolist() for mu in mu_train]
        mu_test =  [mu.tolist() for mu in mu_test]
    elif os.path.exists("mu_train.npy"):
        mu_train = np.load('mu_train.npy')
        mu_train =  [mu.tolist() for mu in mu_train]
        mu_test = []
    elif os.path.exists("mu_test.npy"):
        mu_test = np.load('mu_test.npy')
        mu_test =  [mu.tolist() for mu in mu_test]
        mu_train = []
    return mu_train, mu_test

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# save parameters
#
def FakeProjectParameters(parameters, mu=None):
    angle_of_attack = mu[0]
    mach_infinity   = mu[1]
    wake_normal     = [-np.sin(angle_of_attack*np.pi/180),0.0,np.cos(angle_of_attack*np.pi/180)]
    parameters["processes"]["boundary_conditions_process_list"][0]["Parameters"]["angle_of_attack"].SetDouble(np.double(angle_of_attack))
    parameters["processes"]["boundary_conditions_process_list"][0]["Parameters"]["mach_infinity"].SetDouble(np.double(mach_infinity))
    parameters["processes"]["boundary_conditions_process_list"][1]["Parameters"]["wake_stl_file_name"].SetString(f'SalomeFiles/Wake_{angle_of_attack}.stl')
    parameters["processes"]["boundary_conditions_process_list"][1]["Parameters"]["wake_process_cpp_parameters"]["wake_normal"].SetVector(wake_normal)
    parameters["output_processes"]["vtk_output"][0]["Parameters"]["output_path"].SetString(f'Results/RBF_{angle_of_attack}, {mach_infinity}')
    return parameters

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# save parameters
#
def _GetAnalysisStageClass(parameters):
    analysis_stage_module_name = parameters["analysis_stage"].GetString()
    analysis_stage_class_name = analysis_stage_module_name.split('.')[-1]
    analysis_stage_class_name = ''.join(x.title() for x in analysis_stage_class_name.split('_'))
    analysis_stage_module = importlib.import_module(analysis_stage_module_name)
    analysis_stage_class = getattr(analysis_stage_module, analysis_stage_class_name)
    return analysis_stage_class

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# save parameters
#
def BuildRBFoutput(mu_list):

    for mu in mu_list:
        case_name = f'{mu[0]}, {mu[1]}'

        #### RBF ####
        rbf_name = f"RBF_Snapshots/{case_name}.npy"
        if os.path.exists(rbf_name):
            rbf = np.load(rbf_name).T
            
            LaunchFakeSimulation(rbf, mu)

# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #


if __name__ == "__main__":

    mu_train, mu_test = load_mu_parameters()

    BuildRBFoutput(mu_train + mu_test)