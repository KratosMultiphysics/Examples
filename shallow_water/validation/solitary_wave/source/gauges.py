import argparse
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import KratosMultiphysics.ShallowWaterApplication.utilities.solitary_wave_utilities as solitary_wave


parser = argparse.ArgumentParser()
parser.add_argument('-g','--gauge_id', help="from 1 to 3 or all", default='all')
parser.add_argument('-a','--analytical', help="plot the analytical solution", default=True, type=bool)
parser.add_argument('-p','--path', help="the path to the files", default="gauges", type=str)


amplitude = 0.1
end_time = 60
results_pattern = '{}/gauge_{}.dat'
coordinates_map = {
    1 : 20,
    2 : 50,
    3 : 150  # If non flat bottom, the analytical solution won't be valid since shoaling is present.
}


def plot_data(data, ax, **kwargs):
    data.plot(x='t', y='h', ax=ax, **kwargs)


def read_data(file_name, reference=0, **kwargs):
    df = pd.read_csv(file_name, header=None, delimiter=r'\s+', **kwargs)
    df['h'] = df['h'] - reference
    return df


def analytical_data(x, amplitude):
    t = np.linspace(0, end_time, 500)
    w = solitary_wave.BoussinesqSolution(1.0, amplitude=amplitude)
    h = [float(w.eta(x, time)) for time in t]
    df = pd.DataFrame({'t': t, 'h': h})
    return df


def plot_gauge(gauge_id, ax, path):
    coord = coordinates_map[gauge_id]

    data = read_data(results_pattern.format(path, gauge_id), skiprows=2, names=['t', 'h', 'u', 'v', 'w'])
    plot_data(data, ax, label="Numerical")    

    if args.analytical:
        analyt = analytical_data(coord, amplitude)
        plot_data(analyt, ax, label='Analytical', color='k', linewidth=1, dashes=[3,6])

    ax.set_title('Gauge at x={}m'.format(coord))
    ax.set_xlabel('Time [s]')
    ax.set_ylabel('Amplitude [m]')
    ax.set_xlim([0, end_time])


if __name__ == '__main__':
    plt.style.use('seaborn-muted')
    args = parser.parse_args()
    if args.gauge_id == 'all':
        fig, axes = plt.subplots(3, sharex=True)
        for i in range(3):
            plot_gauge(i+1, axes[i], args.path)
            axes[i].legend().remove()
        axes[0].legend()
    else:
        fig, axes = plt.subplots()
        plot_gauge(int(args.gauge_id), axes, args.path)
    fig.tight_layout()
    plt.show()
