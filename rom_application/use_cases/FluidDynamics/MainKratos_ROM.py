import KratosMultiphysics
from KratosMultiphysics.FluidDynamicsApplication.fluid_dynamics_analysis import FluidDynamicsAnalysis
from KratosMultiphysics.RomApplication.rom_testing_utilities import SetUpSimulationInstance
import json


def TrainROM(end_time=30):
    with open("ProjectParametersCreateROMParams.json",'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())
    model = KratosMultiphysics.Model()
    parameters = updateProjectParameters('FOM',parameters,end_time)
    simulation = FluidDynamicsAnalysis(model,parameters)
    simulation.Run()


def ROM(end_time=30):
    """
    To run a rom simulation, make sure that the following flags are correcly set in the RomParameters.json:
        - "train_hrom": false,
        - "run_hrom": false,
    """
    with open("ProjectParameters.json", 'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())
    model = KratosMultiphysics.Model()
    parameters = updateProjectParameters('ROM',parameters,end_time)
    simulation = SetUpSimulationInstance(model,parameters)
    simulation.Run()


def TrainHROM(end_time=30):
    """
    To run a rom simulation, make sure that the following flags are correcly set in the RomParameters.json:
        - "train_hrom": true,
        - "run_hrom": false,
    """
    with open("ProjectParameters.json", 'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())
    parameters = updateProjectParameters('ROM',parameters,end_time)
    model = KratosMultiphysics.Model()
    simulation = SetUpSimulationInstance(model,parameters)
    simulation.Run()

def HROM(end_time = 30):
    """
    To run a rom simulation, make sure that the following flags are correcly set in the RomParameters.json:
        - "train_hrom": false,
        - "run_hrom": true,
    """
    with open("ProjectParametersHROM.json", 'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())
    parameters = updateProjectParameters('HROM',parameters,end_time)
    model = KratosMultiphysics.Model()
    simulation = SetUpSimulationInstance(model,parameters)
    simulation.Run()

def updateProjectParameters(results_name,parameters,end_time):

    #susbtituting time_step parameter
    parameters["problem_data"]["end_time"].SetInt(end_time)

    #storing results into a results folder
    parameters["output_processes"]["gid_output"][0]["Parameters"]["output_name"].SetString('Results/'+ results_name)
    parameters["output_processes"]["vtk_output"][0]["Parameters"]["output_path"].SetString('Results/vtk_output_'+ results_name)

    return parameters



def setting_flags_rom_parameters(simulation_to_run = 'ROM'):
    #other options: "trainHROM", "runHROM"
    #taken from code by Philipa & Catharina
    parameters_file_name = './RomParameters.json'
    with open(parameters_file_name, 'r+') as parameter_file:
        f=json.load(parameter_file)
        if simulation_to_run=='ROM':
            f['train_hrom']=False
            f['run_hrom']=False
        elif simulation_to_run=='trainHROM':
            f['train_hrom']=True
            f['run_hrom']=False
        elif simulation_to_run=='runHROM':
            f['train_hrom']=False
            f['run_hrom']=True
        else:
            print('Unknown operation. Add new rule!')
        parameter_file.seek(0)
        json.dump(f,parameter_file,indent=4)
        parameter_file.truncate()



if __name__ == "__main__":


    TrainROM()
    #ROM()
    setting_flags_rom_parameters(simulation_to_run = 'trainHROM')
    TrainHROM()
    setting_flags_rom_parameters(simulation_to_run = 'runHROM')
    HROM()
