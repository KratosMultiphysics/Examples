import sys
import time
import importlib

import KratosMultiphysics

def CreateAnalysisStageWithFlushInstance(cls, global_model, parameters):
    class AnalysisStageWithFlush(cls):

        def __init__(self, model,project_parameters, flush_frequency=10.0):
            super().__init__(model,project_parameters)
            self.flush_frequency = flush_frequency
            self.last_flush = time.time()
            sys.stdout.flush()

        def ModifyInitialGeometry(self):
            super().ModifyInitialGeometry()

            # Auxiliary function to create the concentrated mass elements
            # First argument is the model part name and second one the extra mass to be applied at each node
            self.__CreateNodalConcentratedMassElements("Structure.GENERIC_Esquinas", 4145.75)
            self.__CreateNodalConcentratedMassElements("Structure.GENERIC_porteria-ext-esquina", 1911)
            self.__CreateNodalConcentratedMassElements("Structure.GENERIC_porteria-ext-centro", 1811.25)
            self.__CreateNodalConcentratedMassElements("Structure.GENERIC_largo-int-centro", 3663.275)
            self.__CreateNodalConcentratedMassElements("Structure.GENERIC_largo-int-esquinas", 3755)
            self.__CreateNodalConcentratedMassElements("Structure.GENERIC_porteria-int-esquinas", 3784.375)
            self.__CreateNodalConcentratedMassElements("Structure.GENERIC_porteria-int-centro", 3718.75)
            self.__CreateNodalConcentratedMassElements("Structure.GENERIC_largo-ext-intermedio", 2887.5)
            self.__CreateNodalConcentratedMassElements("Structure.GENERIC_largo-ext-esquinas", 1940.75)
            self.__CreateNodalConcentratedMassElements("Structure.GENERIC_largo-ext-centro", 3730.3)

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

        def __CreateNodalConcentratedMassElements(self, model_part_name, mass_value):
            # Search for the maximum element id
            main_model_part = self.model.GetModelPart("Structure")
            max_id = 0
            for element in main_model_part.Elements:
                if element.Id > max_id:
                    max_id = element.Id

            # For each node create a concentrated nodal mass element
            mass_nodes_model_part = self.model.GetModelPart(model_part_name)
            property_0 = mass_nodes_model_part.GetProperties(0) # Get the default empty properties
            for node in mass_nodes_model_part.Nodes:
                # Create the concentrated nodal mass element
                max_id += 1 # Update the element id
                node_list = [node.Id] # The nodal list is just the current node
                new_element = mass_nodes_model_part.CreateNewElement("NodalConcentratedElement3D1N", max_id, node_list, property_0)

                # Set the extra mass value to current element
                # IMPORTANT: this needs to be mass (internally it will be multiplied by the gravity, which value is the VOLUME_ACCELERATION within the ProjectParameters.json)
                new_element.SetValue(KratosMultiphysics.NODAL_MASS, mass_value)


    return AnalysisStageWithFlush(global_model, parameters)

if __name__ == "__main__":

    with open("ProjectParameters.json", 'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())

    analysis_stage_module_name = parameters["analysis_stage"].GetString()
    analysis_stage_class_name = analysis_stage_module_name.split('.')[-1]
    analysis_stage_class_name = ''.join(x.title() for x in analysis_stage_class_name.split('_'))

    analysis_stage_module = importlib.import_module(analysis_stage_module_name)
    analysis_stage_class = getattr(analysis_stage_module, analysis_stage_class_name)

    global_model = KratosMultiphysics.Model()
    simulation = CreateAnalysisStageWithFlushInstance(analysis_stage_class, global_model, parameters)
    simulation.Run()
