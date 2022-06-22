import matplotlib.pyplot as plt
import pandas as pd

time = 0.5

name = '0.2/shock_200.0050.dat'

def ReadDataFrame(file_name):
    df = pd.read_csv(file_name, sep='\s+', skiprows=1, escapechar='#')
    return df

df = ReadDataFrame(name)

fig, axes = plt.subplots(nrows=2, sharex=True, gridspec_kw={'height_ratios': [3, 2]})
plt.rcParams['lines.linewidth'] = 2

df.plot(x='X', y='FREE_SURFACE_ELEVATION', ax=axes[0])
df.plot(x='X', y='EXACT_FREE_SURFACE', ax=axes[0], linewidth=1, color='black', linestyle='dashed')
df.plot(x='X', y='TOPOGRAPHY', ax=axes[0], linewidth=1, color='black', linestyle='solid')
df.plot(x='X', y='MOMENTUM_X', label='DISCHARGE', ax=axes[1], color='red')

axes[0].set_ylabel('$[m]$')
axes[1].set_ylabel('$[m^2/s]$')
axes[1].set_xlabel('Position $[m]$')

axes[0].set_xlim([0, 100])
axes[1].set_ylim([1.7, 2.3])

fig.set_size_inches(10, 6, forward=True)
fig.tight_layout()
plt.show()
