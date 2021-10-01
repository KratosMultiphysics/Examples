#!/usr/bin/env bash

path_to_examples_folder=$(pwd)

materials_path_to_replace_poisson="../problem_settings/materials_poisson_square_2d.json"
materials_new_path_poisson="$path_to_examples_folder/../problem_settings/materials_poisson_square_2d.json"

mdpa_path_to_replace_1="../problem_settings/square_level_1"
mdpa_new_path_1="$path_to_examples_folder/../problem_settings/square_level_1"
mdpa_path_to_replace_2="../problem_settings/square_level_2"
mdpa_new_path_2="$path_to_examples_folder/../problem_settings/square_level_2"
mdpa_path_to_replace_3="../problem_settings/square_level_3"
mdpa_new_path_3="$path_to_examples_folder/../problem_settings/square_level_3"
mdpa_path_to_replace_4="../problem_settings/square_level_4"
mdpa_new_path_4="$path_to_examples_folder/../problem_settings/square_level_4"
mdpa_path_to_replace_5="../problem_settings/square_level_5"
mdpa_new_path_5="$path_to_examples_folder/../problem_settings/square_level_5"
mdpa_path_to_replace_6="../problem_settings/square_level_6"
mdpa_new_path_6="$path_to_examples_folder/../problem_settings/square_level_6"
mdpa_path_to_replace_7="../problem_settings/square_level_7"
mdpa_new_path_7="$path_to_examples_folder/../problem_settings/square_level_7"
mdpa_path_to_replace_8="../problem_settings/square_level_8"
mdpa_new_path_8="$path_to_examples_folder/../problem_settings/square_level_8"

# set absolute path in Kratos parameters
for i in 1 2 3 4 5 6 7 8
do
    sed -i "s|$materials_path_to_replace_poisson|$materials_new_path_poisson|g" "../problem_settings/parameters_level_$i.json"
    sed -i "s|$mdpa_path_to_replace_$i|$mdpa_new_path_$i|g" "../problem_settings/parameters_level_$i.json"
done

runcompss \
    --lang=python \
    --python_interpreter=python3 \
    --pythonpath=$path_to_examples_folder/ \
    ./run_mlmc_Kratos.py

# revert change in Kratos parameters
for i in 1 2 3 4 5 6 7 8
do
    sed -i "s|$materials_new_path_poisson|$materials_path_to_replace_poisson|g" "../problem_settings/parameters_level_$i.json"
    sed -i "s|$mdpa_new_path_$i|$mdpa_path_to_replace_$i|g" "../problem_settings/parameters_level_$i.json"
done