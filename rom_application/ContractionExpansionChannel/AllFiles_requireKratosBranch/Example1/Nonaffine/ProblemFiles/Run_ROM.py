import KratosMultiphysics
from KratosMultiphysics.RomApplication.fluid_dynamics_analysis_rom import FluidDynamicsAnalysisROM

import os.path


import KratosMultiphysics.RomApplication as romapp
import json

from KratosMultiphysics.RomApplication.randomized_singular_value_decomposition import RandomizedSingularValueDecomposition

import numpy as np


#importing PyGeM tools
from pygem import FFD, RBF







class ROM_Class(FluidDynamicsAnalysisROM):

    def __init__(self, model, project_parameters, correct_cluster = None, hard_impose_correct_cluster = False, bases=None, hrom=None):
        super().__init__(model, project_parameters, hrom)
        time_step_size = self.project_parameters["solver_settings"]["fluid_solver_settings"]["time_stepping"]["time_step"].GetDouble()
        self.delta_deformation = time_step_size # this ensures to obtain the same deformation independently of the time step used
        self.control_point = 854 #a node around the middle of the geometry to capture the bufurcation
        self.maximum = 11
        self.minimum = 0
        ###  ###  ###
        self.node_up = 412      #nodes to obtain the narrowing width
        self.node_down = 673
        ###  ###  ###
        self.deformation_multiplier_list = []
        self.time_step_solution_container = []
        self.velocity_y_at_control_point = []
        self.narrowing_width = []
        self.matrix_of_free_coordinates = None
        self.deformation_multiplier = 0


    def MoveInnerNodesWithRBF(self):
        # first loop, ONLY ENTERED ONCE
        if self.matrix_of_free_coordinates is None:
            x_original = []
            y_original = []
            for node in self.model.GetModelPart("FluidModelPart").Nodes:
                if not node.IsFixed(KratosMultiphysics.MESH_DISPLACEMENT_X):
                    x_original.append(node.X0)
                if not node.IsFixed(KratosMultiphysics.MESH_DISPLACEMENT_Y):
                    y_original.append(node.Y0)
            x_original = np.array(x_original).reshape(-1,1)
            y_original = np.array(y_original).reshape(-1,1)
            self.matrix_of_free_coordinates = np.c_[x_original, y_original, np.ones((y_original.shape[0],1))]
        self.matrix_of_modified_coordinates = self.rbf(self.matrix_of_free_coordinates)

        # second loop
        i = 0
        for node in self.model.GetModelPart("FluidModelPart").Nodes:
            if not node.IsFixed(KratosMultiphysics.MESH_DISPLACEMENT_X):
                x_disp = self.matrix_of_modified_coordinates[i,0] - node.X0
                node.SetSolutionStepValue(KratosMultiphysics.MESH_DISPLACEMENT_X,0, x_disp )
            if not node.IsFixed(KratosMultiphysics.MESH_DISPLACEMENT_Y):
                y_disp = self.matrix_of_modified_coordinates[i,1] - node.Y0
                node.SetSolutionStepValue(KratosMultiphysics.MESH_DISPLACEMENT_Y,0, y_disp )
                i +=1
            node.Fix(KratosMultiphysics.MESH_DISPLACEMENT_X)
            node.Fix(KratosMultiphysics.MESH_DISPLACEMENT_Y)


    def StoreBifurcationData(self):
        node =  self.model.GetModelPart("FluidModelPart").GetNode(self.control_point)
        self.velocity_y_at_control_point.append(node.GetSolutionStepValue(KratosMultiphysics.VELOCITY_Y))
        self.deformation_multiplier_list.append(self.deformation_multiplier)
        node_up = self.model.GetModelPart("FluidModelPart").GetNode(self.node_up)
        node_down = self.model.GetModelPart("FluidModelPart").GetNode(self.node_down)
        self.narrowing_width.append(node_up.Y - node_down.Y)




    def ModifyInitialGeometry(self):
        super().ModifyInitialGeometry()
        self.IdentifyNodes()
        self.SetUpFreeFormDeformation()



    def IdentifyNodes(self):
        control_down = self.model.GetModelPart("FluidModelPart.GENERIC_ControlDown")
        control_up = self.model.GetModelPart("FluidModelPart.GENERIC_ControlUp")
        fixed_walls= self.model.GetModelPart("FluidModelPart.GENERIC_FixedWalls")

        number_of_nodes_walls = fixed_walls.NumberOfNodes()
        number_of_nodes_down = control_down.NumberOfNodes()
        number_of_nodes_up = control_down.NumberOfNodes()

        #get matrix of original coordinates
        walls_coordinates = np.ones((int(number_of_nodes_walls),3))
        up_coordinates = np.ones((int(number_of_nodes_up),3))
        down_coordinates = np.ones((int(number_of_nodes_down),3))

        counter = 0
        for node in control_down.Nodes:
            down_coordinates[counter, 0] = node.X0
            down_coordinates[counter, 1] = node.Y0
            counter+=1

        counter = 0
        for node in control_up.Nodes:
            up_coordinates[counter, 0] = node.X0
            up_coordinates[counter, 1] = node.Y0
            counter+=1

        counter = 0
        for node in fixed_walls.Nodes:
            walls_coordinates[counter, 0] = node.X0
            walls_coordinates[counter, 1] = node.Y0
            counter+=1

        self.walls = walls_coordinates

        self.up = up_coordinates
        at_3_y = np.where(self.up[:,1] == 3)
        self.up = np.delete(self.up,at_3_y, 0)

        self.down = down_coordinates
        at_0_y = np.where(self.down[:,1] == 0)
        self.down = np.delete(self.down,at_0_y, 0)

        self.fixed_coordinates = np.r_[walls_coordinates, self.down, self.up]




    def SetUpFreeFormDeformation(self):
        #creating a free form deformation object for each control domain
        self.ffd_up = FFD([2,5,2])  #3D box of control points
        self.ffd_down = FFD([2,5,2])  #3D box of control points

        #setting the centre and size of the upper box of control points
        self.ffd_down.box_origin = np.array([1.25, 0, 0.5])
        self.ffd_down.box_length = np.array([1, 1.25, 1])

        #setting the centre and size of the lower box of control points
        self.ffd_up.box_origin = np.array([1.25, 1.75, 0.5])
        self.ffd_up.box_length = np.array([1, 1.25, 1])

        self.list_of_ffds = [self.ffd_up, self.ffd_down]




    def MoveControlPoints(self, scale_of_deformation=1):

        self.ffd_down.array_mu_x[0, 0, 0] = self.deformation_multiplier*scale_of_deformation * 0.0
        self.ffd_down.array_mu_x[0, 1, 0] = self.deformation_multiplier*scale_of_deformation * 0.04
        self.ffd_down.array_mu_x[0, 2, 0] = self.deformation_multiplier*scale_of_deformation * 0.06
        self.ffd_down.array_mu_x[0, 3, 0] = self.deformation_multiplier*scale_of_deformation * 0.04
        self.ffd_down.array_mu_x[0, 4, 0] = self.deformation_multiplier*scale_of_deformation * 0.0
        self.ffd_down.array_mu_x[0, 0, 1] = self.deformation_multiplier*scale_of_deformation * 0.0
        self.ffd_down.array_mu_x[0, 1, 1] = self.deformation_multiplier*scale_of_deformation * 0.04
        self.ffd_down.array_mu_x[0, 2, 1] = self.deformation_multiplier*scale_of_deformation * 0.06
        self.ffd_down.array_mu_x[0, 3, 1] = self.deformation_multiplier*scale_of_deformation * 0.04
        self.ffd_down.array_mu_x[0, 4, 1] = self.deformation_multiplier*scale_of_deformation * 0.0

        self.ffd_down.array_mu_y[0, 0, 0] = self.deformation_multiplier*scale_of_deformation * 0.0
        self.ffd_down.array_mu_y[0, 1, 0] = self.deformation_multiplier*scale_of_deformation * 0.01
        self.ffd_down.array_mu_y[0, 2, 0] = self.deformation_multiplier*scale_of_deformation * 0.015
        self.ffd_down.array_mu_y[0, 3, 0] = self.deformation_multiplier*scale_of_deformation * 0.02
        self.ffd_down.array_mu_y[0, 4, 0] = self.deformation_multiplier*scale_of_deformation * 0.025
        self.ffd_down.array_mu_y[0, 0, 1] = self.deformation_multiplier*scale_of_deformation * 0.00
        self.ffd_down.array_mu_y[0, 1, 1] = self.deformation_multiplier*scale_of_deformation * 0.01
        self.ffd_down.array_mu_y[0, 2, 1] = self.deformation_multiplier*scale_of_deformation * 0.015
        self.ffd_down.array_mu_y[0, 3, 1] = self.deformation_multiplier*scale_of_deformation * 0.02
        self.ffd_down.array_mu_y[0, 4, 1] = self.deformation_multiplier*scale_of_deformation * 0.025


        self.ffd_down.array_mu_x[1, 0, 0] = self.deformation_multiplier*scale_of_deformation * 0.0
        self.ffd_down.array_mu_x[1, 1, 0] = self.deformation_multiplier*scale_of_deformation * 0.04
        self.ffd_down.array_mu_x[1, 2, 0] = self.deformation_multiplier*scale_of_deformation * 0.06
        self.ffd_down.array_mu_x[1, 3, 0] = self.deformation_multiplier*scale_of_deformation * 0.04
        self.ffd_down.array_mu_x[1, 4, 0] = self.deformation_multiplier*scale_of_deformation * 0.0
        self.ffd_down.array_mu_x[1, 0, 1] = self.deformation_multiplier*scale_of_deformation * 0.0
        self.ffd_down.array_mu_x[1, 1, 1] = self.deformation_multiplier*scale_of_deformation * 0.04
        self.ffd_down.array_mu_x[1, 2, 1] = self.deformation_multiplier*scale_of_deformation * 0.06
        self.ffd_down.array_mu_x[1, 3, 1] = self.deformation_multiplier*scale_of_deformation * 0.04
        self.ffd_down.array_mu_x[1, 4, 1] = self.deformation_multiplier*scale_of_deformation * 0.0

        self.ffd_down.array_mu_y[1, 0, 0] = self.deformation_multiplier*scale_of_deformation * 0.0
        self.ffd_down.array_mu_y[1, 1, 0] = self.deformation_multiplier*scale_of_deformation * 0.01
        self.ffd_down.array_mu_y[1, 2, 0] = self.deformation_multiplier*scale_of_deformation * 0.015
        self.ffd_down.array_mu_y[1, 3, 0] = self.deformation_multiplier*scale_of_deformation * 0.02
        self.ffd_down.array_mu_y[1, 4, 0] = self.deformation_multiplier*scale_of_deformation * 0.025
        self.ffd_down.array_mu_y[1, 0, 1] = self.deformation_multiplier*scale_of_deformation * 0.00
        self.ffd_down.array_mu_y[1, 1, 1] = self.deformation_multiplier*scale_of_deformation * 0.01
        self.ffd_down.array_mu_y[1, 2, 1] = self.deformation_multiplier*scale_of_deformation * 0.015
        self.ffd_down.array_mu_y[1, 3, 1] = self.deformation_multiplier*scale_of_deformation * 0.02
        self.ffd_down.array_mu_y[1, 4, 1] = self.deformation_multiplier*scale_of_deformation * 0.025

        self.ffd_up.array_mu_x[0, 0, 0] = self.deformation_multiplier*scale_of_deformation * 0.0
        self.ffd_up.array_mu_x[0, 1, 0] = self.deformation_multiplier*scale_of_deformation * 0.04
        self.ffd_up.array_mu_x[0, 2, 0] = self.deformation_multiplier*scale_of_deformation * 0.06
        self.ffd_up.array_mu_x[0, 3, 0] = self.deformation_multiplier*scale_of_deformation * 0.04
        self.ffd_up.array_mu_x[0, 4, 0] = self.deformation_multiplier*scale_of_deformation * 0.0
        self.ffd_up.array_mu_x[0, 0, 1] = self.deformation_multiplier*scale_of_deformation * 0.0
        self.ffd_up.array_mu_x[0, 1, 1] = self.deformation_multiplier*scale_of_deformation * 0.04
        self.ffd_up.array_mu_x[0, 2, 1] = self.deformation_multiplier*scale_of_deformation * 0.06
        self.ffd_up.array_mu_x[0, 3, 1] = self.deformation_multiplier*scale_of_deformation * 0.04
        self.ffd_up.array_mu_x[0, 4, 1] = self.deformation_multiplier*scale_of_deformation * 0.0

        self.ffd_up.array_mu_y[0, 0, 0] = -self.deformation_multiplier*scale_of_deformation * 0.025
        self.ffd_up.array_mu_y[0, 1, 0] = -self.deformation_multiplier*scale_of_deformation * 0.020
        self.ffd_up.array_mu_y[0, 2, 0] = -self.deformation_multiplier*scale_of_deformation * 0.015
        self.ffd_up.array_mu_y[0, 3, 0] = -self.deformation_multiplier*scale_of_deformation * 0.01
        self.ffd_up.array_mu_y[0, 4, 0] = -self.deformation_multiplier*scale_of_deformation * 0.00
        self.ffd_up.array_mu_y[0, 0, 1] = -self.deformation_multiplier*scale_of_deformation * 0.025
        self.ffd_up.array_mu_y[0, 1, 1] = -self.deformation_multiplier*scale_of_deformation * 0.020
        self.ffd_up.array_mu_y[0, 2, 1] = -self.deformation_multiplier*scale_of_deformation * 0.015
        self.ffd_up.array_mu_y[0, 3, 1] = -self.deformation_multiplier*scale_of_deformation * 0.01
        self.ffd_up.array_mu_y[0, 4, 1] = -self.deformation_multiplier*scale_of_deformation * 0.00


        self.ffd_up.array_mu_x[1, 0, 0] = self.deformation_multiplier*scale_of_deformation * 0.0
        self.ffd_up.array_mu_x[1, 1, 0] = self.deformation_multiplier*scale_of_deformation * 0.04
        self.ffd_up.array_mu_x[1, 2, 0] = self.deformation_multiplier*scale_of_deformation * 0.06
        self.ffd_up.array_mu_x[1, 3, 0] = self.deformation_multiplier*scale_of_deformation * 0.04
        self.ffd_up.array_mu_x[1, 4, 0] = self.deformation_multiplier*scale_of_deformation * 0.0
        self.ffd_up.array_mu_x[1, 0, 1] = self.deformation_multiplier*scale_of_deformation * 0.0
        self.ffd_up.array_mu_x[1, 1, 1] = self.deformation_multiplier*scale_of_deformation * 0.04
        self.ffd_up.array_mu_x[1, 2, 1] = self.deformation_multiplier*scale_of_deformation * 0.06
        self.ffd_up.array_mu_x[1, 3, 1] = self.deformation_multiplier*scale_of_deformation * 0.04
        self.ffd_up.array_mu_x[1, 4, 1] = self.deformation_multiplier*scale_of_deformation * 0.0

        self.ffd_up.array_mu_y[1, 0, 0] = -self.deformation_multiplier*scale_of_deformation * 0.025
        self.ffd_up.array_mu_y[1, 1, 0] = -self.deformation_multiplier*scale_of_deformation * 0.020
        self.ffd_up.array_mu_y[1, 2, 0] = -self.deformation_multiplier*scale_of_deformation * 0.015
        self.ffd_up.array_mu_y[1, 3, 0] = -self.deformation_multiplier*scale_of_deformation * 0.01
        self.ffd_up.array_mu_y[1, 4, 0] = -self.deformation_multiplier*scale_of_deformation * 0.00
        self.ffd_up.array_mu_y[1, 0, 1] = -self.deformation_multiplier*scale_of_deformation * 0.025
        self.ffd_up.array_mu_y[1, 1, 1] = -self.deformation_multiplier*scale_of_deformation * 0.020
        self.ffd_up.array_mu_y[1, 2, 1] = -self.deformation_multiplier*scale_of_deformation * 0.015
        self.ffd_up.array_mu_y[1, 3, 1] = -self.deformation_multiplier*scale_of_deformation * 0.01
        self.ffd_up.array_mu_y[1, 4, 1] = -self.deformation_multiplier*scale_of_deformation * 0.00

        moved_up = self.ffd_up(self.up)
        moved_down = self.ffd_down(self.down)


        #Moving lower part
        control_down = self.model.GetModelPart("FluidModelPart.GENERIC_ControlDown")
        i=0
        for node in control_down.Nodes:
            if node.Y0 != 0:
                x_disp = moved_down[i,0] - node.X0
                y_disp = moved_down[i,1] - node.Y0
                node.SetSolutionStepValue(KratosMultiphysics.MESH_DISPLACEMENT_X,0, x_disp )
                node.SetSolutionStepValue(KratosMultiphysics.MESH_DISPLACEMENT_Y,0, y_disp )
                i +=1
            node.Fix(KratosMultiphysics.MESH_DISPLACEMENT_X)
            node.Fix(KratosMultiphysics.MESH_DISPLACEMENT_Y)


        #moving upper part
        control_up = self.model.GetModelPart("FluidModelPart.GENERIC_ControlUp")
        i=0
        for node in control_up.Nodes:
            if node.Y0 != 3:
                x_disp = moved_up[i,0] - node.X0
                y_disp = moved_up[i,1] - node.Y0
                node.SetSolutionStepValue(KratosMultiphysics.MESH_DISPLACEMENT_X,0, x_disp )
                node.SetSolutionStepValue(KratosMultiphysics.MESH_DISPLACEMENT_Y,0, y_disp )
                i +=1
            node.Fix(KratosMultiphysics.MESH_DISPLACEMENT_X)
            node.Fix(KratosMultiphysics.MESH_DISPLACEMENT_Y)

        self.moved_coordinates =  np.r_[self.walls, moved_down, moved_up]



    def UpdateRBF(self):
        self.rbf = RBF(original_control_points = self.fixed_coordinates, deformed_control_points =
            self.moved_coordinates, radius=0.75)


    def LockOuterWalls(self):
        for node in self.model.GetModelPart("FluidModelPart.GENERIC_FixedWalls").Nodes:
            node.SetSolutionStepValue(KratosMultiphysics.MESH_DISPLACEMENT_X,0, 0 )
            node.SetSolutionStepValue(KratosMultiphysics.MESH_DISPLACEMENT_Y,0, 0)
            node.Fix(KratosMultiphysics.MESH_DISPLACEMENT_X)
            node.Fix(KratosMultiphysics.MESH_DISPLACEMENT_Y)




    def UpdateDeformationMultiplier(self):
        ####Train trajectory####
        if self.time>10.0 and self.time<=21.0: # start modifying narrowing from 10 seconds onwards
            self.deformation_multiplier+=self.delta_deformation
            if self.deformation_multiplier > self.maximum:
                self.deformation_multiplier = self.maximum
        elif self.time>31.0 and self.time<41.9: # start modifying narrowing from 10 seconds onwards
            self.deformation_multiplier-=self.delta_deformation
            if self.deformation_multiplier < self.minimum:
                self.deformation_multiplier = self.minimum



    def InitializeSolutionStep(self):
        super().InitializeSolutionStep()
        #free all nodes
        for node in self.model.GetModelPart("FluidModelPart").Nodes:
            node.Free(KratosMultiphysics.MESH_DISPLACEMENT_X)
            node.Free(KratosMultiphysics.MESH_DISPLACEMENT_Y)

        self.UpdateDeformationMultiplier()
        self.MoveControlPoints()
        self.LockOuterWalls()






    def FinalizeSolutionStep(self):
        super().FinalizeSolutionStep()
        self.StoreBifurcationData()

        ArrayOfResults = []
        for node in self._GetSolver().fluid_solver.GetComputingModelPart().Nodes:
            ArrayOfResults.append(node.GetSolutionStepValue(KratosMultiphysics.VELOCITY_X, 0))
            ArrayOfResults.append(node.GetSolutionStepValue(KratosMultiphysics.VELOCITY_Y, 0))
            ArrayOfResults.append(node.GetSolutionStepValue(KratosMultiphysics.PRESSURE, 0))
        self.time_step_solution_container.append(ArrayOfResults)




    def GetBifuracationData(self):
        return self.velocity_y_at_control_point ,  self.narrowing_width, self.deformation_multiplier_list




    def GetSnapshotsMatrix(self):
        SnapshotMatrix = np.zeros((len(self.time_step_solution_container[0]), len(self.time_step_solution_container)))
        for i in range(len(self.time_step_solution_container)):
            Snapshot_i= np.array(self.time_step_solution_container[i])
            SnapshotMatrix[:,i] = Snapshot_i.transpose()
        return SnapshotMatrix








def prepare_files(working_path, svd_truncation_tolerance):
    """pre-pending the absolut path of the files in the Project Parameters"""
    with open(working_path+'/ProblemFiles/ProjectParameters.json','r') as f:
        updated_project_parameters = json.load(f)
        file_input_name = updated_project_parameters["solver_settings"]["fluid_solver_settings"]["model_import_settings"]["input_filename"]
        materials_filename = updated_project_parameters["solver_settings"]["fluid_solver_settings"]["material_import_settings"]["materials_filename"]
        gid_output_name = updated_project_parameters["output_processes"]["gid_output"][0]["Parameters"]["output_name"]

        updated_project_parameters["solver_settings"]["fluid_solver_settings"]["model_import_settings"]["input_filename"] = working_path + '/ProblemFiles/'+ file_input_name
        updated_project_parameters["solver_settings"]["fluid_solver_settings"]["material_import_settings"]["materials_filename"] = working_path +'/ProblemFiles/'+ materials_filename
        updated_project_parameters["output_processes"]["gid_output"][0]["Parameters"]["output_name"] = working_path +f'/Results/ROM_{svd_truncation_tolerance}'

    with open(working_path+'/ProblemFiles/ProjectParameters_modified.json','w') as f:
        json.dump(updated_project_parameters, f, indent = 4)












def ROM(svd_truncation_tolerance):

    if not os.path.exists(f'./Results/ROM_{svd_truncation_tolerance}.post.bin'):

        basis = f'ROM/{svd_truncation_tolerance}.npy'

        if os.path.exists(basis):
            u = np.load(basis)
        else:
            if not os.path.exists(f'./ROM/'):
                os.mkdir(f'./ROM/')
            u,s,_,_ = RandomizedSingularValueDecomposition().Calculate(np.load(f'Results/SnapshotMatrix.npy'), svd_truncation_tolerance)
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
        simulation = ROM_Class(global_model, parameters)
        simulation.Run()

        np.save(f'Results/ROM_snapshots_{svd_truncation_tolerance}.npy',simulation.GetSnapshotsMatrix())

        vy_rom,w_rom,deformation_multiplier =  simulation.GetBifuracationData()

        np.save(f'Results/y_velocity_ROM_{svd_truncation_tolerance}.npy', vy_rom)
        np.save(f'Results/narrowing_ROM_{svd_truncation_tolerance}.npy', w_rom)
        np.save(f'Results/deformation_multiplier_{svd_truncation_tolerance}.npy', deformation_multiplier)











if __name__=="__main__":

    #library for passing arguments to the script from bash
    from sys import argv

    Launch_Simulation = bool(int(argv[1]))
    Number_Of_Clusters= 1
    svd_truncation_tolerance= float(argv[3])
    clustering= argv[4]
    overlapping = int(argv[5])
    working_path = argv[6]

    prepare_files(working_path, svd_truncation_tolerance)

    ROM(svd_truncation_tolerance)


