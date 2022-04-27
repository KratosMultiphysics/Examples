import KratosMultiphysics as KM

import numpy as np

def Factory(settings, model):
    if not isinstance(settings, KM.Parameters):
        raise Exception("expected input shall be a Parameters object, encapsulating a json string")
    return ComputeReflectionCoefficientProcess(model, settings["Parameters"])

class ComputeReflectionCoefficientProcess(KM.OutputProcess):

    def __init__(self, model, settings):
        KM.OutputProcess.__init__(self)
        settings.ValidateAndAssignDefaults(self.GetDefaultParameters())

        self.model_part = model.GetModelPart(settings["model_part_name"].GetString())
        self.gauge_coordinates = KM.Point(settings["gauge_coordinates"].GetVector())
        self.interval = KM.IntervalUtility(settings)
        self.incident_direction = KM.Array3(settings["incident_direction"].GetVector())
        self.variable = KM.KratosGlobals.GetVariable(settings["variable_name"].GetString())
        self.tolerance = settings["search_tolerance"].GetDouble()
        self.file_name = settings["file_name"].GetString() + ".dat"

    @staticmethod
    def GetDefaultParameters():
        return KM.Parameters("""{
            "model_part_name"    : "model_part",
            "interval"           : [0, "End"],
            "incident_direction" : [1, 0, 0],
            "gauge_coordinates"  : [0, 0, 0],
            "search_tolerance"   : 1e-6,
            "variable_name"      : "FREE_SURFACE_ELEVATION",
            "file_name"          : "file_name"
        }""")

    @staticmethod
    def IsOutputStep():
        return False

    @staticmethod
    def PrintOutput():
        pass

    def ExecuteInitialize(self):
        self.incident_max = -1e16
        self.incident_min =  1e16
        self.reflected_max = -1e16
        self.reflected_min =  1e16

        configuration = KM.Configuration.Current
        locator = KM.BruteForcePointLocator(self.model_part)
        self.area_coords = KM.Vector()
        found_id = locator.FindElement(self.gauge_coordinates, self.area_coords, configuration, self.tolerance)
        self.element = self.model_part.Elements[found_id]

    def ExecuteFinalizeSolutionStep(self):
        current_time = self.model_part.ProcessInfo[KM.TIME]

        if self.interval.IsInInterval(current_time):
            value = self._GetValue(self.variable)
            velocity = self._GetValue(KM.VELOCITY)
            if value * np.dot(velocity, self.incident_direction) > 0:
                self.incident_max = max(self.incident_max, value)
                self.incident_min = min(self.incident_min, value)
            else:
                self.reflected_max = max(self.reflected_max, value)
                self.reflected_min = min(self.reflected_min, value)

    def ExecuteFinalize(self):
        incident_wave = self.incident_max - self.incident_min
        reflected_wave = self.reflected_max - self.reflected_min
        reflection_coefficient = reflected_wave / incident_wave

        print("Incident wave: {}".format(incident_wave))
        print("Reflected wave: {}".format(reflected_wave))
        print("The reflection coefficient is : {}".format(reflection_coefficient))

        with open(self.file_name, 'a') as file:
            file.write('{}\n'.format(reflection_coefficient))

    def _GetValue(self, variable):
        nodes = self.element.GetNodes()
        value = self.area_coords[0] * nodes[0].GetSolutionStepValue(variable)
        for node , N in zip(nodes[1:], self.area_coords[1:]):
            value += N * node.GetSolutionStepValue(variable)
        return value
