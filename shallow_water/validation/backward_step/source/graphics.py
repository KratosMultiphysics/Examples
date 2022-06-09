import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import sys
sys.path.append('/graphics/')

time = 0.5

def ReadDataFrame(file_name):
    df = pd.read_csv(file_name, sep='\s+', skiprows=1, escapechar="#")
    return df

times = [0.3, 0.6, 0.9, 1.2, 1.5, 1.8, 2.1, 2.4, 2.7, 3.0]
# times = [3.3, 3.6, 3.9, 4.2, 4.5, 4.8, 5.1, 5.4, 5.7, 6.0]

name = 'graphics/output_file_{}.dat'
df = []
for t in times:
    df.append(ReadDataFrame(name.format(t)))

fig, ax = plt.subplots()
mpl.rc('lines', linewidth=2)
mpl.rc('image', cmap='bone')
colors = plt.cm.coolwarm(np.linspace(0.1, 0.9, len(times)))

ax.plot([5,5], [-0.003,0.025], color='lightgray', linewidth=5)

for i in range(0, len(times)):
    c = colors[i]
    l = '$t={}$'.format(times[i])
    df[i].plot(x='X', y='FREE_SURFACE_ELEVATION', ax=ax, color=c, label=l)

ax.legend(bbox_to_anchor=(1.15, 1.05))
ax.set_xlabel('Position $[m]$')
ax.set_ylabel('$[m]$')

fig.set_size_inches(10, 3, forward=True)
fig.tight_layout()
plt.show()
