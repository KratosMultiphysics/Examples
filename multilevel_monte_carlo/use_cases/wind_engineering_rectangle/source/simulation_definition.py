# Import Python libraries
import os
import numpy as np

# Import Kratos
import KratosMultiphysics
import KratosMultiphysics.MultilevelMonteCarloApplication
import KratosMultiphysics.MappingApplication

# Importing the problem analysis stage class
from FluidDynamicsAnalysisProblemZero import FluidDynamicsAnalysisProblemZero
from KratosMultiphysics.FluidDynamicsApplication import check_and_prepare_model_process_fluid

# Avoid printing of Kratos informations
KratosMultiphysics.Logger.GetDefaultOutput().SetSeverity(KratosMultiphysics.Logger.Severity.WARNING)


class SimulationScenario(FluidDynamicsAnalysisProblemZero):
    def __init__(self,input_model,input_parameters,sample):
        super().__init__(input_model,input_parameters)
        self.sample = sample
        self.mapping = False
        self.interest_model_part = "MainModelPart.NoSlip2D_No_Slip_Auto1"
        self.number_instances_time_power_sums = 0
        self.IsVelocityFieldPerturbed = False
        self.filename = "filename"

    def ModifyInitialProperties(self):
        """
        function changing print to file settings
        input:  self: an instance of the class
        """
        super().ModifyInitialProperties()
        # add capability of saving force time series
        raw_path, raw_filename = os.path.split(self.filename)
        self.project_parameters["processes"]["auxiliar_process_list"][0]["Parameters"]["write_drag_output_file"].SetBool(True)
        self.project_parameters["processes"]["auxiliar_process_list"][0]["Parameters"]["output_file_settings"]["file_name"].SetString(raw_filename)
        self.project_parameters["processes"]["auxiliar_process_list"][0]["Parameters"]["output_file_settings"]["output_path"].SetString(raw_path)
        # introduce stochasticity in inlet
        if self.project_parameters["problem_data"]["random_velocity_modulus"]:
            random_inlet = max(0.1,self.sample[1])
            self.project_parameters["processes"]["boundary_conditions_process_list"][0]["Parameters"]["value"][0].SetDouble(random_inlet)
        # save new seed
        if (self.project_parameters["problem_data"]["perturbation"]["type"].GetString() == "correlated"):
            self.project_parameters["processes"]["initial_conditions_process_list"][0]["Parameters"]["seed"].SetInt(self.sample[0])

    def ApplyBoundaryConditions(self):
        """
        function introducing the stochasticity in the problem
        input:  self: an instance of the class
        """
        super().ApplyBoundaryConditions()
        if (self.IsVelocityFieldPerturbed is False) and (self.project_parameters["problem_data"]["perturbation"]["type"].GetString() == "uncorrelated"):
            np.random.seed(self.sample[0])
            print("[SCREENING] perturbing the domain:","Yes")
            self.main_model_part = self.model.GetModelPart("MainModelPart")
            # load velocity field
            with open("average_velocity_field_RectangularCylinder_300.0_25k.dat") as dat_file:
                lines=dat_file.readlines()
                for line, node in zip(lines, self.main_model_part.Nodes):
                    if not (node.IsFixed(KratosMultiphysics.VELOCITY_X) or node.IsFixed(KratosMultiphysics.VELOCITY_Y) or node.IsFixed(KratosMultiphysics.VELOCITY_Z) or node.IsFixed(KratosMultiphysics.PRESSURE)):
                        # retrieve velocity
                        velocity = KratosMultiphysics.Vector(3, 0.0)
                        velocity[0] = float(line.split(' ')[0])
                        velocity[1] = float(line.split(' ')[1])
                        velocity[2] = float(line.split(' ')[2])
                        # compute uncorrelated perturbation
                        perturbation_intensity = self.project_parameters["problem_data"]["perturbation"]["intensity"].GetDouble()
                        perturbation = np.random.uniform(-perturbation_intensity,perturbation_intensity,2) * velocity.norm_2() # all nodes and directions different value
                        # sum avg velocity and perturbation
                        velocity[0] = velocity[0] + perturbation[0]
                        velocity[1] = velocity[1] + perturbation[1]
                        node.SetSolutionStepValue(KratosMultiphysics.VELOCITY, 1, velocity)
            self.IsVelocityFieldPerturbed = True
        else:
            print("[SCREENING] perturbing the domain:", "No")

    def ComputeNeighbourElements(self):
        """
        function computing neighbour elements, required by our boundary conditions
        input:  self: an instance of the class
        """
        tmoc = KratosMultiphysics.TetrahedralMeshOrientationCheck
        throw_errors = False
        flags = (tmoc.COMPUTE_NODAL_NORMALS).AsFalse() | (tmoc.COMPUTE_CONDITION_NORMALS).AsFalse()
        flags |= tmoc.ASSIGN_NEIGHBOUR_ELEMENTS_TO_CONDITIONS
        KratosMultiphysics.TetrahedralMeshOrientationCheck(self._GetSolver().main_model_part.GetSubModelPart("fluid_computational_model_part"),throw_errors, flags).Execute()

    def Initialize(self):
        """
        function initializing moment estimator array
        input:  self: an instance of the class
        """
        super().Initialize()
        # compute neighbour elements required for current boundary conditions and not automatically run due to remeshing
        self.ComputeNeighbourElements()
        # initialize MomentEstimator class for each qoi to build time power sums
        self.moment_estimator_array = [[[0.0],[0.0],[0.0],[0.0],[0.0],[0.0],[0.0],[0.0],[0.0],[0.0]] for _ in range (0,1)] # +1 is for drag force x
        if (self.mapping is True):
            power_sums_parameters = KratosMultiphysics.Parameters("""{
                "reference_variable_name": "PRESSURE"
                }""")
            self.power_sums_process_mapping = KratosMultiphysics.MultilevelMonteCarloApplication.PowerSumsStatistics(self.mapping_reference_model.GetModelPart(self.interest_model_part),power_sums_parameters)
            self.power_sums_process_mapping.ExecuteInitialize()
            print("[SCREENING] number nodes of submodelpart + drag force:",self.mapping_reference_model.GetModelPart(self.interest_model_part).NumberOfNodes()+1) # +1 is for drag force x
        else:
            power_sums_parameters = KratosMultiphysics.Parameters("""{
                "reference_variable_name": "PRESSURE"
                }""")
            self.power_sums_process = KratosMultiphysics.MultilevelMonteCarloApplication.PowerSumsStatistics(self.model.GetModelPart(self.interest_model_part),power_sums_parameters)
            self.power_sums_process.ExecuteInitialize()
            print("[SCREENING] number nodes of submodelpart + drag force:",self.model.GetModelPart(self.interest_model_part).NumberOfNodes()+1) # +1 is for drag force x
        print("[SCREENING] mapping flag:",self.mapping)

    def FinalizeSolutionStep(self):
        """
        function applying mapping if required and updating moment estimator array
        input:  self: an instance of the class
        """
        super().FinalizeSolutionStep()
        # run if current index is index of interest
        if (self.is_current_index_maximum_index is True):
            # avoid burn-in time
            if (self.model.GetModelPart(self.interest_model_part).ProcessInfo.GetPreviousTimeStepInfo().GetValue(KratosMultiphysics.TIME) >= \
                self.project_parameters["problem_data"]["burnin_time"].GetDouble()):
                # update number of contributions to time power sums
                self.number_instances_time_power_sums = self.number_instances_time_power_sums + 1
                # update power sums of drag force x and base moment z
                self.moment_estimator_array[0][0][0] = self.moment_estimator_array[0][0][0] + self.current_force_x
                self.moment_estimator_array[0][1][0] = self.moment_estimator_array[0][1][0] + self.current_force_x**2
                self.moment_estimator_array[0][2][0] = self.moment_estimator_array[0][2][0] + self.current_force_x**3
                self.moment_estimator_array[0][3][0] = self.moment_estimator_array[0][3][0] + self.current_force_x**4
                self.moment_estimator_array[0][4][0] = self.moment_estimator_array[0][4][0] + self.current_force_x**5
                self.moment_estimator_array[0][5][0] = self.moment_estimator_array[0][5][0] + self.current_force_x**6
                self.moment_estimator_array[0][6][0] = self.moment_estimator_array[0][6][0] + self.current_force_x**7
                self.moment_estimator_array[0][7][0] = self.moment_estimator_array[0][7][0] + self.current_force_x**8
                self.moment_estimator_array[0][8][0] = self.moment_estimator_array[0][8][0] + self.current_force_x**9
                self.moment_estimator_array[0][9][0] = self.moment_estimator_array[0][9][0] + self.current_force_x**10
                if (self.mapping is True):
                    # mapping from current model part of interest to reference model part the pressure
                    mapping_parameters = KratosMultiphysics.Parameters("""{
                        "mapper_type": "nearest_element",
                        "interface_submodel_part_origin": "MainModelPart.NoSlip2D_No_Slip_Auto1",
                        "interface_submodel_part_destination": "MainModelPart.NoSlip2D_No_Slip_Auto1",
                        "echo_level" : 3
                        }""")
                    mapper = KratosMultiphysics.MappingApplication.MapperFactory.CreateMapper(self._GetSolver().main_model_part,self.mapping_reference_model.GetModelPart("MainModelPart"),mapping_parameters)
                    mapper.Map(KratosMultiphysics.PRESSURE,KratosMultiphysics.PRESSURE)
                    # update pressure field
                    self.power_sums_process_mapping.ExecuteFinalizeSolutionStep()
                else:
                    # update pressure field
                    self.power_sums_process.ExecuteFinalizeSolutionStep()
        else:
            pass

    def EvaluateQuantityOfInterest(self):
        """
        function evaluating the QoI of the problem: lift coefficient
        input:  self: an instance of the class
        """
        # run if current index is index of interest
        if (self.is_current_index_maximum_index is True):
            print("[SCREENING] computing qoi current index:",self.is_current_index_maximum_index)
            qoi_list = []
            # append time average drag force
            qoi_list.append(self.mean_force_x)
            # append time average pressure
            averaged_pressure_list = []
            if (self.mapping is not True):
                for node in self.model.GetModelPart(self.interest_model_part).Nodes:
                    averaged_pressure_list.append(node.GetValue(KratosMultiphysics.ExaquteSandboxApplication.AVERAGED_PRESSURE))
            elif (self.mapping is True):
                for node in self.mapping_reference_model.GetModelPart(self.interest_model_part).Nodes:
                    averaged_pressure_list.append(node.GetValue(KratosMultiphysics.ExaquteSandboxApplication.AVERAGED_PRESSURE))
            qoi_list.append(averaged_pressure_list)
            # append number of contributions to the power sums list
            self.moment_estimator_array[0].append(self.number_instances_time_power_sums) # drag force x
            # append drag force time series power sums
            qoi_list.append(self.moment_estimator_array[0]) # drag force x
            # append pressure time series power sums
            pressure_list = []
            if (self.mapping is True):
                for node in self.mapping_reference_model.GetModelPart(self.interest_model_part).Nodes:
                    S1 = node.GetValue(KratosMultiphysics.MultilevelMonteCarloApplication.POWER_SUM_1)
                    S2 = node.GetValue(KratosMultiphysics.MultilevelMonteCarloApplication.POWER_SUM_2)
                    S3 = node.GetValue(KratosMultiphysics.MultilevelMonteCarloApplication.POWER_SUM_3)
                    S4 = node.GetValue(KratosMultiphysics.MultilevelMonteCarloApplication.POWER_SUM_4)
                    S5 = node.GetValue(KratosMultiphysics.MultilevelMonteCarloApplication.POWER_SUM_5)
                    S6 = node.GetValue(KratosMultiphysics.MultilevelMonteCarloApplication.POWER_SUM_6)
                    S7 = node.GetValue(KratosMultiphysics.MultilevelMonteCarloApplication.POWER_SUM_7)
                    S8 = node.GetValue(KratosMultiphysics.MultilevelMonteCarloApplication.POWER_SUM_8)
                    S9 = node.GetValue(KratosMultiphysics.MultilevelMonteCarloApplication.POWER_SUM_9)
                    S10 = node.GetValue(KratosMultiphysics.MultilevelMonteCarloApplication.POWER_SUM_10)
                    M = self.number_instances_time_power_sums
                    power_sums = [[S1],[S2],[S3],[S4],[S5],[S6],[S7],[S8],[S9],[S10],M]
                    pressure_list.append(power_sums)
            else:
                for node in self.model.GetModelPart(self.interest_model_part).Nodes:
                    S1 = node.GetValue(KratosMultiphysics.MultilevelMonteCarloApplication.POWER_SUM_1)
                    S2 = node.GetValue(KratosMultiphysics.MultilevelMonteCarloApplication.POWER_SUM_2)
                    S3 = node.GetValue(KratosMultiphysics.MultilevelMonteCarloApplication.POWER_SUM_3)
                    S4 = node.GetValue(KratosMultiphysics.MultilevelMonteCarloApplication.POWER_SUM_4)
                    S5 = node.GetValue(KratosMultiphysics.MultilevelMonteCarloApplication.POWER_SUM_5)
                    S6 = node.GetValue(KratosMultiphysics.MultilevelMonteCarloApplication.POWER_SUM_6)
                    S7 = node.GetValue(KratosMultiphysics.MultilevelMonteCarloApplication.POWER_SUM_7)
                    S8 = node.GetValue(KratosMultiphysics.MultilevelMonteCarloApplication.POWER_SUM_8)
                    S9 = node.GetValue(KratosMultiphysics.MultilevelMonteCarloApplication.POWER_SUM_9)
                    S10 = node.GetValue(KratosMultiphysics.MultilevelMonteCarloApplication.POWER_SUM_10)
                    M = self.number_instances_time_power_sums
                    power_sums = [[S1],[S2],[S3],[S4],[S5],[S6],[S7],[S8],[S9],[S10],M]
                    pressure_list.append(power_sums)
        else:
            print("[SCREENING] computing qoi current index:",self.is_current_index_maximum_index)
            qoi_list = None
        qoi_list.append(pressure_list)
        # print("[SCREENING] qoi list:",qoi_list)
        return qoi_list

    def MappingAndEvaluateQuantityOfInterest(self):
        """
        function mapping the weighted pressure on reference model and calling evaluation of quantit of interest
        input:  self: an instance of the class
        """
        # map from current model part of interest to reference model part
        mapping_parameters = KratosMultiphysics.Parameters("""{
            "mapper_type": "nearest_element",
            "interface_submodel_part_origin": "MainModelPart.NoSlip2D_No_Slip_Auto1",
            "interface_submodel_part_destination": "MainModelPart.NoSlip2D_No_Slip_Auto1",
            "echo_level" : 3
            }""")
        mapper = KratosMultiphysics.MappingApplication.MapperFactory.CreateMapper(self._GetSolver().main_model_part,self.mapping_reference_model.GetModelPart("MainModelPart"),mapping_parameters)
        mapper.Map(KratosMultiphysics.ExaquteSandboxApplication.AVERAGED_PRESSURE, \
            KratosMultiphysics.ExaquteSandboxApplication.AVERAGED_PRESSURE,        \
            KratosMultiphysics.MappingApplication.Mapper.FROM_NON_HISTORICAL |     \
            KratosMultiphysics.MappingApplication.Mapper.TO_NON_HISTORICAL)
        # evaluate qoi
        qoi_list = self.EvaluateQuantityOfInterest()
        return qoi_list
