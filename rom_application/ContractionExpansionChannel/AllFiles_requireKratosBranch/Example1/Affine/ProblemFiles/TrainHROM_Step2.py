import numpy as np
from KratosMultiphysics.RomApplication.empirical_cubature_method import EmpiricalCubatureMethod
from KratosMultiphysics.RomApplication.randomized_singular_value_decomposition import RandomizedSingularValueDecomposition
from matplotlib import pyplot as plt

import os.path

def get_global_norm(number_bases):
    norm = 0
    for i in range(number_bases):
        norm_a = np.linalg.norm(np.load(f'HROM/Sr_{i}.npy'))
        norm = np.sqrt(np.power(norm_a, 2) + np.power(norm, 2))
    return norm


def get_bases(number_bases, global_norm, tol,  relative=False):
    bases = []
    for i in range(number_bases):
        if relative:
            u,_,_,_ = RandomizedSingularValueDecomposition(RELATIVE_SVD=False).Calculate( np.load(f'HROM/Sr_{i}.npy'), tol* global_norm) #* global_norm
        else:
            u,_,_,_ = RandomizedSingularValueDecomposition(RELATIVE_SVD=True).Calculate( np.load(f'HROM/Sr_{i}.npy'), tol) #* global_norm
        bases.append(u)

    return bases

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


def get_basis(svd_truncation_tolerance, tol):

    basis = f'HROM/basis_{svd_truncation_tolerance}_{residuals_svd_truncation_tolerance}.npy'

    if not os.path.exists(basis):
        u,_,_,_ = RandomizedSingularValueDecomposition(RELATIVE_SVD=True).Calculate( np.load(f'HROM/Sr_{svd_truncation_tolerance}.npy'), tol)
        np.save( basis,u)


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


    get_basis(svd_truncation_tolerance, residuals_svd_truncation_tolerance)
    select_elements(svd_truncation_tolerance, residuals_svd_truncation_tolerance)

