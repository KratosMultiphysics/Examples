import argparse
import numpy as np
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
import KratosMultiphysics.ShallowWaterApplication.utilities.solitary_wave_utilities as solitary_wave


parser = argparse.ArgumentParser()
parser.add_argument('-g','--gauge_id', help="from 1 to 3", default=2, type=int)
parser.add_argument('-a','--analytical', help="plot the analytical solution", default=True, type=bool)
args = parser.parse_args()

amplitude = 0.1
x_shift = 0
end_time = 20
results_pattern = 'gauges/gauge_{}.dat'

coordinates_map = {
    1 : 20,
    2 : 50,
    3 : 150  # Non flat bottom. Here the analytical solution is not valid since shoaling is present.
}


def plot_data(data, ax, **kwargs):
    data.plot(x='t', y='h', ax=ax, **kwargs)


def read_data(file_name, reference=0, **kwargs):
    df = pd.read_csv(file_name, header=None, delimiter=r'\s+', **kwargs)
    df['h'] = df['h'] - reference
    return df


def analytical_data(x):
    t = np.linspace(0, end_time, 200)
    w = solitary_wave.BoussinesqSolution(1.0, amplitude=amplitude)
    h = [float(w.eta(x -x_shift, time)) for time in t]
    df = pd.DataFrame({'t': t, 'h': h})
    return df


def plot_gauge(gauge_id, ax):
    coord = coordinates_map[gauge_id]

    data = read_data(results_pattern.format(gauge_id), skiprows=2, names=['t', 'h', 'u', 'v', 'w'])
    plot_data(data, ax, label="numerical")    

    if args.analytical:
        analyt = analytical_data(coord)
        plot_data(analyt, ax, label='analytical')

    ax.set_title('recording at x={}m'.format(coord))
    ax.set_xlabel('time [s]')
    ax.set_ylabel('amplitude [m]')
    ax.set_xlim([0, end_time])


mpl.style.use('seaborn-muted')
fig, axes = plt.subplots()
plot_gauge(args.gauge_id, axes)
fig.tight_layout()
plt.show()
