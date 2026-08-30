"""The analysis module the active-learning backend launches per label.

The InProcessBackend imports this module, calls Create(model, parameters)
and Run()s the result; the label strategy then reads the requested fields
off the model part. The conductivity comes in through the parameters file
(templated per sample by KratosALSample.parameters).
"""

import KratosMultiphysics as Kratos

import thermal_plate


def Create(model, parameters):
    return ThermalAnalysis(model, parameters)


class ThermalAnalysis:
    def __init__(self, model, parameters):
        self.model = model
        self.conductivity = parameters["case_settings"]["conductivity"].GetDouble()

    def Run(self):
        from KratosMultiphysics.ConvectionDiffusionApplication.convection_diffusion_analysis import (
            ConvectionDiffusionAnalysis)
        model_part = thermal_plate.CreateModelPart(self.model, divisions=20)
        thermal_plate.ApplyCase(model_part, self.conductivity, 1.0, (0.5, 0.5))
        ConvectionDiffusionAnalysis(self.model, thermal_plate._ProjectParameters()).Run()
