#!/bin/bash
cd mok_fsi_CSM_solids_original
python3 MainCoSim.py
cd ../only_structure
python3 SingleCNNLSTMMain.py
cd ../mok_fsi_CSM_solids_NN
python3 MainCosim.py
