#!/bin/bash

cd only_structure
python3 SingleCNNLSTMMain.py
cd ../mok_fsi_CSM_solids_NN
python3 MainCosim.py
