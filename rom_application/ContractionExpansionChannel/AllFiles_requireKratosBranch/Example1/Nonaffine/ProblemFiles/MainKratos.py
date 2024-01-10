import KratosMultiphysics
from KratosMultiphysics.FluidDynamicsApplication.fluid_dynamics_analysis import FluidDynamicsAnalysis
from KratosMultiphysics.RomApplication.fluid_dynamics_analysis_rom import FluidDynamicsAnalysisROM

import KratosMultiphysics.RomApplication as romapp
import json

from KratosMultiphysics.RomApplication.empirical_cubature_method import EmpiricalCubatureMethod
from KratosMultiphysics.RomApplication.randomized_singular_value_decomposition import RandomizedSingularValueDecomposition

import numpy as np
from matplotlib import pyplot as plt


#importing PyGeM tools
from pygem import FFD, RBF

#Function from PyGeM tutorial
def scatter3d(arr, figsize=(8,8), s=10, draw=True, ax=None, alpha=1, labels=None, title=None):
    if ax is None:
        fig = plt.figure(figsize=figsize)
        ax = fig.add_subplot(projection='3d')

    for idx,a in enumerate(arr):
        if labels is not None:
            ax.scatter(*a.T, s=s, alpha=alpha, label=labels[idx])
        else:
            ax.scatter(*a.T, s=s, alpha=alpha)

    if draw:
        if labels is not None:
            plt.legend()
        if title is not None:
            plt.title(title)
        plt.show()
    else:
        return ax


class FOM_Class(FluidDynamicsAnalysis):


    def __init__(self, model, project_parameters):
        super().__init__(model, project_parameters)
        self.w = 1 # original narrowing size
        time_step_size = self.project_parameters["solver_settings"]["fluid_solver_settings"]["time_stepping"]["time_step"].GetDouble()
        self.control_point = 363 #a node around the middle of the geometry to capture the bufurcation
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
        self.narrowing_width.append(self.deformation_multiplier)



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
                print(node.Y0)
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
                print(node.Y0)
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




    def InitializeSolutionStep(self):
        super().InitializeSolutionStep()

        #free all nodes
        for node in self.model.GetModelPart("FluidModelPart").Nodes:
            node.Free(KratosMultiphysics.MESH_DISPLACEMENT_X)
            node.Free(KratosMultiphysics.MESH_DISPLACEMENT_Y)

        if self.time>1.0 and self.time<16.0: # start modifying narrowing from 1 second onwards
            self.deformation_multiplier+=.1
        elif self.time>21.0 and self.time<36:
            self.deformation_multiplier-=.1

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
        return self.velocity_y_at_control_point ,  self.narrowing_width



    def GetSnapshotsMatrix(self):
        SnapshotMatrix = np.zeros((len(self.time_step_solution_container[0]), len(self.time_step_solution_container)))
        for i in range(len(self.time_step_solution_container)):
            Snapshot_i= np.array(self.time_step_solution_container[i])
            SnapshotMatrix[:,i] = Snapshot_i.transpose()
        return SnapshotMatrix








def Train_ROM():
    with open("ProjectParameters.json", 'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())

    global_model = KratosMultiphysics.Model()
    simulation = FOM_Class(global_model, parameters)
    simulation.Run()
    return simulation.GetBifuracationData()







if __name__ == "__main__":
    #Train_ROM()
    vy, w = Train_ROM()

    plt.plot(vy, w, 'k-', label = 'FOM', linewidth = 3)
    plt.legend()
    plt.xlabel('velocity y', size=20)
    plt.ylabel('narrowing w',size=20)
    plt.show()
