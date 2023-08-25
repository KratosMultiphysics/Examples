import os
import numpy as np
from ezyrb import Database
from ezyrb import ReducedOrderModel as ROM
from ezyrb import RBF, POD
from sys import argv

def interpolate_parameters(analysis_directory_path, new_parameters_list):
    # These are the hardcoded filenames and their corresponding parameters
    hardcoded_files_and_parameters = {
        "velocity_field_200.npy": 200,
        "velocity_field_300.npy": 300,
        "velocity_field_400.npy": 400,
        "velocity_field_500.npy": 500
    }
    
    snapshots_list = []
    parameters_list = list(hardcoded_files_and_parameters.values())
    
    for filename, parameter in hardcoded_files_and_parameters.items():
        full_path = os.path.join(analysis_directory_path, filename)
        if os.path.exists(full_path):
            snapshots_list.append(np.load(full_path))
        else:
            print(f"Warning: Expected file {filename} not found in directory!")

    parameters = np.array(parameters_list).reshape(-1, 1)
    snapshots = np.array(snapshots_list)

    db = Database(parameters, snapshots)
    pod = POD()
    rbf = RBF()
    rom = ROM(db, pod, rbf)
    rom.fit()

    solutions_list = [rom.predict([element]) for element in new_parameters_list]
    for i, solution in enumerate(solutions_list):
        np.save(f"velocity_field_{new_parameters_list[i]}.npy", solution)

