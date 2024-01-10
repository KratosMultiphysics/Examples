import numpy as np
from matplotlib import pyplot as plt

class TrainingTrajectory():

    def __init__(self, time_step_size):
        self.min_or_max_reached_flag = False
        self.maximum = 2.9
        self.minimum = 0.1
        self.delta_w = 0.025 * time_step_size # this ensures to obtain a maximum narrowing size of 2.9 and a minimum of 0.1 for a total time T=244

    def SetUpInitialNarrowing(self):
        return self.maximum # starting with a wide narrowing

    def UpdateW(self, w):
        ####Train trajectory####
        if not self.min_or_max_reached_flag: #contraction
            w -= self.delta_w
            if w < self.minimum:
                w =self.minimum
                self.min_or_max_reached_flag = True
        else: #expansion
            w += self.delta_w
            if w > self.maximum:
                w = self.maximum
        return w



class TestingTrajectory():

    def __init__(self, time_step_size):
        self.min_or_max_reached_flag = False
        self.maximum = 2.9
        self.minimum = 0.1
        self.delta_w = 0.025 * time_step_size # this ensures to obtain a maximum narrowing size of 2.9 and a minimum of 0.1 for a total time T=244

    def SetUpInitialNarrowing(self):
        return self.minimum # starting with a narrow narrowing

    def UpdateW(self, w):
        ####Test trajectory####
        if not self.min_or_max_reached_flag:#expansion
            w += self.delta_w
            if w > self.maximum:
                w = self.maximum
                self.min_or_max_reached_flag = True
        else: #contraction
            w -= self.delta_w
            if w < self.minimum:
                w =self.minimum
        return w




class TestingTrajectory2():


    def SetUpInitialNarrowing(self):
        return self.UpdateW(0)


    def UpdateW(self, time, T=100):
        # Normalizing time t to the range [0, 2*pi]
        fixed_deformation_factor = 2.8
        normalized_t = (2 * np.pi * time) / T

        # Defining the function using a combination of sine and cosine functions
        # with a phase shift and frequency adjustments for more variations
        return 0.1 + (0.5 * (1 + np.sin(normalized_t - np.pi/2) * np.cos(3 * normalized_t)) * fixed_deformation_factor)
