#!/usr/bin/env bash

# commented commands
# -g -t \

runcompss \
    -g \
    --lang=python \
    --python_interpreter=python3 \
    --pythonpath=/home/riccardo/src/exaqute-applications/xMC_compressible_potential_flow \
    ./run_mlmc_Kratos.py problem_settings/parameters_xmc_asynchronous_mlmc_potentialFlow.json
