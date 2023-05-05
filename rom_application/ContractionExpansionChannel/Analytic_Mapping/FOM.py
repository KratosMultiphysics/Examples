import KratosMultiphysics
from KratosMultiphysics.FluidDynamicsApplication.fluid_dynamics_analysis import FluidDynamicsAnalysis

import json

import numpy as np

#for checking if paths exits
import os

#importing training trajectory
from simulation_trajectories import TrainingTrajectory



class FOM_Class(FluidDynamicsAnalysis):

    def __init__(self, model, project_parameters):
        super().__init__(model, project_parameters)
        self.control_point = 538 #a node around the middle of the geometry to capture the bufurcation
        self.velocity_y_at_control_point = []
        self.narrowing_width = []
        self.time_step_solution_container = []
        self.reynolds_number_container = []


    def InitialMeshPosition(self):
        self.training_trajectory = TrainingTrajectory(self.project_parameters["solver_settings"]["fluid_solver_settings"]["time_stepping"]["time_step"].GetDouble())
        self.w = self.training_trajectory.SetUpInitialNarrowing()
        self.MoveAllPartsAccordingToW()

    def ModifyInitialGeometry(self):
        super().ModifyInitialGeometry()
        self.InitialMeshPosition()



    def MovePart(self, part_name, jacobian, centering_vector, extra_centering):
        x_original = []
        y_original = []
        # first loop
        for node in self.model.GetModelPart(f"FluidModelPart.{part_name}").Nodes:
            if not node.IsFixed(KratosMultiphysics.MESH_DISPLACEMENT_X):
                x_original.append(node.X0)
            if not node.IsFixed(KratosMultiphysics.MESH_DISPLACEMENT_Y):
                y_original.append(node.Y0)
        x_original = np.array(x_original).reshape(1,-1)
        y_original = np.array(y_original).reshape(1,-1)
        matrix_of_coordinates = np.r_[x_original, y_original]
        modified_matrix_of_coordinates = np.linalg.inv(jacobian) @ (matrix_of_coordinates - centering_vector)
        modified_matrix_of_coordinates += centering_vector + extra_centering #re-locating
        # second loop
        i = 0
        for node in self.model.GetModelPart(f"FluidModelPart.{part_name}").Nodes:
            if not node.IsFixed(KratosMultiphysics.MESH_DISPLACEMENT_X):
                x_disp = modified_matrix_of_coordinates[0,i] - node.X0
                node.SetSolutionStepValue(KratosMultiphysics.MESH_DISPLACEMENT_X,0, x_disp )
            if not node.IsFixed(KratosMultiphysics.MESH_DISPLACEMENT_Y):
                y_disp = modified_matrix_of_coordinates[1,i] - node.Y0
                node.SetSolutionStepValue(KratosMultiphysics.MESH_DISPLACEMENT_Y,0, y_disp )
                i +=1
            node.Fix(KratosMultiphysics.MESH_DISPLACEMENT_X)
            node.Fix(KratosMultiphysics.MESH_DISPLACEMENT_Y)


    def StoreBifurcationData(self):
        # node =  self.model.GetModelPart("FluidModelPart").GetNode(self.control_point)
        # self.velocity_y_at_control_point.append(node.GetSolutionStepValue(KratosMultiphysics.VELOCITY_Y))
        # self.narrowing_width.append(self.w)
        for node in self.model.GetModelPart("FluidModelPart.GENERIC_Meassure").Nodes:
            pass
        #node =  self.model.GetModelPart("Meassure").GetNode(self.control_point)
        self.velocity_y_at_control_point.append(node.GetSolutionStepValue(KratosMultiphysics.VELOCITY_Y))
        self.narrowing_width.append(self.w)


    def MoveAllPartsAccordingToW(self):
        #############################
        ####    FREE ALL NODES   ####
        #############################
        for node in self.model.GetModelPart("FluidModelPart").Nodes:
            node.Free(KratosMultiphysics.MESH_DISPLACEMENT_X)
            node.Free(KratosMultiphysics.MESH_DISPLACEMENT_Y)

        #############################
        #### FIXING OUTSIDE PART ####
        #############################
        for node in self.model.GetModelPart("FluidModelPart.GENERIC_not_moving").Nodes:
            node.SetSolutionStepValue(KratosMultiphysics.MESH_DISPLACEMENT_X,0, 0)
            node.Fix(KratosMultiphysics.MESH_DISPLACEMENT_X)
            node.SetSolutionStepValue(KratosMultiphysics.MESH_DISPLACEMENT_Y,0, 0)
            node.Fix(KratosMultiphysics.MESH_DISPLACEMENT_Y)

        #############################
        ###  MOVE EACH SUB-PART   ###
        #############################
        self.MovePart('GENERIC_green', np.array([[1,0],[0,1/self.w]]), np.array([[0],[1.5]]), np.array([[0],[0]]))
        self.MovePart('GENERIC_yellow_up', np.array([[1,0],[0, (2/(3-self.w))]]), np.array([[0],[3]]), np.array([[0],[0]]))
        self.MovePart('GENERIC_yellow_down', np.array([[1,0],[0, 2/(3-self.w)]]), np.array([[0],[0]]), np.array([[0],[0]]))
        self.MovePart('GENERIC_blue', np.array([[1,0],[(self.w-1)/2, 1]]), np.array([[0],[0]]), np.array([[0],[(self.w-1)/4]]))
        self.MovePart('GENERIC_grey', np.array([[1,0],[(1-self.w)/2, 1]]), np.array([[0],[0]]), np.array([[0],[- (self.w-1)/4]]))



    def UpdateNarrowing(self):
        self.w = self.training_trajectory.UpdateW(self.w)



    def InitializeSolutionStep(self):
        super().InitializeSolutionStep()

        if self.time>10.0: # start modifying narrowing from 10 seconds onwards   (How long does it take to close????)
            self.UpdateNarrowing()
            self.MoveAllPartsAccordingToW()

        print('The current Reynolds Number is: ', self.GetReynolds())



    def GetReynolds(self):
        #TODO Make values agree with papers. Parameter to modify: dunamic viscosity niu
        velocities = []
        for node in self.model.GetModelPart("FluidModelPart.GENERIC_narrowing_zone").Nodes:
            velocities.append(node.GetSolutionStepValue(KratosMultiphysics.VELOCITY_X, 0))
        vel_np = np.array(velocities)

        vx =  np.max(vel_np) #np.mean(vel_np)
        Re = (vx*self.w) / 0.1 #TODO retrieve dynamic viscosity in a more robust way
        return Re



    def FinalizeSolutionStep(self):
        super().FinalizeSolutionStep()
        self.StoreBifurcationData()
        self.reynolds_number_container.append(self.GetReynolds())

        ArrayOfResults = []
        for node in self._GetSolver().fluid_solver.GetComputingModelPart().Nodes:
            ArrayOfResults.append(node.GetSolutionStepValue(KratosMultiphysics.VELOCITY_X, 0))
            ArrayOfResults.append(node.GetSolutionStepValue(KratosMultiphysics.VELOCITY_Y, 0))
            ArrayOfResults.append(node.GetSolutionStepValue(KratosMultiphysics.PRESSURE, 0))
        self.time_step_solution_container.append(ArrayOfResults)

    def GetBifuracationData(self):
        return np.array(self.velocity_y_at_control_point) ,  np.array(self.narrowing_width)

    def GetReynoldsData(self):
        return np.array(self.reynolds_number_container)

    def GetSnapshotsMatrix(self):
        SnapshotMatrix = np.zeros((len(self.time_step_solution_container[0]), len(self.time_step_solution_container)))
        for i in range(len(self.time_step_solution_container)):
            Snapshot_i= np.array(self.time_step_solution_container[i])
            SnapshotMatrix[:,i] = Snapshot_i.transpose()
        return SnapshotMatrix






















def prepare_files(working_path):
    """pre-pending the absolut path of the files in the Project Parameters"""
    with open(working_path+'/ProblemFiles/ProjectParameters.json','r') as f:
        updated_project_parameters = json.load(f)
        file_input_name = updated_project_parameters["solver_settings"]["fluid_solver_settings"]["model_import_settings"]["input_filename"]
        materials_filename = updated_project_parameters["solver_settings"]["fluid_solver_settings"]["material_import_settings"]["materials_filename"]
        gid_output_name = updated_project_parameters["output_processes"]["gid_output"][0]["Parameters"]["output_name"]

        updated_project_parameters["solver_settings"]["fluid_solver_settings"]["model_import_settings"]["input_filename"] = working_path + '/ProblemFiles/'+ file_input_name
        updated_project_parameters["solver_settings"]["fluid_solver_settings"]["material_import_settings"]["materials_filename"] = working_path +'/ProblemFiles/'+ materials_filename
        updated_project_parameters["output_processes"]["gid_output"][0]["Parameters"]["output_name"] = working_path +'/Results/FOM'
        updated_project_parameters["output_processes"]["vtk_output"] = []

    with open(working_path+'/ProblemFiles/ProjectParameters_modified.json','w') as f:
        json.dump(updated_project_parameters, f, indent = 4)









def convert_to_nd(SnapshotsMatrix, number_of_dimensions=2):
    for i in range(np.shape(SnapshotsMatrix)[1]):
        column_mean = np.mean( SnapshotsMatrix[:,i].reshape(-1,number_of_dimensions).reshape(-1,number_of_dimensions),0).reshape(-1,1)
        if i ==0:
            columns_means = column_mean
        else:
            columns_means = np.c_[columns_means,column_mean]

    return columns_means

















def Train_ROM():

    if not os.path.exists(f'./Results/FOM.post.bin'):

        with open("ProblemFiles/ProjectParameters_modified.json", 'r') as parameter_file:
            parameters = KratosMultiphysics.Parameters(parameter_file.read())
        global_model = KratosMultiphysics.Model()
        simulation = FOM_Class(global_model, parameters)
        simulation.Run()
        SnapshotsMatrix = simulation.GetSnapshotsMatrix()
        velocity_y, narrowing = simulation.GetBifuracationData()
        reynolds = simulation.GetReynoldsData()
        np.save('Results/reynolds.npy', reynolds)
        np.save('Results/narrowing.npy', narrowing)
        np.save('Results/Velocity_y.npy', velocity_y)
        np.save('Results/SnapshotMatrix.npy', SnapshotsMatrix )
























if __name__=="__main__":
    working_path =os.getcwd()

    prepare_files(working_path)

    Train_ROM()