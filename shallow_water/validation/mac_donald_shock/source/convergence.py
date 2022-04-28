import numpy as np
import h5py as h5
import matplotlib.pyplot as plt

'''possible variables:
    FREE_SURFACE
    MOMENTUM
'''
variable = 'MOMENTUM'
titles = {'MOMENTUM':'Discharge', 'FREE_SURFACE':'Free surface'}

file_name = 'convergence.hdf5'
f = h5.File(file_name)

ds = f["analysis_000"]

num_elems = ds["num_elems"]
if variable == 'FREE_SURFACE':
    error_L2 = ds["FREE_SURFACE_ERROR"]
    value_L2 = ds["EXACT_FREE_SURFACE"]
elif variable == 'MOMENTUM':
    error_L2 = ds["MOMENTUM_ERROR_X"]
    value_L2 = ds["EXACT_MOMENTUM_X"]
else:
    raise Exception('unknown variable name')
meshes = np.sqrt(2*10 / num_elems)
labels = ds["label"]
filter = [label == b'all  ' for label in labels]

plt.figure(figsize=(5,4.5))
plt.loglog(meshes[filter], np.divide(error_L2[filter], value_L2[filter]), marker='o')
plt.xlabel('mesh size, $\log(h)$')
plt.ylabel('relative error norm, $\log(L_2)$')
plt.title(titles[variable])
plt.tight_layout()
plt.show()
