#!/bin/bash

cd mok_fsi_CFM_fluids_original
python3 MainCoSim.py
cd ../only_fluid
python3 MainKratos.py
cd ../mok_fsi_CFM_fluid_NN
python3 MainCoSim.py
