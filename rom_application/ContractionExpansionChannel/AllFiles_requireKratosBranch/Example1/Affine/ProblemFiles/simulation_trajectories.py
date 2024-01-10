class TrainingTrajectory():

    def __init__(self, time_step_size):
        self.min_or_max_reached_flag = False
        self.maximum = 2.9
        self.minimum = 0.1
        self.delta_w = 0.025 * time_step_size # this ensures to obtain a maximum narrowing size of 2.9 and a minimum of 0.1 for a total time T=244

    def SetUpInitialNarrowing(self):
        return 2.9 # starting with a wide narrowing

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
        return 0.1 # starting with a narrow narrowing

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

