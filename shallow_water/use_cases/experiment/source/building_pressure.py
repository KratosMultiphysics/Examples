import matplotlib as mpl
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

"""This file plots a set of graphs generated from GiD.

The expected filenames are the following:
    - /building_2.grf
    - /building_5.grf
    - /building_10.grf
    - /building_15.grf
"""

file_name_pattern = 'results_2021_08_25/building_{}.grf'
colors = plt.cm.coolwarm(np.linspace(0.1, 0.9, 4))

i_plot = 0

def plot_building(time, ax, *, title='$t={}s$'):
    # Defining the plot counter as global
    global i_plot

    # Read the numerical results and the image of the gauge position
    results_file_name = file_name_pattern.format(time)
    res = pd.read_csv(results_file_name, header=None, skiprows=2, delimiter=r'\s+', names=['x', 'h'])

    # Clean the input
    res = res[:-1]
    res['x'] = pd.to_numeric(res['x'])
    res['h'] = pd.to_numeric(res['h'])

    # Write the right coordinates
    res['x'] += 3.0

    # Split the series front and behind the building
    left = res.loc[res['x'] < 3.8]
    right = res.loc[res['x'] > 3.8]

    # Plot the results
    left.plot(x='x', y='h', color=colors[i_plot], ax=ax, label=title.format(time))
    right.plot(x='x', y='h', color=colors[i_plot], ax=ax, label='')

    i_plot += 1


fig, axes = plt.subplots()

for t in [2, 5, 10, 15]:
    plot_building(t, axes)

axes.fill_between([3.59, 4.00], 0, 0.2, color='gray', alpha=.3)
axes.set_xlabel('$x$ coordinate [m]')
axes.set_ylabel('depth [m]')
axes.set_title('Cut along the building at $y=0.2m$')
axes.legend()
plt.show()
