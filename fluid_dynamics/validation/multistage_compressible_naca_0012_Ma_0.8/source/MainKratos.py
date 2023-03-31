import KratosMultiphysics
from KratosMultiphysics.multistage_analysis import MultistageAnalysis

if __name__ == "__main__":

    with open("ProjectParameters.json", 'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())

    global_model = KratosMultiphysics.Model()
    multistage_simulation = MultistageAnalysis(global_model, parameters)
    multistage_simulation.Run()
