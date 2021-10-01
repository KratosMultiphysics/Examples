#!/usr/bin/env bash

path_to_examples_folder=$(pwd)

materials_path_to_replace_poisson="materials/materials_Re_1.json"
materials_new_path_poisson="$path_to_examples_folder/materials/materials_Re_1.json"
mdpa_path_to_replace_0="problem_settings/problem_zero_interperror0.5"
mdpa_new_path_0="$path_to_examples_folder/problem_settings/problem_zero_interperror0.5"
mdpa_path_to_replace_1="problem_settings/problem_zero_interperror0.25"
mdpa_new_path_1="$path_to_examples_folder/problem_settings/problem_zero_interperror0.25"
mdpa_path_to_replace_2="problem_settings/problem_zero_interperror0.1"
mdpa_new_path_2="$path_to_examples_folder/problem_settings/problem_zero_interperror0.1"

# set absolute path in Kratos parameters
sed -i "s|$materials_path_to_replace_poisson|$materials_new_path_poisson|g" "problem_settings/ProblemZeroParametersVMS_lev0.json"
sed -i "s|$materials_path_to_replace_poisson|$materials_new_path_poisson|g" "problem_settings/ProblemZeroParametersVMS_lev1.json"
sed -i "s|$materials_path_to_replace_poisson|$materials_new_path_poisson|g" "problem_settings/ProblemZeroParametersVMS_lev2.json"
sed -i "s|$mdpa_path_to_replace_0|$mdpa_new_path_0|g" "problem_settings/ProblemZeroParametersVMS_lev0.json"
sed -i "s|$mdpa_path_to_replace_1|$mdpa_new_path_1|g" "problem_settings/ProblemZeroParametersVMS_lev1.json"
sed -i "s|$mdpa_path_to_replace_2|$mdpa_new_path_2|g" "problem_settings/ProblemZeroParametersVMS_lev2.json"

runcompss \
    --lang=python \
    --python_interpreter=python3 \
    --pythonpath=$path_to_folder \
    ./run_mlmc_Kratos.py problem_settings/parameters_xmc_asynchronous_mlmc_problemZero.json

# revert change in Kratos parameters
sed -i "s|$materials_new_path_poisson|$materials_path_to_replace_poisson|g" "problem_settings/ProblemZeroParametersVMS_lev0.json"
sed -i "s|$materials_new_path_poisson|$materials_path_to_replace_poisson|g" "problem_settings/ProblemZeroParametersVMS_lev1.json"
sed -i "s|$materials_new_path_poisson|$materials_path_to_replace_poisson|g" "problem_settings/ProblemZeroParametersVMS_lev2.json"
sed -i "s|$mdpa_new_path_0|$mdpa_path_to_replace_0|g" "problem_settings/ProblemZeroParametersVMS_lev0.json"
sed -i "s|$mdpa_new_path_1|$mdpa_path_to_replace_1|g" "problem_settings/ProblemZeroParametersVMS_lev1.json"
sed -i "s|$mdpa_new_path_2|$mdpa_path_to_replace_2|g" "problem_settings/ProblemZeroParametersVMS_lev2.json"