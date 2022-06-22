import KratosMultiphysics
from KratosMultiphysics.StructuralMechanicsApplication.structural_mechanics_analysis import StructuralMechanicsAnalysis
from KratosMultiphysics.RomApplication.rom_testing_utilities import SetUpSimulationInstance


def FOM():
    with open("ProjectParameters.json",'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())
    model = KratosMultiphysics.Model()
    simulation = StructuralMechanicsAnalysis(model,parameters)
    simulation.Run()


def TrainROM():
    with open("ProjectParametersCreateROMParams.json",'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())
    model = KratosMultiphysics.Model()
    simulation = StructuralMechanicsAnalysis(model,parameters)
    simulation.Run()


def ROM():
    """
    To run a rom simulation, make sure that the following flags are correcly set in the RomParameters.json:
        - "train_hrom": false,
        - "run_hrom": false,
    """
    with open("ProjectParameters.json", 'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())
    model = KratosMultiphysics.Model()
    simulation = SetUpSimulationInstance(model,parameters)
    simulation.Run()


def TrainHROM():
    """
    To run a rom simulation, make sure that the following flags are correcly set in the RomParameters.json:
        - "train_hrom": true,
        - "run_hrom": false,
    """
    with open("ProjectParameters.json", 'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())
    model = KratosMultiphysics.Model()
    simulation = SetUpSimulationInstance(model,parameters)
    simulation.Run()

def HROM():
    """
    To run a rom simulation, make sure that the following flags are correcly set in the RomParameters.json:
        - "train_hrom": false,
        - "run_hrom": true,
    """
    with open("ProjectParameters.json", 'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())
    model = KratosMultiphysics.Model()
    simulation = SetUpSimulationInstance(model,parameters)
    simulation.Run()


if __name__ == "__main__":
    FOM()
    #TrainROM()
    #ROM()
    #TrainHROM()
    #HROM()
