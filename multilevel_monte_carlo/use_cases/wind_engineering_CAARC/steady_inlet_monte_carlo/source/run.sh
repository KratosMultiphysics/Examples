#!/usr/bin/env bash

path_to_examples_folder=$(pwd)

materials_path_to_replace="materials/materials_Re_119M.json"
materials_new_path="$path_to_examples_folder/materials/materials_Re_119M.json"
mdpa_path_to_replace="problem_settings/CAARC_3d_combinedPressureVelocity_312k"
mdpa_new_path="$path_to_examples_folder/problem_settings/CAARC_3d_combinedPressureVelocity_312k"
avg_velocity_field_to_replace="average_velocity_field_CAARC_3d_combinedPressureVelocity_312k_690.0.dat"
avg_velocity_field_new_path="$path_to_examples_folder/average_velocity_field_CAARC_3d_combinedPressureVelocity_312k_690.0.dat"
materials_poisson_path_to_replace="problem_settings/materials_Poisson.json"
materials_poisson_new_path="$path_to_examples_folder/problem_settings/materials_Poisson.json"

# set absolute path in Kratos parameters
sed -i "s|$materials_path_to_replace|$materials_new_path|g" "problem_settings/ProjectParametersCAARC_MC_steadyInlet.json"
sed -i "s|$mdpa_path_to_replace|$mdpa_new_path|g" "problem_settings/ProjectParametersCAARC_MC_steadyInlet.json"
sed -i "s|$avg_velocity_field_to_replace|$avg_velocity_field_new_path|g" "problem_settings/ProjectParametersCAARC_MC_steadyInlet.json"
sed -i "s|$materials_poisson_path_to_replace|$materials_poisson_new_path|g" "problem_settings/ProjectParametersCAARC_MC_steadyInlet.json"

runcompss \
    --lang=python \
    --python_interpreter=python3 \
    --pythonpath=$path_to_examples_folder \
    ./run_mc_Kratos.py problem_settings/parameters_xmc.json

# revert change in Kratos parameters
sed -i "s|$materials_new_path|$materials_path_to_replace|g" "problem_settings/ProjectParametersCAARC_MC_steadyInlet.json"
sed -i "s|$mdpa_new_path|$mdpa_path_to_replace|g" "problem_settings/ProjectParametersCAARC_MC_steadyInlet.json"
sed -i "s|$avg_velocity_field_new_path|$avg_velocity_field_to_replace|g" "problem_settings/ProjectParametersCAARC_MC_steadyInlet.json"
sed -i "s|$materials_poisson_new_path|$materials_poisson_path_to_replace|g" "problem_settings/ProjectParametersCAARC_MC_steadyInlet.json"