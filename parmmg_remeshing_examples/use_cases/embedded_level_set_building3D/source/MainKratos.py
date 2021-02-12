import os
#Kratos Imports
import KratosMultiphysics
import KratosMultiphysics.mpi as KratosMPI
import KratosMultiphysics.FluidDynamicsApplication as KratosFluidDynamics
import KratosMultiphysics.TrilinosApplication as TrilinosApplication
import KratosMultiphysics.MeshingApplication

#Kratos Fluid Dynamic Analysis Imports
from KratosMultiphysics.FluidDynamicsApplication.fluid_dynamics_analysis import FluidDynamicsAnalysis
import KratosMultiphysics.TrilinosApplication.trilinos_linear_solver_factory as trilinos_linear_solver_factory

from KratosMultiphysics.mpi.distributed_gid_output_process import DistributedGiDOutputProcess as GiDOutputProcess
import KratosMultiphysics.mpi.distributed_import_model_part_utility as distributed_import_model_part_utility


#Kratos System Imports
class Remesher():
    def __init__(self,model,project_parameters, remeshing_parameters):
        self.model = model
        self.project_parameters = project_parameters
        self.main_model_part = self.model.CreateModelPart(project_parameters["solver_settings"]["model_part_name"].GetString())
        self.main_model_part.ProcessInfo.SetValue(KratosMultiphysics.DOMAIN_SIZE, self.project_parameters["solver_settings"]["domain_size"].GetInt())

        self.main_model_part.AddNodalSolutionStepVariable(KratosMultiphysics.PRESSURE)
        self.main_model_part.AddNodalSolutionStepVariable(KratosMultiphysics.VELOCITY)
        self.main_model_part.AddNodalSolutionStepVariable(KratosMultiphysics.DENSITY)
        self.main_model_part.AddNodalSolutionStepVariable(KratosMultiphysics.ACCELERATION)
        self.main_model_part.AddNodalSolutionStepVariable(KratosMultiphysics.MESH_VELOCITY)
        self.main_model_part.AddNodalSolutionStepVariable(KratosMultiphysics.BODY_FORCE)
        self.main_model_part.AddNodalSolutionStepVariable(KratosMultiphysics.NODAL_AREA)
        self.main_model_part.AddNodalSolutionStepVariable(KratosMultiphysics.REACTION)
        self.main_model_part.AddNodalSolutionStepVariable(KratosMultiphysics.REACTION_WATER_PRESSURE)
        self.main_model_part.AddNodalSolutionStepVariable(KratosMultiphysics.NORMAL)
        self.main_model_part.AddNodalSolutionStepVariable(KratosMultiphysics.EXTERNAL_PRESSURE)
        self.main_model_part.AddNodalSolutionStepVariable(KratosMultiphysics.DISTANCE)              # Distance function nodal values
        self.main_model_part.AddNodalSolutionStepVariable(KratosMultiphysics.FLAG_VARIABLE)
        self.main_model_part.AddNodalSolutionStepVariable(KratosMultiphysics.DISTANCE_GRADIENT)
        self.main_model_part.AddNodalSolutionStepVariable(KratosMultiphysics.PARTITION_INDEX)
        self.main_model_part.AddNodalSolutionStepVariable(KratosMultiphysics.RIGID_BODY_ID)
        self.main_model_part.AddNodalSolutionStepVariable(KratosFluidDynamics.EMBEDDED_WET_PRESSURE)          # Post-process variable (stores the fluid nodes pressure and is set to 0 in the structure ones)
        self.main_model_part.AddNodalSolutionStepVariable(KratosFluidDynamics.EMBEDDED_WET_VELOCITY)

        import_parameters = KratosMultiphysics.Parameters("""{
            "echo_level" : 0,
            "model_import_settings" : {
                "input_type" : "mdpa",
                "input_filename" : "model_part_name",
                "partition_in_memory" : false
            }
        }""")

        import_parameters["model_import_settings"]["input_filename"].SetString(project_parameters["solver_settings"]["model_import_settings"]["input_filename"].GetString())

        # Construct the Trilinos import model part utility
        distributed_model_part_importer = KratosMPI.distributed_import_model_part_utility.DistributedImportModelPartUtility(self.main_model_part, import_parameters)

        # Execute the Metis partitioning and reading
        distributed_model_part_importer.ImportModelPart()
        distributed_model_part_importer.CreateCommunicators()

        communicator = KratosMultiphysics.DataCommunicator.GetDefault()
        rank = communicator.Rank()
        if rank == 0:
            if not os.path.exists("gid_output"):
                os.makedirs("gid_output")
        communicator.Barrier()

        self.remeshing_parameters = remeshing_parameters
        self.skin_model_part = model.CreateModelPart("skin")
        self.skin_model_part.ProcessInfo.SetValue(KratosMultiphysics.DOMAIN_SIZE, self.project_parameters["solver_settings"]["domain_size"].GetInt())
        self.skin_model_part.AddNodalSolutionStepVariable(KratosMultiphysics.VELOCITY)
        self.skin_model_part.AddNodalSolutionStepVariable(KratosMultiphysics.FLAG_VARIABLE)
        try:
            KratosMultiphysics.ModelPartIO('skin_building').ReadModelPart(self.skin_model_part)
        except:
            raise(Exception("skin_building.mdpa not found. Please check that you have unzipped the file skin_building.zip"))

    def InitializeGeometry(self):
        # Computing continuous distance required to compute the metric (only on intersected elements)
        tolerance = 1e-12
        calculate_distance_process = KratosMultiphysics.CalculateDistanceToSkinProcess3D(
                self.main_model_part,
                self.skin_model_part, tolerance)
        calculate_distance_process.Execute()

        for step in range(1, self.remeshing_parameters["number_of_iterations"].GetInt() + 1):
            # Computing distance far away from the body (extending previous computed distance)
            linear_solver_settings=KratosMultiphysics.Parameters("""
            {
                "solver_type": "amgcl",
                "max_iteration": 400,
                "gmres_krylov_space_dimension": 100,
                "smoother_type":"ilu0",
                "coarsening_type":"smoothed_aggregation",
                "coarse_enough" : 5000,
                "krylov_type": "lgmres",
                "tolerance": 1e-9,
                "verbosity": 0,
                "scaling": false
            }""")

            linear_solver = trilinos_linear_solver_factory.ConstructSolver(linear_solver_settings)
            maximum_iterations = 1
            EpetraCommunicator = TrilinosApplication.CreateCommunicator()

            variational_distance_process = TrilinosApplication.TrilinosVariationalDistanceCalculationProcess3D(
                EpetraCommunicator,
                self.main_model_part,
                linear_solver,
                maximum_iterations,
                KratosMultiphysics.VariationalDistanceCalculationProcess3D.CALCULATE_EXACT_DISTANCES_TO_PLANE.AsFalse(),
                "aux_model_part"+str(step)
            )
            variational_distance_process.Execute()

            # Computing gradient and nodal_h required to compute the metric
            local_gradient = KratosMultiphysics.ComputeNodalGradientProcess3D(self.main_model_part,
                KratosMultiphysics.DISTANCE,
                KratosMultiphysics.DISTANCE_GRADIENT,
                KratosMultiphysics.NODAL_AREA)
            local_gradient.Execute()

            find_nodal_h = KratosMultiphysics.FindNodalHNonHistoricalProcess(self.main_model_part)
            find_nodal_h.Execute()

            # GiD output for visualization purposes
            self._OutputToGid('embedded_distance_field_'+str(step))

            # Compute the metric accorind to the distance computed (level-set)
            metric_parameters = self.remeshing_parameters["metric_parameters"]
            metric_process = KratosMultiphysics.MeshingApplication.ComputeLevelSetSolMetricProcess3D(
                self.main_model_part,
                KratosMultiphysics.DISTANCE_GRADIENT,
                metric_parameters)
            metric_process.Execute()

            # Call ParMmg
            parmmg_parameters = self.remeshing_parameters["parmmg_parameters"]
            parmmg_process = KratosMultiphysics.MeshingApplication.ParMmgProcess3D(self.main_model_part, parmmg_parameters)
            parmmg_process.Execute()

            # Verify the orientation of the new mesh and compute normals
            tmoc = KratosMultiphysics.TetrahedralMeshOrientationCheck
            throw_errors = False
            flags = (tmoc.COMPUTE_NODAL_NORMALS).AsFalse() | (tmoc.COMPUTE_CONDITION_NORMALS).AsFalse()
            flags |= tmoc.ASSIGN_NEIGHBOUR_ELEMENTS_TO_CONDITIONS
            KratosMultiphysics.TetrahedralMeshOrientationCheck(self.main_model_part,throw_errors, flags).Execute()

            # Computing continuous distance required to compute the metric (only on intersected elements)
            tolerance = 1e-12
            calculate_distance_process = KratosMultiphysics.CalculateDistanceToSkinProcess3D(
                    self.main_model_part,
                    self.skin_model_part, tolerance)
            calculate_distance_process.Execute()


        self._OutputToGid('final_remeshed_embedded_distance_field')

        # Compute the discontinuous distance for ausas formulation
        calculate_distance_process = KratosMultiphysics.CalculateDiscontinuousDistanceToSkinProcess3D(
            self.main_model_part,
            self.skin_model_part)
        calculate_distance_process.Execute()

    def _OutputToGid(self, file_name):
        gid_output = GiDOutputProcess(
            self.main_model_part,
            "gid_output/"+file_name,
            KratosMultiphysics.Parameters("""
                {
                    "result_file_configuration" : {
                        "gidpost_flags": {
                            "GiDPostMode": "GiD_PostBinary",
                            "MultiFileFlag": "SingleFile"
                        },
                        "nodal_results"       : ["DISTANCE", "PARTITION_INDEX"],
                        "nodal_nonhistorical_results": [],
                        "gauss_point_results" : [],
                        "nodal_flags_results": [],
                        "elemental_conditional_flags_results": []
                    }
                }
                """)
        )
        gid_output.ExecuteInitialize()
        gid_output.ExecuteBeforeSolutionLoop()
        gid_output.ExecuteInitializeSolutionStep()
        gid_output.PrintOutput()
        gid_output.ExecuteFinalizeSolutionStep()
        gid_output.ExecuteFinalize()

    def Run(self):
        # Preparing settings to run an already loaded model
        self.project_parameters["solver_settings"]["model_import_settings"]["input_type"].SetString("use_input_model_part")
        simulation = FluidDynamicsAnalysis(self.model, self.project_parameters)
        simulation.Run()



if __name__ == "__main__":

    with open("ProjectParameters.json",'r') as parameter_file:
        parameters = KratosMultiphysics.Parameters(parameter_file.read())

    with open("RemeshingParameters.json",'r') as parameter_file:
        remeshing_parameters = KratosMultiphysics.Parameters(parameter_file.read())

    model = KratosMultiphysics.Model()
    simulation = Remesher(model, parameters, remeshing_parameters)
    simulation.InitializeGeometry()
    simulation.Run()
