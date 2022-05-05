import argparse
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import KratosMultiphysics.ShallowWaterApplication.utilities.solitary_wave_utilities as solitary_wave


parser = argparse.ArgumentParser()
parser.add_argument('-t','--time', help="time or array of times", default=[4, 8, 12], nargs='+')
parser.add_argument('--analytical',    dest='analytical', action='store_true')
parser.add_argument('--no-analytical', dest='analytical', action='store_false')
parser.set_defaults(analytical=False)
args = parser.parse_args()


amplitude = 0.1
x_shift = 0
x_end = 73
results_pattern = 'line_graph/line_graph-{:.1f}.dat'


def plot_data(data, ax, **kwargs):
    data.plot(x='x', y='f', ax=ax, **kwargs)


def read_data(file_name, reference=0, **kwargs):
    df = pd.read_csv(file_name, header=None, delimiter=r'\s+', **kwargs)
    df['f'] = df['f'] - reference
    return df


def analytical_data(time):
    coords = np.linspace(0, x_end, 200)
    w = solitary_wave.BoussinesqSolution(1.0, amplitude=amplitude)
    eta = [float(w.eta(x -x_shift, time)) for x in coords]
    df = pd.DataFrame({'x': coords, 'f': eta})
    return df


def plot_gauge(time, ax, **kwarg):

    data = read_data(results_pattern.format(time), skiprows=2, names=['x', 'y', 'z', 'f'])
    plot_data(data, ax, **kwarg)    

    if args.analytical:
        analyt = analytical_data(time)
        plot_data(analyt, ax, label='Analytical')

    ax.set_xlabel('distance [m]')
    ax.set_ylabel('amplitude [m]')
    ax.set_xlim([0, x_end])


mpl.style.use('seaborn-muted')
fig, axes = plt.subplots(figsize=(8, 3))
if hasattr(args.time, '__iter__'):
    for time in args.time:
        plot_gauge(float(time), axes, color='k', linewidth=1)
else:
    plot_gauge(float(args.time), axes)
axes.set_xlabel('')
axes.set_ylabel('')
axes.set_xticks([])
axes.set_yticks([])
axes.set_ylim([0.0001, 0.12])
axes.legend().remove()
fig.tight_layout()
plt.show()
