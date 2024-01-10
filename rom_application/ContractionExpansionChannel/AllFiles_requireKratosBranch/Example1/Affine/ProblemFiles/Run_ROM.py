import KratosMultiphysics
from KratosMultiphysics.RomApplication.fluid_dynamics_analysis_rom import FluidDynamicsAnalysisROM


import KratosMultiphysics.RomApplication as romapp
import json

from KratosMultiphysics.RomApplication.randomized_singular_value_decomposition import RandomizedSingularValueDecomposition

import numpy as np




import os.path



#importing training trajectory
from simulation_trajectories import TrainingTrajectory







class ROM_Class(FluidDynamicsAnalysisROM):

    def __init__(self, model, project_parameters, correct_cluster = None, hard_impose_correct_cluster = False, bases=None, hrom=None):
        super().__init__(model, project_parameters, hrom)
        self.bases = bases
        self.w = 1 # original narrowing size
        time_step_size = self.project_parameters["solver_settings"]["fluid_solver_settings"]["time_stepping"]["time_step"].GetDouble()
        self.delta_w = 0.025 * time_step_size # this ensures to obtain a maximum narrowing size of 2.9 and a minimum of 0.1
        self.maximum = 2.9
        self.minimum = 0.1
        self.control_point = None
        self.velocity_y_at_control_point = []
        self.narrowing_width = []
        self.tttime = 0 #fake time step, useful to impose the correct cluster
        self.time_step_solution_container = []


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


    def StoreBifurcationData(self):
        for node in self.model.GetModelPart("FluidModelPart.GENERIC_Meassure").Nodes:
            pass
        #node =  self.model.GetModelPart("Meassure").GetNode(self.control_point)
        self.velocity_y_at_control_point.append(node.GetSolutionStepValue(KratosMultiphysics.VELOCITY_Y))
        self.narrowing_width.append(self.w)


    def UpdateNarrowing(self):
        self.w = self.training_trajectory.UpdateW(self.w)



    def InitializeSolutionStep(self):
        super().InitializeSolutionStep()

        if self.time>10.0: # start modifying narrowing from 10 seconds onwards   (How long does it take to close????)
            self.UpdateNarrowing()
            self.MoveAllPartsAccordingToW()

    def FinalizeSolutionStep(self):
        super().FinalizeSolutionStep()
        self.StoreBifurcationData()
        self.tttime += 1

        ArrayOfResults = []
        for node in self._GetSolver().fluid_solver.GetComputingModelPart().Nodes:
            ArrayOfResults.append(node.GetSolutionStepValue(KratosMultiphysics.VELOCITY_X, 0))
            ArrayOfResults.append(node.GetSolutionStepValue(KratosMultiphysics.VELOCITY_Y, 0))
            ArrayOfResults.append(node.GetSolutionStepValue(KratosMultiphysics.PRESSURE, 0))
        self.time_step_solution_container.append(ArrayOfResults)


    def GetBifuracationData(self):
        return self.velocity_y_at_control_point ,  self.narrowing_width


    def GetSnapshotsMatrix(self):
        SnapshotMatrix = np.zeros((len(self.time_step_solution_container[0]), len(self.time_step_solution_container)))
        for i in range(len(self.time_step_solution_container)):
            Snapshot_i= np.array(self.time_step_solution_container[i])
            SnapshotMatrix[:,i] = Snapshot_i.transpose()
        return SnapshotMatrix







def prepare_files(working_path,svd_truncation_tolerance):
    """pre-pending the absolut path of the files in the Project Parameters"""
    with open(working_path+'/ProblemFiles/ProjectParameters.json','r') as f:
        updated_project_parameters = json.load(f)
        file_input_name = updated_project_parameters["solver_settings"]["fluid_solver_settings"]["model_import_settings"]["input_filename"]
        materials_filename = updated_project_parameters["solver_settings"]["fluid_solver_settings"]["material_import_settings"]["materials_filename"]
        gid_output_name = updated_project_parameters["output_processes"]["gid_output"][0]["Parameters"]["output_name"]

        updated_project_parameters["solver_settings"]["fluid_solver_settings"]["model_import_settings"]["input_filename"] = working_path + '/ProblemFiles/'+ file_input_name
        updated_project_parameters["solver_settings"]["fluid_solver_settings"]["material_import_settings"]["materials_filename"] = working_path +'/ProblemFiles/'+ materials_filename
        updated_project_parameters["output_processes"]["gid_output"][0]["Parameters"]["output_name"] = working_path +f'/Results/ROM_{svd_truncation_tolerance}'
        updated_project_parameters["output_processes"]["vtk_output"] = []

    with open(working_path+'/ProblemFiles/ProjectParameters_modified.json','w') as f:
        json.dump(updated_project_parameters, f, indent = 4)












def ROM(hard_impose_currect_cluster = False, Number_Of_Clusters=1, svd_truncation_tolerance=1e-4):

    if not os.path.exists(f'./Results/ROM_{svd_truncation_tolerance}.post.bin'):
        if not os.path.exists(f'./ROM/'):
            os.mkdir('./ROM')
        basis = f'./ROM/Phi_{svd_truncation_tolerance}.npy'
        if os.path.exists(basis):
            u = np.load(basis)
        else:
            u,s,_,_ = RandomizedSingularValueDecomposition().Calculate(np.load(f'./Results/SnapshotMatrix.npy'), svd_truncation_tolerance)
            np.save(basis,u)

        ### Saving the nodal basis ###  (Need to make this more robust, hard coded here)
        basis_POD={"rom_settings":{},"nodal_modes":{}}
        basis_POD["rom_settings"]["nodal_unknowns"] = ["VELOCITY_X","VELOCITY_Y","PRESSURE"]
        basis_POD["rom_settings"]["number_of_rom_dofs"] = np.shape(u)[1]
        Dimensions = len(basis_POD["rom_settings"]["nodal_unknowns"])
        N_nodes=np.shape(u)[0]/Dimensions
        N_nodes = int(N_nodes)
        node_Id=np.linspace(1,N_nodes,N_nodes)
        i = 0
        for j in range (0,N_nodes):
            basis_POD["nodal_modes"][int(node_Id[j])] = (u[i:i+Dimensions].tolist())
            i=i+Dimensions

        with open('ProblemFiles/RomParameters.json', 'w') as f:
            json.dump(basis_POD,f, indent=2)

        print('\n\nNodal basis printed in json format\n\n')

        with open("ProblemFiles/ProjectParameters_modified.json", 'r') as parameter_file:
            parameters = KratosMultiphysics.Parameters(parameter_file.read())
        global_model = KratosMultiphysics.Model()
        correct_clusters = None

        #loading the bases
        bases = []
        bases = None
        simulation = ROM_Class(global_model, parameters, correct_clusters, hard_impose_currect_cluster, bases)
        simulation.Run()
        np.save(f'./Results/ROM_snapshots_{svd_truncation_tolerance}.npy',simulation.GetSnapshotsMatrix())

        vy_rom, w_rom = simulation.GetBifuracationData()

        np.save(f'./Results/y_velocity_ROM_{svd_truncation_tolerance}.npy', vy_rom)
        np.save(f'./Results/narrowing_ROM_{svd_truncation_tolerance}.npy', w_rom)

















if __name__=="__main__":

    #library for passing arguments to the script from bash
    from sys import argv

    Launch_Simulation = bool(int(argv[1]))
    Number_Of_Clusters= 1
    svd_truncation_tolerance= float(argv[3])
    clustering= argv[4]
    overlapping = int(argv[5])
    working_path = argv[6]


    prepare_files(working_path,svd_truncation_tolerance)


    ROM(hard_impose_currect_cluster = True, Number_Of_Clusters=Number_Of_Clusters, svd_truncation_tolerance=svd_truncation_tolerance)




