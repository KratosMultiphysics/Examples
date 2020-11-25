#Kratos Imports
import KratosMultiphysics
import KratosMultiphysics.FluidDynamicsApplication
from KratosMultiphysics.FluidDynamicsApplication.fluid_dynamics_analysis import FluidDynamicsAnalysis
import KratosMultiphysics.MeshingApplication as KratosMeshing
import KratosMultiphysics.StatisticsApplication as KratosStatistics

class FluidDynamicsAnalysisWithMetrics(FluidDynamicsAnalysis):
    def __init__(self,model, parameters, remeshing_parameters):
        self.remeshing_parameters = remeshing_parameters
        self.metric_parameters = remeshing_parameters["metric_parameters"]
        super().__init__(model,parameters)
    def Initialize(self):
        super().Initialize()
        # Computing nodal_h that will be needed in the metric processes
        find_nodal_h = KratosMultiphysics.FindNodalHNonHistoricalProcess(self._GetSolver().main_model_part)
        find_nodal_h.Execute()

    def FinalizeSolutionStep(self):
        super().FinalizeSolutionStep()
        self.metric_parameters["hessian_strategy_parameters"]["non_historical_metric_variable"].SetBool(False)
        if self.time >= self.remeshing_parameters["start_time_control_value"].GetDouble():
            if "VELOCITY" in self.remeshing_parameters["variables_to_remesh"].GetStringArray():
                if self.time >= self.remeshing_parameters["start_time_control_value"].GetDouble():
                    hessian_metric = KratosMeshing.ComputeHessianSolMetricProcess(self._GetSolver().main_model_part,KratosMultiphysics.VELOCITY_X, self.metric_parameters)
                    hessian_metric.Execute()
                    hessian_metric = KratosMeshing.ComputeHessianSolMetricProcess(self._GetSolver().main_model_part,KratosMultiphysics.VELOCITY_Y, self.metric_parameters)
                    hessian_metric.Execute()
                    hessian_metric = KratosMeshing.ComputeHessianSolMetricProcess(self._GetSolver().main_model_part,KratosMultiphysics.VELOCITY_Z, self.metric_parameters)
                    hessian_metric.Execute()
            if "PRESSURE" in self.remeshing_parameters["variables_to_remesh"].GetStringArray():
                if self.time >= self.remeshing_parameters["start_time_control_value"].GetDouble():
                    hessian_metric = KratosMeshing.ComputeHessianSolMetricProcess(self._GetSolver().main_model_part,KratosMultiphysics.PRESSURE, self.metric_parameters)
                    hessian_metric.Execute()

    def Finalize(self):
        super().Finalize()
        self.metric_parameters["hessian_strategy_parameters"]["non_historical_metric_variable"].SetBool(True)
        if "AVERAGE_VELOCITY" in self.remeshing_parameters["variables_to_remesh"].GetStringArray():
            hessian_metric = KratosMeshing.ComputeHessianSolMetricProcess(self._GetSolver().main_model_part,KratosStatistics.VECTOR_3D_MEAN_X, self.metric_parameters)
            hessian_metric.Execute()
            hessian_metric = KratosMeshing.ComputeHessianSolMetricProcess(self._GetSolver().main_model_part,KratosStatistics.VECTOR_3D_MEAN_Y, self.metric_parameters)
            hessian_metric.Execute()
            hessian_metric = KratosMeshing.ComputeHessianSolMetricProcess(self._GetSolver().main_model_part,KratosStatistics.VECTOR_3D_MEAN_Z, self.metric_parameters)
            hessian_metric.Execute()
        if "AVERAGE_PRESSURE" in self.remeshing_parameters["variables_to_remesh"].GetStringArray():
            hessian_metric = KratosMeshing.ComputeHessianSolMetricProcess(self._GetSolver().main_model_part,KratosStatistics.SCALAR_MEAN, self.metric_parameters)
            hessian_metric.Execute()

if __name__ == '__main__':

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
        parameter_file_name = "ProjectParameters.json"

    with open(parameter_file_name,'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())

    with open("RemeshingParameters.json",'r') as parameter_file:
        remeshing_parameters = KratosMultiphysics.Parameters(parameter_file.read())

    model = KratosMultiphysics.Model()
    simulation = FluidDynamicsAnalysisWithMetrics(model,parameters,remeshing_parameters)
    simulation.Run()
