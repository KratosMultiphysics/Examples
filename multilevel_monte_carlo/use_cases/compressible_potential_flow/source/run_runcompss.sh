#!/usr/bin/env bash

path_to_examples_folder=$(pwd)

materials_path_to_replace_poisson="problem_settings/materials.json"
materials_new_path_poisson="$path_to_examples_folder/problem_settings/materials.json"
mdpa_path_to_replace_0="problem_settings/naca0012Mesh4"
mdpa_new_path_0="$path_to_examples_folder/problem_settings/naca0012Mesh4"
mdpa_path_to_replace_1="problem_settings/CPS_MONTECARLO_MeshInterpError1e-2"
mdpa_new_path_1="$path_to_examples_folder/problem_settings/CPS_MONTECARLO_MeshInterpError1e-2"
mdpa_path_to_replace_2="problem_settings/CPS_MONTECARLO_MeshInterpError5e-3"
mdpa_new_path_2="$path_to_examples_folder/problem_settings/CPS_MONTECARLO_MeshInterpError5e-3"

# set absolute path in Kratos parameters
sed -i "s|$materials_path_to_replace_poisson|$materials_new_path_poisson|g" "problem_settings/parameters_potential_naca_lev0.json"
sed -i "s|$materials_path_to_replace_poisson|$materials_new_path_poisson|g" "problem_settings/parameters_potential_naca_lev1.json"
sed -i "s|$materials_path_to_replace_poisson|$materials_new_path_poisson|g" "problem_settings/parameters_potential_naca_lev2.json"
sed -i "s|$mdpa_path_to_replace_0|$mdpa_new_path_0|g" "problem_settings/parameters_potential_naca_lev0.json"
sed -i "s|$mdpa_path_to_replace_1|$mdpa_new_path_1|g" "problem_settings/parameters_potential_naca_lev1.json"
sed -i "s|$mdpa_path_to_replace_2|$mdpa_new_path_2|g" "problem_settings/parameters_potential_naca_lev2.json"

runcompss \
    --lang=python \
    --python_interpreter=python3 \
    --pythonpath=$path_to_folder \
    ./run_mc_Kratos.py problem_settings/parameters_xmc_asynchronous_mc_potentialFlow.json

# revert change in Kratos parameters
sed -i "s|$materials_new_path_poisson|$materials_path_to_replace_poisson|g" "problem_settings/parameters_potential_naca_lev0.json"
sed -i "s|$materials_new_path_poisson|$materials_path_to_replace_poisson|g" "problem_settings/parameters_potential_naca_lev1.json"
sed -i "s|$materials_new_path_poisson|$materials_path_to_replace_poisson|g" "problem_settings/parameters_potential_naca_lev2.json"
sed -i "s|$mdpa_new_path_0|$mdpa_path_to_replace_0|g" "problem_settings/parameters_potential_naca_lev0.json"
sed -i "s|$mdpa_new_path_1|$mdpa_path_to_replace_1|g" "problem_settings/parameters_potential_naca_lev1.json"
sed -i "s|$mdpa_new_path_2|$mdpa_path_to_replace_2|g" "problem_settings/parameters_potential_naca_lev2.json"