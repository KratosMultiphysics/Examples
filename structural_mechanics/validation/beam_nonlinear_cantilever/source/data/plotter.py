import matplotlib.pyplot as plt
import numpy as np
import KratosMultiphysics.NeuralNetworkApplication.data_loading_utilities as data_loading

input_file = 'training_in_raw.dat'
target_file = 'training_out_raw.dat'
val_input_file = 'testing_in_raw.dat'
val_target_file = 'testing_out_raw.dat'

test_input = data_loading.ImportAscii(input_file)

target = data_loading.ImportAscii(target_file)

val_test_input = data_loading.ImportAscii(val_input_file)

val_target = data_loading.ImportAscii(val_target_file)


plt.plot( abs(target[:,0])/2.0,abs(test_input[:,0]),'.', label="training_x")
plt.plot( abs(val_target[:,0]/2.0),abs(val_test_input[:,0]),'.', label = "testing_x")
plt.plot( abs(target[:,1])/2.0,abs(test_input[:,0]),'.', label="training_y")
plt.plot( abs(val_target[:,1]/2.0),abs(val_test_input[:,0]),'.', label = "testing_y")
plt.legend()
plt.show()

