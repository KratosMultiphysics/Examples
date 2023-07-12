import sys
import importlib
import KratosMultiphysics
from KratosMultiphysics.project import Project

if __name__ == "__main__":

    # Check if a custom project parameters filename is provided
    if len(sys.argv) == 1:
        project_parameters_filename = "ProjectParameters.json"
    else:
        project_parameters_filename = str(sys.argv[1])

    # Parse simulation settings and run simulation
    with open(project_parameters_filename, 'r') as parameter_file:
        project_parameters = KratosMultiphysics.Parameters(parameter_file.read())

        project = Project(project_parameters)

        orchestrator_reg_entry = KratosMultiphysics.Registry[project.GetSettings()["orchestrator"]["name"].GetString()]
        orchestrator_module = importlib.import_module(orchestrator_reg_entry["ModuleName"])
        orchestrator_class = getattr(orchestrator_module, orchestrator_reg_entry["ClassName"])
        orchestrator_instance = orchestrator_class(project)
        orchestrator_instance.Run()