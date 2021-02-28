import KratosMultiphysics
import KratosMultiphysics.StructuralMechanicsApplication as StructuralMechanics
from KratosMultiphysics.StructuralMechanicsApplication.structural_mechanics_analysis import StructuralMechanicsAnalysis

#ROM imports
from KratosMultiphysics.RomApplication.structural_mechanics_analysis_rom import StructuralMechanicsAnalysisROM
import KratosMultiphysics.RomApplication as romapp
from KratosMultiphysics.RomApplication.randomized_singular_value_decomposition import RandomizedSingularValueDecomposition
from matplotlib import pyplot as plt
import numpy as np
import json


class StructuralMechanicsAnalysisMSConstraints(StructuralMechanicsAnalysis):

    def __init__(self,model,project_parameters):
        super().__init__(model,project_parameters)
        self.time_step_solution_container = []

    def ModifyInitialGeometry(self):
        super().ModifyInitialGeometry()
        model_part = self.model.GetModelPart("Structure")
        constraint_id = 100
        constant = 0.0

        # SETTING THE MASTER-SLAVE constraints
        # middle
        master_nodes_sub_model_part = model_part.GetSubModelPart("MASTER_Surface_Mid")
        slave_node_sub_model_part = model_part.GetSubModelPart("SLAVE_Surface_Mid")
        weight = 1.0
        for master, slave in zip(master_nodes_sub_model_part.Nodes,  slave_node_sub_model_part.Nodes):
            print('pair is: master ', master.Id, 'slave ', slave.Id)
            model_part.CreateNewMasterSlaveConstraint("LinearMasterSlaveConstraint", constraint_id, master, KratosMultiphysics.DISPLACEMENT_X, slave, KratosMultiphysics.DISPLACEMENT_X, weight, constant)
            constraint_id += 1
            model_part.CreateNewMasterSlaveConstraint("LinearMasterSlaveConstraint", constraint_id, master, KratosMultiphysics.DISPLACEMENT_Y, slave, KratosMultiphysics.DISPLACEMENT_Y, weight, constant)
            constraint_id += 1
            model_part.CreateNewMasterSlaveConstraint("LinearMasterSlaveConstraint", constraint_id, master, KratosMultiphysics.DISPLACEMENT_Z, slave, KratosMultiphysics.DISPLACEMENT_Z, weight, constant)
            constraint_id += 1
            model_part.CreateNewMasterSlaveConstraint("LinearMasterSlaveConstraint", constraint_id, master, KratosMultiphysics.ROTATION_X, slave, KratosMultiphysics.ROTATION_X, weight, constant)
            constraint_id += 1
            model_part.CreateNewMasterSlaveConstraint("LinearMasterSlaveConstraint", constraint_id, master, KratosMultiphysics.ROTATION_Y, slave, KratosMultiphysics.ROTATION_Y, weight, constant)
            constraint_id += 1
            model_part.CreateNewMasterSlaveConstraint("LinearMasterSlaveConstraint", constraint_id, master, KratosMultiphysics.ROTATION_Z, slave, KratosMultiphysics.ROTATION_Z, weight, constant)
            constraint_id += 1
        # top
        master_nodes_sub_model_part = model_part.GetSubModelPart("MASTER_Surface_Top")
        slave_node_sub_model_part = model_part.GetSubModelPart("SLAVE_Surface_Top")
        weight = 0.5
        for master_node in master_nodes_sub_model_part.Nodes:
            for slave_node in slave_node_sub_model_part.Nodes:
                print('pair is: master ', master_node.Id, 'slave ', slave_node.Id)
                model_part.CreateNewMasterSlaveConstraint("LinearMasterSlaveConstraint", constraint_id, master_node, KratosMultiphysics.DISPLACEMENT_X, slave_node, KratosMultiphysics.DISPLACEMENT_X, weight, constant)
                constraint_id += 1
                model_part.CreateNewMasterSlaveConstraint("LinearMasterSlaveConstraint", constraint_id, master_node, KratosMultiphysics.DISPLACEMENT_Y, slave_node, KratosMultiphysics.DISPLACEMENT_Y, weight, constant)
                constraint_id += 1
                model_part.CreateNewMasterSlaveConstraint("LinearMasterSlaveConstraint", constraint_id, master_node, KratosMultiphysics.DISPLACEMENT_Z, slave_node, KratosMultiphysics.DISPLACEMENT_Z, weight, constant)
                constraint_id += 1

    def FinalizeSolutionStep(self):
        super().FinalizeSolutionStep()
        ArrayOfDisplacements = []
        for node in self._GetSolver().GetComputingModelPart().Nodes:
            ArrayOfDisplacements.append(node.GetSolutionStepValue(KratosMultiphysics.ROTATION_X, 0))
            ArrayOfDisplacements.append(node.GetSolutionStepValue(KratosMultiphysics.ROTATION_Y, 0))
            ArrayOfDisplacements.append(node.GetSolutionStepValue(KratosMultiphysics.ROTATION_Z, 0))
            ArrayOfDisplacements.append(node.GetSolutionStepValue(KratosMultiphysics.DISPLACEMENT_X, 0))
            ArrayOfDisplacements.append(node.GetSolutionStepValue(KratosMultiphysics.DISPLACEMENT_Y, 0))
            ArrayOfDisplacements.append(node.GetSolutionStepValue(KratosMultiphysics.DISPLACEMENT_Z, 0))
        self.time_step_solution_container.append(ArrayOfDisplacements)

    def GetSnapshotsMatrix(self):
        SnapshotMatrix = np.zeros((len(self.time_step_solution_container[0]), len(self.time_step_solution_container)))
        for i in range(len(self.time_step_solution_container)):
            Snapshot_i= np.array(self.time_step_solution_container[i])
            SnapshotMatrix[:,i] = Snapshot_i.transpose()
        return SnapshotMatrix






class RunHROM(StructuralMechanicsAnalysisROM):

    def ModifyInitialGeometry(self):
        """Here is the place where the HROM_WEIGHTS are assigned to the selected elements and conditions"""
        super().ModifyInitialGeometry()
        computing_model_part = self._solver.GetComputingModelPart()
        ## Adding the weights to the corresponding elements
        with open('ElementsAndWeights.json') as f:
            HR_data = json.load(f)
            for key in HR_data["Elements"].keys():
                computing_model_part.GetElement(int(key)+1).SetValue(romapp.HROM_WEIGHT, HR_data["Elements"][key])
            for key in HR_data["Conditions"].keys():
                computing_model_part.GetCondition(int(key)+1).SetValue(romapp.HROM_WEIGHT, HR_data["Conditions"][key])







if __name__ == "__main__":
    ### run FOM
    with open("ProjectParameters.json",'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())

    model = KratosMultiphysics.Model()
    simulation = StructuralMechanicsAnalysisMSConstraints(model,parameters)
    simulation.Run()
    SnapshostMatrixFOM = simulation.GetSnapshotsMatrix()

    # #check that master slave constraints are respected (visually)
    # number_of_dofs = 6 #3 displacements and 3 rotations
    # master_nodes = [2,4]
    # slave_nodes = [5,6]
    # for master, slave in zip(master_nodes,slave_nodes):
    #     master_node_solution = SnapshostMatrixFOM[ ((master-1)*number_of_dofs):((master-1)*number_of_dofs)+number_of_dofs,:]
    #     slave_node_solution = SnapshostMatrixFOM[ ((slave-1)*number_of_dofs):((slave-1)*number_of_dofs)+number_of_dofs,:]
    #     for i in range(number_of_dofs):
    #         plt.title('master-slave constraints')
    #         if i==0:
    #             plt.plot(master_node_solution[i,:], 'ro', label = 'master')
    #             plt.plot(slave_node_solution[i,:], 'b-', label = 'slave')
    #         else:
    #             plt.plot(master_node_solution[i,:], 'ro')
    #             plt.plot(slave_node_solution[i,:], 'b-')
    #     plt.legend()
    #     plt.show()


    # ROM simulation

    ## Taking the SVD ###
    truncation_tolerance_svd = 1e-8
    u,s,_,_= RandomizedSingularValueDecomposition().Calculate(SnapshostMatrixFOM,truncation_tolerance_svd)

    ### Plotting singular values  ###
    plt.plot( range(0,len(s)), np.log(s), marker='o', markerfacecolor='blue', markersize=12, color='skyblue', linewidth=4)
    plt.title('Singular Values')
    plt.show()

    ### Saving the nodal basis ###
    basis_POD={"rom_settings":{},"nodal_modes":{}}
    basis_POD["rom_settings"]["nodal_unknowns"] = ["ROTATION_X","ROTATION_Y","ROTATION_Z","DISPLACEMENT_X","DISPLACEMENT_Y","DISPLACEMENT_Z"]
    basis_POD["rom_settings"]["number_of_rom_dofs"] = np.shape(u)[1]
    Dimensions = len(basis_POD["rom_settings"]["nodal_unknowns"])
    N_nodes=np.shape(u)[0]/Dimensions
    N_nodes = int(N_nodes)
    node_Id=np.linspace(1,N_nodes,N_nodes)
    i = 0
    for j in range (0,N_nodes):
        basis_POD["nodal_modes"][int(node_Id[j])] = (u[i:i+Dimensions].tolist())
        i=i+Dimensions
    with open('RomParameters.json', 'w') as f:
        json.dump(basis_POD,f, indent=2)
    print('\n\nNodal basis printed in json format\n\n')




    ### train HROM by running ROM with ECM element selection algorithm
    with open("ProjectParameters.json",'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())
    model = KratosMultiphysics.Model()
    simulation = StructuralMechanicsAnalysisROM(model,parameters,'EmpiricalCubature')
    simulation.Run()




    ### run HROM
    with open("ProjectParametersHROM.json",'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())
    model = KratosMultiphysics.Model()
    simulation = RunHROM(model,parameters)
    simulation.Run()