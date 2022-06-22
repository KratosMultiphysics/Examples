import matplotlib.pyplot as plt
import pandas as pd

def ReadDataFrame(file_name):
    df = pd.read_csv(file_name, sep='\s+', skiprows=1, escapechar='#')
    return df

time = '1.0'

name = 'line_graph/parabola_{}.dat'.format(time)
df = ReadDataFrame(name)

fig, axes = plt.subplots(nrows=2, sharex=True, figsize=(10, 4))#, gridspec_kw={'height_ratios': [2, 3]})
plt.rcParams['lines.linewidth'] = 2
axes2 = axes[1].twinx()

df.plot(x='X', y='FREE_SURFACE_ELEVATION', ax=axes[0])
df.plot(x='X', y='EXACT_FREE_SURFACE', color='black', linewidth=1, linestyle='dashed', ax=axes[0])
df.plot(x='X', y='TOPOGRAPHY', color='black', linewidth=1, ax=axes[0])
df.plot(x='X', y='VELOCITY_X', label='VELOCITY', color='orange', ax=axes[1])
df.plot(x='X', y='EXACT_VELOCITY_X', label='EXACT_VELOCITY', color='black', linewidth=1, linestyle='dashed', ax=axes[1])
df.plot(x='X', y='MOMENTUM_X', label='DISCHARGE', color='red', ax=axes2)
df.plot(x='X', y='EXACT_MOMENTUM_X', label='EXACT_DISCHARGE', color='black', linewidth=1, linestyle='dotted', ax=axes2)

axes[0].legend()
axes[1].set_xlabel('Position $[m]$')
axes[0].set_ylabel('$[m]$')
axes[0].set_xlim([3, 7])
axes[0].set_ylim([-1.5, 4])

line1, label1 = axes[1].get_legend_handles_labels()
line2, label2 = axes2.get_legend_handles_labels()
axes[1].legend(line1 + line2, label1 + label2)
axes2.legend().remove()
axes[1].set_ylabel('Velocity $[m/s]$')
axes2.set_ylabel('Discharge $[m^2/s]$')
if time == '0.5000':
    axes[1].set_ylim([-1, 6])
    axes2.set_ylim([-.5, 3])
elif time == '1.0000':
    axes[1].set_ylim([-6, 1])
    axes2.set_ylim([-3, .5])

fig.tight_layout()
plt.show()
