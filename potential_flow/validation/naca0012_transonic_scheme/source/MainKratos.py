import sys
import time
import importlib
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cbook

import KratosMultiphysics

def CreateAnalysisStageWithFlushInstance(cls, global_model, parameters):
    class AnalysisStageWithFlush(cls):

        def __init__(self, model,project_parameters, flush_frequency=10.0):
            super().__init__(model,project_parameters)
            self.flush_frequency = flush_frequency
            self.last_flush = time.time()
            sys.stdout.flush()

        def Initialize(self):
            super().Initialize()
            sys.stdout.flush()

        def FinalizeSolutionStep(self):
            super().FinalizeSolutionStep()
    
            if self.parallel_type == "OpenMP":
                now = time.time()
                if now - self.last_flush > self.flush_frequency:
                    sys.stdout.flush()
                    self.last_flush = now

    return AnalysisStageWithFlush(global_model, parameters)

if __name__ == "__main__":

    critical_machs_and_upwind_factor_constants_list = []
    critical_machs_and_upwind_factor_constants_list.append([0.9 , 2.0, 1e-3 , 0.95, 1.0])
    critical_machs_and_upwind_factor_constants_list.append([0.9 , 2.0, 1e-30, 0.95, 1.0]) # not updated
    critical_machs_and_upwind_factor_constants_list.append([0.95, 1.0, 1e-30, 0.95, 1.0]) # not updated

    with open("ProjectParameters.json", 'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())

    analysis_stage_module_name = parameters["analysis_stage"].GetString()
    analysis_stage_class_name = analysis_stage_module_name.split('.')[-1]
    analysis_stage_class_name = ''.join(x.title() for x in analysis_stage_class_name.split('_'))

    analysis_stage_module = importlib.import_module(analysis_stage_module_name)
    analysis_stage_class = getattr(analysis_stage_module, analysis_stage_class_name)

    for id, values in enumerate(critical_machs_and_upwind_factor_constants_list): 
        KratosMultiphysics.kratos_utilities.DeleteFileIfExisting("residual_per_iteration.txt")

        parameters["solver_settings"]["scheme_settings"]["initial_critical_mach"].SetDouble(values[0])
        parameters["solver_settings"]["scheme_settings"]["initial_upwind_factor_constant"].SetDouble(values[1])

        parameters["solver_settings"]["scheme_settings"]["update_relative_residual_norm"].SetDouble(values[2]) 

        parameters["solver_settings"]["scheme_settings"]["target_critical_mach"].SetDouble(values[3])
        parameters["solver_settings"]["scheme_settings"]["target_upwind_factor_constant"].SetDouble(values[4]) 

        output_name = f'{values[0]}_{values[1]}_{values[2]}_{values[3]}_{values[4]}'
        parameters["output_processes"]["gid_output"][0]["Parameters"]["output_name"].SetString(f'gid_output/{output_name}') 
        parameters["output_processes"]["vtk_output"][0]["Parameters"]["output_path"].SetString(f'vtk_output/{output_name}') 

        global_model = KratosMultiphysics.Model()
        simulation = CreateAnalysisStageWithFlushInstance(analysis_stage_class, global_model, parameters)
        simulation.Run()

        modelpart = global_model["FluidModelPart.Body2D_Body"]
        fout = open(f'{id}.dat','w')
        for i,node in enumerate(modelpart.Nodes):
            x  = node.X0
            cp = node.GetValue(KratosMultiphysics.PRESSURE_COEFFICIENT)
            fout.write("%s %s\n" %(x,cp))
        fout.close()

    x     = np.loadtxt('0.dat', usecols=(0,))
    cp_0  = np.loadtxt('0.dat', usecols=(1,))
    cp_1  = np.loadtxt('1.dat', usecols=(1,))
    cp_2  = np.loadtxt('2.dat', usecols=(1,))

    fig, ax = plt.subplots()
    fig.set_figwidth(8.0)
    fig.set_figheight(6.0)
    # make data
    ax.plot( x, -cp_0, ".", label='Mc = 0.90 Ufc = 2.0 updated to Mc = 0.95  Ufc = 1.0')
    ax.plot( x, -cp_1, ".", label='Mc = 0.90 Ufc = 2.0 not updated')
    ax.plot( x, -cp_2, ".", label='Mc = 0.95 Ufc = 1.0 not updated')
    ax.grid()
    # inset Axes....
    x1, x2, y1, y2 = 0.40, 0.60, -0.1, 1.0  # subregion of the original image
    axins = ax.inset_axes([0.65, 0.45, 0.3, 0.52])
    axins.set_xlim(x1, x2)
    axins.set_ylim(y1, y2)

    axins.plot( x, -cp_0, ".")
    axins.plot( x, -cp_1, ".")
    axins.plot( x, -cp_2, ".")
    axins.grid()
    ax.indicate_inset_zoom(axins, edgecolor="grey")

    fig = plt.ylabel('Cp')
    fig = plt.xlabel('x')
    fig = plt.legend()
    fig = plt.title('Naca0012 - Alpha = 0.0º Mach = 0.8')
    fig = plt.tight_layout()
    fig = plt.savefig("Airfoils_Cp_x.png", dpi=400)
    fig = plt.close('all')