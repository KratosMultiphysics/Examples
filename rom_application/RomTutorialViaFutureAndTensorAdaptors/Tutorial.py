#!/usr/bin/env python3
"""
Nonlinear reduced-order modelling (ROM) demo using Kratos' Future suite.

This is the standalone-script version of the accompanying Jupyter notebook.
The interactive parameter sliders have been omitted; the script runs the
selected ROM projection and compares its result with the full-order model.

Required Python packages:
    KratosMultiphysics
    KratosStructuralMechanicsApplication
    numpy
    scipy
    torch
    matplotlib

The three Kratos input files are downloaded automatically if they are not
already present in --data-dir.
"""

import argparse
from pathlib import Path
import urllib.request

import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.collections import PolyCollection

import numpy as np
import scipy.sparse as sp
import torch
import torch.nn as nn
import KratosMultiphysics as KM
import KratosMultiphysics.StructuralMechanicsApplication as SMA
from KratosMultiphysics.process_factory import KratosProcessFactory
from KratosMultiphysics import scipy_conversion_tools

torch.set_default_dtype(torch.float64)


INPUT_BASE_URL = (
    "https://raw.githubusercontent.com/KratosMultiphysics/Examples/refs/heads/master/"
    "rom_application/RomTutorialViaFutureAndTensorAdaptors/"
)
INPUT_FILES = (
    "cantilever.mdpa",
    "loads_and_constraints.json",
    "materials.json",
)


def ensure_input_files(data_dir: Path) -> None:
    """Download the tutorial input files that are missing from data_dir."""
    data_dir.mkdir(parents=True, exist_ok=True)
    for filename in INPUT_FILES:
        destination = data_dir / filename
        if not destination.exists():
            url = INPUT_BASE_URL + filename
            print(f"Downloading {filename}...")
            urllib.request.urlretrieve(url, destination)


def create_model(data_dir: Path):
    """Create and initialize the Kratos model from the tutorial input files."""
    model = KM.Model()
    model_part = model.CreateModelPart("MainModelPart")

    model_part.AddNodalSolutionStepVariable(KM.DISPLACEMENT)
    model_part.AddNodalSolutionStepVariable(KM.REACTION)
    model_part.AddNodalSolutionStepVariable(KM.VOLUME_ACCELERATION)

    mdpa_file_base_name = str(data_dir / "cantilever")
    model_part_io = KM.ModelPartIO(mdpa_file_base_name)
    model_part_io.ReadModelPart(model_part)

    KM.VariableUtils().AddDof(KM.DISPLACEMENT_X, KM.REACTION_X, model_part)
    KM.VariableUtils().AddDof(KM.DISPLACEMENT_Y, KM.REACTION_Y, model_part)

    # Instantiate the processes for the loads and constraints.
    factory = KratosProcessFactory(model)
    with open(data_dir / "loads_and_constraints.json", "r", encoding="utf-8") as file:
        process_parameters = KM.Parameters(file.read())

    list_of_processes = []
    list_of_processes += factory.ConstructListOfProcesses(
        process_parameters["constraints_process_list"]
    )
    list_of_processes += factory.ConstructListOfProcesses(
        process_parameters["loads_process_list"]
    )

    # Execute the processes. The loads are constant in this example.
    for process in list_of_processes:
        process.ExecuteInitialize()
        process.ExecuteBeforeSolutionLoop()
        process.ExecuteInitializeSolutionStep()

    # Apply material parameters specified in materials.json.
    with open(data_dir / "materials.json", "r", encoding="utf-8") as material_file:
        material_parameters = KM.Parameters(material_file.read())
    KM.ReadMaterialsUtility(model).ReadMaterials(material_parameters)

    return model, model_part


class KratosHelper():

    # Parameters for the Kratos scheme
    scheme_parameters = KM.Parameters("""{
        "build_settings": {
            "name": "block_builder"
        },
        "echo_level": 0,
        "move_mesh": false,
        "name": "static_scheme",
        "reform_dofs_at_each_step": false
        }""")

    def __init__(self, model, model_part):

        self.model = model
        self.model_part = model_part

        # Instantiate and initialize Kratos static scheme and strategy data
        self.scheme = KM.Future.StaticScheme(self.model_part, self.scheme_parameters)
        self.strategy_data = KM.Future.ImplicitStrategyData()

        self.scheme.Initialize(self.strategy_data)
        self.scheme.Predict(self.strategy_data)
        self.scheme.InitializeSolutionStep(self.strategy_data)
        self.scheme.InitializeNonLinIteration(self.strategy_data)

        # Get a TensorAdaptor for the initial node positions. The data can be retrieved later via CollectData()
        dim=2
        self.node_pos_ta = KM.TensorAdaptors.NodePositionTensorAdaptor(self.model_part.Nodes, KM.Configuration.Initial, data_shape = [dim])
        self.node_pos_ta.Check()

        # Get number of DoFs for later use
        self.num_dofs = len(self.strategy_data.GetEffectiveDofSet())

    def assign_values_to_kratos_database(self, u_vec):
        # Assigns displacement values directly to the Kratos DoFs, ensuring correct order.
        self.strategy_data.GetEffectiveDofSet().SetValues(u_vec.ravel())

    def build_system_to_u(self, u_vec, as_scipy=False):
        # Set all system vectors/matrices to zero
        lin_system = self.strategy_data.GetLinearSystem()
        lin_system.GetVector(KM.Future.DenseVectorTag.Dx).SetValue(0.0)
        rhs = lin_system.GetVector(KM.Future.DenseVectorTag.RHS)
        lhs = lin_system.GetMatrix(KM.Future.SparseMatrixTag.LHS)
        rhs.SetValue(0.0)
        lhs.SetValue(0.0)

        # Assign given u_vec to the Kratos database
        self.assign_values_to_kratos_database(u_vec.ravel())

        # Build the system and apply Dirichlet conditions
        self.scheme.Build(lhs, rhs)
        self.scheme.BuildLinearSystemConstraints(self.strategy_data)
        self.scheme.ApplyLinearSystemConstraints(self.strategy_data)

        # Collect built Kratos' RHS and LHS with constraints applied
        eff_lin_sys = self.strategy_data.GetEffectiveLinearSystem()
        eff_rhs = eff_lin_sys.GetVector(KM.Future.DenseVectorTag.RHS)
        eff_lhs = eff_lin_sys.GetMatrix(KM.Future.SparseMatrixTag.LHS)

        # If as_scipy, convert rhs to numpy and lhs to scipy csr martix
        if as_scipy:
            eff_rhs = np.array(eff_rhs, copy=False)
            eff_lhs = scipy_conversion_tools.to_csr(eff_lhs)

        return eff_rhs, eff_lhs

    def get_node_coordinates(self):
        # Use CollectData() for the TensorAdaptor instantiated previously to collect Kratos' data.
        # Then .data returns these values as a numpy array.
        self.node_pos_ta.CollectData()
        return self.node_pos_ta.data

    def perform_FOM_simulation(self):
        # Sets system to 0 (undeformed configuration), then builds it.
        self.build_system_to_u(np.zeros(self.num_dofs))

        # Instantiate a linear solver, then solve the system
        solver = KM.Future.SkylineLUFactorizationSolver()
        eff_lin_sys = self.strategy_data.GetEffectiveLinearSystem()
        solver.PerformSolutionStep(eff_lin_sys)
        solver.FinalizeSolutionStep(eff_lin_sys)

        # Get the resulting displacements vector as our result
        eff_dx = eff_lin_sys.GetVector(KM.Future.DenseVectorTag.Dx)

        return np.array(eff_dx, copy=True)

    def get_r_norm_squared_and_potential_energy_at_u(self, u_vec):
        R, K = self.build_system_to_u(u_vec)
        r_norm_squared = np.linalg.norm(R)**2
        potential_energy = -np.dot(u_vec,R)-1/2*np.dot(u_vec,K@u_vec)
        return r_norm_squared, potential_energy



class CantileverParametrization(nn.Module):
    def __init__(self, kratos_helper):
        super().__init__()
        self.kratos_helper = kratos_helper

        # Initialize tensors for x and y coordinates from the kratos interface (this is constant)
        self.coords_tensor = torch.tensor(self.kratos_helper.get_node_coordinates(), dtype=torch.float64)

        ##### MODIFIABLE CODE

        # Adjust the number of parameters you need for your model (see the forward method for more info)
        num_params = 6

        #####

        # Initialize parameters to zero
        self.init_params = torch.tensor(np.zeros(num_params), dtype=torch.float64)


    def get_coords(self):
        return self.coords_tensor[:,0], self.coords_tensor[:,1]

    def forward(self, q_tens):
        x,y = self.get_coords()

        ##### MODIFIABLE CODE

        # Here we assume that num_params is six. Change accordingly
        a,b,c,d,e,f = q_tens

        # Define the parametrized functions for the displacement on x and on y
        D_x = x*(a*y+b)
        D_y = x*(c*x**3+d*x**2+e*x+f)

        #####

        return torch.vstack([D_x, D_y]).T.ravel()

    def run(self, q):
        # Ensure q is a tensor before passing to forward
        if not isinstance(q, torch.Tensor):
            q = torch.tensor(q, dtype=torch.float64)
        return self.forward(q).detach().numpy()

    def get_jacobian(self, q):

        # Get the function to compute the jacobian of the decoder with respect to q (unevaluated)
        self.compute_jacobian_function = torch.func.jacfwd(self.forward)

        if not isinstance(q, torch.Tensor):
            q = torch.tensor(q, dtype=torch.float64)
        return self.compute_jacobian_function(q).detach().numpy()




class Plotter:
    def __init__(self, model_part, kratos_helper):

        # Get connectivity from model part (nodes for each quad element)
        node_id_to_idx = {node.Id: i for i, node in enumerate(model_part.Nodes)}
        self.connectivity = np.array([[node_id_to_idx[node.Id] for node in elem.GetGeometry()] for elem in model_part.Elements])

        self.kratos_helper = kratos_helper

        self.u_fom = None

    def get_positions_from_displacement(self, u):
        coords = self.kratos_helper.get_node_coordinates()
        return u.reshape(coords.shape) + coords

    def plot_meshes(self, u_list, labels = None, title = None, colors = None):
        # Create a list even if there is only one mesh to simulate
        if type(u_list) is not list:
            u_list = [u_list]
        if labels is not None and type(labels) is not list:
            labels = [labels]
        if colors is None:
            # Get a set of colors from a predefined palette (max 10 different colors)
            colors = plt.get_cmap('tab10').colors[:len(u_list)]
        elif type(colors) is not list:
            colors = [colors]

        # Single axis for all meshes
        fig, ax = plt.subplots(figsize=(10, 6))

        # Get node positions from fiven displacements
        pos_vec_list = [self.get_positions_from_displacement(u)for u in u_list]

        # Get positions for each element vertex
        element_verts_list = [pos_vec[self.connectivity] for pos_vec in pos_vec_list]

        # Obtain and add mesh visualization objects for all meshes.
        # First mesh will appear at the back, then each one in front of the previous one.
        for element_verts, color in zip(element_verts_list, colors):
            mesh_object = PolyCollection(element_verts, color = color, linewidths=0.8, alpha=0.5)
            ax.add_collection(mesh_object)

        # Automatically adjust limits with a margin
        # Combine all points to find the global bounding box
        all_points = np.vstack(pos_vec_list)
        ax.update_datalim(all_points)  # Tell the axis about the data extent
        ax.margins(0.05)               # Add a 5% margin around the data
        ax.autoscale_view()            # Apply the limits

        ax.set_aspect('equal', 'box')  # Forces 1:1 aspect ratio

        if title is not None: ax.set_title(title)
        if labels is not None:
            custom_lines = [Line2D([0], [0], color=color, lw=1.5, alpha=0.5) for color in colors]
            ax.legend(custom_lines, labels, loc='best')

        plt.tight_layout()
        plt.show()


def solve_rom(kratos_helper, decoder, plotter, projection="galerkin"):
    """Solve the reduced problem and compare the ROM and FOM solutions."""
    ##### MODIFIABLE CODE
    projection = projection  # "galerkin" or "lspg"
    #####

    # Get the pytorch tensor for the initial parameters vector
    q = decoder.init_params.clone()

    # Newton Raphson loop
    it = 0
    it_max = 10
    converged=False
    print(f"Starting solver. Using {projection} projection.")
    while it<it_max and not converged:
        it+=1

        #u = D(q)
        u = decoder.run(q)

        #compute Kfom(u=D(q)), Rfom(u=D(q))
        R, K = kratos_helper.build_system_to_u(u, as_scipy=True)

        #compute GradD:= diff(D(q),q)
        grad_D = decoder.get_jacobian(q)

        #define and solve ROM problem
        if projection == "galerkin":
            K_rom = grad_D.T@K@grad_D
            R_rom = grad_D.T@R
        elif projection == "lspg":
            K_rom = grad_D.T@K.T@K@grad_D
            R_rom = grad_D.T@K.T@R
        dq = np.linalg.solve(K_rom,R_rom)

        #update database
        q = q + dq

        #check convergence
        ratio = np.linalg.norm(dq)/np.linalg.norm(q)

        print(f"Iteration {it}:")
        print("  q:", q)
        print(" |dq|/|q|:", ratio)

        if ratio < 1e-9:
            converged = True
            print(f"Converged in {it} iterations.")

    # Plot the ROM results against the FOM ones.

    u_fom = kratos_helper.perform_FOM_simulation()
    u_rom = decoder.run(q)

    plotter.plot_meshes([u_fom, u_rom], labels=["FOM", "ROM"], title="Mesh Deformation: ROM vs FOM")

    # Print residual norm squared and potential energy
    R2_rom, Pi_rom = kratos_helper.get_r_norm_squared_and_potential_energy_at_u(u_rom)
    print("ROM |R|^2: ", R2_rom)
    print("ROM Potential energy: ", Pi_rom)
    R2_fom, Pi_fom = kratos_helper.get_r_norm_squared_and_potential_energy_at_u(u_fom)
    print("FOM |R|^2: ", R2_fom)
    print("FOM Potential energy: ", Pi_fom)



def main():
    parser = argparse.ArgumentParser(
        description="Run the Kratos nonlinear ROM cantilever tutorial."
    )
    parser.add_argument(
        "--projection",
        choices=("galerkin", "lspg"),
        default="galerkin",
        help="Reduced projection method (default: galerkin).",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="Directory containing the Kratos input files (default: script directory).",
    )
    args = parser.parse_args()

    ensure_input_files(args.data_dir)
    model, model_part = create_model(args.data_dir)
    kratos_helper = KratosHelper(model, model_part)
    decoder = CantileverParametrization(kratos_helper)
    plotter = Plotter(model_part, kratos_helper)

    solve_rom(kratos_helper, decoder, plotter, projection=args.projection)


if __name__ == "__main__":
    main()
