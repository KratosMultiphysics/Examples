import matplotlib.pyplot as plt

X, Y = [], []

with open('sdof_solver//results_sdof.dat', 'r') as file:
  reader = file.readlines()
  for line in reader[1:]:
    values = [float(s) for s in line.split()]
    X.append(values[0])
    Y.append(values[1])

plt.plot(X, Y,'-')
plt.xlabel('Time [s]')
plt.ylabel('Displacement [m]')
plt.show()
plt.figsave('sdof_training_data.png')
