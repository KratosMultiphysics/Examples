#!/usr/bin/env bash

path_to_examples_folder=$(pwd)

runcompss \
    --lang=python \
    --python_interpreter=python3 \
    --pythonpath=$path_to_examples_folder/ \
    ./run_mc_Kratos.py
