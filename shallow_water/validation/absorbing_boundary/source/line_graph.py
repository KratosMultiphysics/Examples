import matplotlib.pyplot as plt
import pandas as pd
import numpy as np


time = 60
distance = 10

rel_damp = 2.0
start = 70
end = 100

file_name = f'line_graph/absorbing_boundary_{time}.dat'

def ReadDataFrame(file_name):
    df = pd.read_csv(file_name, sep='\s+', skiprows=2, names=['x', 'y', 'z', 'f', 'u', 'v', 'w'])
    df['b'] = df['x'].apply(AbsorbingCoefficient)
    return df

def AbsorbingCoefficient(position):
    boundary_start = end - distance
    if position > boundary_start:
        smooth_function = np.expm1(((position - boundary_start)/(distance))**3) / np.expm1(1.0)
    else:
        smooth_function = 0.0
    return rel_damp * smooth_function


df = ReadDataFrame(file_name)


fig, axes = plt.subplots(nrows=2, sharex=True, figsize=(8, 4))
axes0 = axes[0].twinx()
axes1 = axes[1].twinx()
axes[0].set_zorder(axes0.get_zorder()+1) # bring the axes front
axes[1].set_zorder(axes1.get_zorder()+1) # bring the axes front
axes[0].patch.set_visible(False)         # set the background transparent
axes[1].patch.set_visible(False)         # set the background transparent


# plot the data
df.plot(x='x', y='f', label='Amplitude', ax=axes[0])
df.plot(x='x', y='u', label='Velocity',  ax=axes[1], color='red')
axes0.axvspan(end - distance, end, color='gainsboro')
axes1.axvspan(end - distance, end, color='gainsboro')
axes0.axhline(0, color='gray')
axes1.axhline(0, color='gray')
df.plot(x='x', y='b', label='Damping coefficient', ax=axes1, color='black')


# set the labels and limits
axes[0].set_ylabel('Amplitude $[m]$')
axes[1].set_ylabel('Velocity $[m/s]$')
axes[1].set_xlabel('Distance $[m]$')
axes[1].set_xlim([start, end])
axes0.get_yaxis().set_visible(False)
axes0.set_ylim([-rel_damp, rel_damp])
axes1.set_ylim([-rel_damp, rel_damp])


# merge the legends
line1, label1 = axes[1].get_legend_handles_labels()
line2, label2 = axes1.get_legend_handles_labels()
axes[1].legend(line1 + line2, label1 + label2)
axes1.legend().remove()

fig.tight_layout()
plt.show()
