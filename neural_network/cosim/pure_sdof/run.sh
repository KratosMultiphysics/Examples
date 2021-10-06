#!/bin/bash

cd data_generation
python3 MainCoSim.py
cd ..
python3 ModifyData.py
cd neural_network_training
python3 ConvMainKratos.py
cd ../FSI
python3 MainKratos.py
python3 Plot.py
