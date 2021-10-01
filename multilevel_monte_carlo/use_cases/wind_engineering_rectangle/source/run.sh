#!/usr/bin/env bash

path_to_examples_folder=$(pwd)

materials_path_to_replace="problem_settings/materials_poisson_rectangle_2d.json"
materials_new_path="$path_to_examples_folder/problem_settings/materials_poisson_rectangle_2d.json"
mdpa_path_to_replace="problem_settings/RectangularCylinder2D_25k"
mdpa_new_path="$path_to_examples_folder/problem_settings/RectangularCylinder2D_25k"
avg_velocity_field_to_replace="average_velocity_field_RectangularCylinder_300.0.dat"
avg_velocity_field_new_path="$path_to_examples_folder/average_velocity_field_RectangularCylinder_300.0.dat"

# set absolute path in Kratos parameters
sed -i "s|$materials_path_to_replace|$materials_new_path|g" "problem_settings/ProjectParametersRectangularCylinder2D_Fractional.json"
sed -i "s|$mdpa_path_to_replace|$mdpa_new_path|g" "problem_settings/ProjectParametersRectangularCylinder2D_Fractional.json"
sed -i "s|$avg_velocity_field_to_replace|$avg_velocity_field_new_path|g" "problem_settings/ProjectParametersRectangularCylinder2D_Fractional.json"

runcompss \
    --lang=python \
    --python_interpreter=python3 \
    --pythonpath=$path_to_examples_folder \
    ./run_mc_Kratos.py problem_settings/parameters_xmc.json

# revert change in Kratos parameters
sed -i "s|$materials_new_path|$materials_path_to_replace|g" "problem_settings/ProjectParametersRectangularCylinder2D_Fractional.json"
sed -i "s|$mdpa_new_path|$mdpa_path_to_replace|g" "problem_settings/ProjectParametersRectangularCylinder2D_Fractional.json"
sed -i "s|$avg_velocity_field_new_path|$avg_velocity_field_to_replace|g" "problem_settings/ProjectParametersRectangularCylinder2D_Fractional.json"