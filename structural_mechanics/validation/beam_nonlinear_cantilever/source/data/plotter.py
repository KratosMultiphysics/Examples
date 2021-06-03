import numpy as np
import matplotlib.pyplot as plt
import KratosMultiphysics.NeuralNetworkApplication.data_loading_utilities as data_loading

input_file = 'training_in_raw.dat'
target_file = 'training_out_raw.dat'
test_input = data_loading.ImportAscii(input_file)
target = data_loading.ImportAscii(target_file)

plt.plot( test_input[:,0],target[:],'.')
plt.show()
