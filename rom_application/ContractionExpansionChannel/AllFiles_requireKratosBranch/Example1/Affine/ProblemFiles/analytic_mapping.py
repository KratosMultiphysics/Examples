import KratosMultiphysics
import numpy as np

#Not working



def MovePart(simulation, part_name, jacobian, centering_vector, extra_centering):
    x_original = []
    y_original = []
    # first loop
    for node in simulation.model.GetModelPart(f"FluidModelPart.{part_name}").Nodes:
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
    for node in simulation.model.GetModelPart(f"FluidModelPart.{part_name}").Nodes:
        if not node.IsFixed(KratosMultiphysics.MESH_DISPLACEMENT_X):
            x_disp = modified_matrix_of_coordinates[0,i] - node.X0
            node.SetSolutionStepValue(KratosMultiphysics.MESH_DISPLACEMENT_X,0, x_disp )
        if not node.IsFixed(KratosMultiphysics.MESH_DISPLACEMENT_Y):
            y_disp = modified_matrix_of_coordinates[1,i] - node.Y0
            node.SetSolutionStepValue(KratosMultiphysics.MESH_DISPLACEMENT_Y,0, y_disp )
            i +=1
        node.Fix(KratosMultiphysics.MESH_DISPLACEMENT_X)
        node.Fix(KratosMultiphysics.MESH_DISPLACEMENT_Y)



def phi(simulation):
    #############################
    ####    FREE ALL NODES   ####
    #############################
    for node in simulation.model.GetModelPart("FluidModelPart").Nodes:
        node.Free(KratosMultiphysics.MESH_DISPLACEMENT_X)
        node.Free(KratosMultiphysics.MESH_DISPLACEMENT_Y)

    #############################
    #### FIXING OUTSIDE PART ####
    #############################
    for node in simulation.model.GetModelPart("FluidModelPart.GENERIC_not_moving").Nodes:
        node.SetSolutionStepValue(KratosMultiphysics.MESH_DISPLACEMENT_X,0, 0)
        node.Fix(KratosMultiphysics.MESH_DISPLACEMENT_X)
        node.SetSolutionStepValue(KratosMultiphysics.MESH_DISPLACEMENT_Y,0, 0)
        node.Fix(KratosMultiphysics.MESH_DISPLACEMENT_Y)

    #############################
    ###  MOVE EACH SUB-PART   ###
    #############################
    simulation.MovePart('GENERIC_green', np.array([[1,0],[0,1/simulation.w]]), np.array([[0],[1.5]]), np.array([[0],[0]]))
    simulation.MovePart('GENERIC_yellow_up', np.array([[1,0],[0, (2/(3-simulation.w))]]), np.array([[0],[3]]), np.array([[0],[0]]))
    simulation.MovePart('GENERIC_yellow_down', np.array([[1,0],[0, 2/(3-simulation.w)]]), np.array([[0],[0]]), np.array([[0],[0]]))
    simulation.MovePart('GENERIC_blue', np.array([[1,0],[(simulation.w-1)/2, 1]]), np.array([[0],[0]]), np.array([[0],[(simulation.w-1)/4]]))
    simulation.MovePart('GENERIC_grey', np.array([[1,0],[(1-simulation.w)/2, 1]]), np.array([[0],[0]]), np.array([[0],[- (simulation.w-1)/4]]))




