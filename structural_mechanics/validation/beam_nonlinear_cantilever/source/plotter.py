import numpy as np
import matplotlib.pyplot as plt
import KratosMultiphysics.NeuralNetworkApplication.data_loading_utilities as data_loading

input_file = 'data/training_in_raw.dat'
target_file = 'data/training_out_raw.dat'
#input_file = 'data_beam_validation/testing_in.dat'
#target_file = 'data_beam_validation/testing_out.dat'
test_input = data_loading.ImportAscii(input_file)
target = data_loading.ImportAscii(target_file)

plt.plot( test_input[:,0],target[:,0],'.')
plt.plot( test_input[:,0],target[:,1],'.')
plt.show()
