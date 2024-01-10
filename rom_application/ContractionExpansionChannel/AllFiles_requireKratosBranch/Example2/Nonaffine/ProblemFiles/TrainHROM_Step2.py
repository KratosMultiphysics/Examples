import numpy as np
from KratosMultiphysics.RomApplication.empirical_cubature_method import EmpiricalCubatureMethod
from KratosMultiphysics.RomApplication.randomized_singular_value_decomposition import RandomizedSingularValueDecomposition
from matplotlib import pyplot as plt

import os.path
import os




def select_elements(svd_truncation_tolerance, residuals_svd_truncation_tolerance):

    weights = f'HROM/WeightsMatrix_{svd_truncation_tolerance}_{residuals_svd_truncation_tolerance}.npy'
    elements = f'HROM/Elementsvector_{svd_truncation_tolerance}_{residuals_svd_truncation_tolerance}.npy'

    if not os.path.exists(weights) and not os.path.exists(elements):
        #u,_,_,_ = RandomizedSingularValueDecomposition(RELATIVE_SVD=True).Calculate( np.load(f'HROM/Sr.npy'), tol) # HEAVY!!!
        u = np.load(f'HROM/basis_{svd_truncation_tolerance}_{residuals_svd_truncation_tolerance}.npy')

        hyper_reduction_element_selector = EmpiricalCubatureMethod()
        hyper_reduction_element_selector.SetUp(u)  #add again z
        hyper_reduction_element_selector.Initialize()
        hyper_reduction_element_selector.Calculate()


        w = np.squeeze(hyper_reduction_element_selector.w)
        z = np.squeeze(hyper_reduction_element_selector.z)

        WeightsMatrix = w.reshape(np.size(z),1)

        np.save(weights, WeightsMatrix )
        np.save(elements, z)



def split_matrix_in_columns(svd_truncation_tolerance):

    array_name = f'HROM/Sr_{svd_truncation_tolerance}'

    if not os.path.exists(array_name + '/column_block1.npy'):

        #load array
        array = np.load(array_name+'.npy')


        # Create a folder with the given name
        if not os.path.exists(array_name):
            os.makedirs(array_name)

        # Create the spliting of the matrix inside the folder
        if not os.path.exists(array_name + '/column_block1.npy'):
            n_rows, n_cols = array.shape
            block_size = n_rows

            start_col = 0
            block_number = 1

            while start_col < n_cols:
                end_col = min(start_col + block_size, n_cols)

                # Check if the remaining columns are too few; if so, merge with the previous block
                if n_cols - end_col < block_size / 2 and start_col != 0:
                    end_col = n_cols

                # Slice the array and save
                block = array[:, start_col:end_col]
                np.save(os.path.join(array_name, f'column_block{block_number}.npy'), block)

                start_col = end_col
                block_number += 1

        os.remove(array_name+'.npy')


def get_global_basis(svd_truncation_tolerance):

    if not os.path.exists(f'HROM/global_basis_{svd_truncation_tolerance}.npy'):

        array_name = f'HROM/Sr_{svd_truncation_tolerance}'

        # List all .npy files in the folder
        files = [f for f in os.listdir(array_name) if f.endswith('.npy')]

        u = None

        for file in files:
            file_path = os.path.join(array_name, file)

            # Load the file
            data = np.load(file_path)

            if u is None:
                u, s ,_ = np.linalg.svd(data, full_matrices=False)
            else:
                print('updating basis')
                u2, s2, _ = np.linalg.svd(data, full_matrices=False)
                u, s, _ = np.linalg.svd(np.c_[u*s, u2*s2], full_matrices=False)

        #store global basis and global singular values
        np.save(f'HROM/global_basis_{svd_truncation_tolerance}.npy',u)
        np.save(f'HROM/global_singular_values_{svd_truncation_tolerance}.npy',s)



def truncated_svd(u,s,epsilon=0):
    tol = np.finfo(float).eps*max(s)/2
    R = np.sum(s > tol)  # Definition of numerical rank
    if epsilon == 0:
        K = R
    else:
        SingVsq = np.multiply(s,s)
        SingVsq.sort()
        normEf2 = np.sqrt(np.cumsum(SingVsq))
        epsilon = epsilon*normEf2[-1] #relative tolerance
        T = (sum(normEf2<epsilon))
        K = len(s)-T
    K = min(R,K)
    return u[:, :K]




def get_particular_basis(svd_truncation_tolerance, residuals_svd_truncation_tolerance):

    basis = f'HROM/basis_{svd_truncation_tolerance}_{residuals_svd_truncation_tolerance}.npy'

    if not os.path.exists(basis):

        u = np.load(f'HROM/global_basis_{svd_truncation_tolerance}.npy')
        s = np.load(f'HROM/global_singular_values_{svd_truncation_tolerance}.npy')
        np.save(basis, truncated_svd(u,s,residuals_svd_truncation_tolerance))






if __name__=="__main__":
    #library for passing arguments to the script from bash
    from sys import argv

    Launch_Simulation = bool(int(argv[1]))
    Number_Of_Clusters= int(argv[2])
    svd_truncation_tolerance= float(argv[3])
    clustering= argv[4]
    overlapping = int(argv[5])
    working_path = argv[6]
    residuals_svd_truncation_tolerance = float(argv[7])
    residuals_svd_relative_to_global_residuals_snapshots = bool(argv[8])

    split_matrix_in_columns(svd_truncation_tolerance)
    get_global_basis(svd_truncation_tolerance)
    get_particular_basis(svd_truncation_tolerance, residuals_svd_truncation_tolerance)
    select_elements(svd_truncation_tolerance, residuals_svd_truncation_tolerance)
