import matplotlib.pyplot as plt
import numpy as np

with open("fsi_sdof/fsi_sdof_cfd_results_disp.dat",'r') as file:
    values = np.genfromtxt(file)

with open("fsi_sdof_cfd_results_disp_ref.dat",'r') as file:
    values_ref = np.genfromtxt(file)

plt.plot(values[:200,0], values[:200,2],'-',label = 'Neural network')
plt.plot(values_ref[:200,0], values_ref[:200,2], '-',label = 'Structural solver')
plt.xlabel('Time [s]')
plt.ylabel('Reaction force [N]')
plt.legend()
plt.savefig("force.png")
plt.clf()
plt.plot(values[:200,0], values[:200,1],'-', label = 'Neural network')
plt.plot(values_ref[:200,0], values_ref[:200,1],'-', label = 'Structural solver')
plt.xlabel('Time [s]')
plt.ylabel('Mesh displacement [m]')
plt.legend()
plt.savefig("disp.png")
