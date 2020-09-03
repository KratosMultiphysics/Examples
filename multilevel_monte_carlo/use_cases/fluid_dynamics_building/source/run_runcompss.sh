#!/usr/bin/env bash

path_to_folder=$(pwd)
runcompss \
    --lang=python \
    --python_interpreter=python3 \
    --pythonpath=$path_to_folder \
    ./run_mc_Kratos.py problem_settings/parameters_xmc_asynchronous_mc_problemZero.json
