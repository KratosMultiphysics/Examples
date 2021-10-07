#!/usr/bin/env bash

path_to_examples_folder=$(pwd)

materials_path_to_replace_poisson="../problem_settings/materials_poisson_square_2d.json"
materials_new_path_poisson="$path_to_examples_folder/../problem_settings/materials_poisson_square_2d.json"
mdpa_path_to_replace="../problem_settings/square_finer_2d"
mdpa_new_path="$path_to_examples_folder/../problem_settings/square_finer_2d"

# set absolute path in Kratos parameters
sed -i "s|$materials_path_to_replace_poisson|$materials_new_path_poisson|g" "../problem_settings/parameters_poisson_square_2d_finer.json"
sed -i "s|$mdpa_path_to_replace|$mdpa_new_path|g" "../problem_settings/parameters_poisson_square_2d_finer.json"

runcompss \
    --lang=python \
    --python_interpreter=python3 \
    --pythonpath=$path_to_examples_folder/ \
    ./run_mlmc_Kratos.py

# revert change in Kratos parameters
sed -i "s|$materials_new_path_poisson|$materials_path_to_replace_poisson|g" "../problem_settings/parameters_poisson_square_2d_finer.json"
sed -i "s|$mdpa_new_path|$mdpa_path_to_replace|g" "../problem_settings/parameters_poisson_square_2d_finer.json"