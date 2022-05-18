import argparse
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt
import matplotlib.ticker as tck


parser = argparse.ArgumentParser()
mode = parser.add_mutually_exclusive_group()
mode.add_argument("-s", "--compute_single", action="store_const", dest="mode", const="compute_single", default="compute_single")
mode.add_argument("-m", "--compute_matrix", action="store_const", dest="mode", const="compute_matrix")
mode.add_argument("-p", "--print_matrix",   action="store_const", dest="mode", const="print_matrix")
args = parser.parse_args()


def read_data(filename):
    df = pd.read_csv(filename, header=None, delimiter=r'\s+', skiprows=2, names=['t', 'f', 'u', 'v', 'w'])
    return df


def filter_harmonics(time, values):
    long_harmonics = sm.nonparametric.lowess(values, time, frac=0.05)
    long_harmonics = long_harmonics[:,1]
    filtered_values = values - long_harmonics
    return filtered_values


def remove_non_consecutive_indices_single(indices):
    acceptable_indices = [False] * len(indices)
    for i in range(1,len(indices)-1):
        if indices[i-1] > 0 and indices[i] > 0 and indices[i+1] > 0:
            acceptable_indices[i] = True
    return acceptable_indices


def remove_non_consecutive_indices(indices, times=1):
    for i in range(times):
        indices = remove_non_consecutive_indices_single(indices)
    return indices


def flip_range(indices):
    return [not index for index in indices]


def get_incident_and_reflected_ranges(amplitudes, velocities):
    reflected_range = amplitudes*velocities < 0
    incident_range  = flip_range(reflected_range)
    incident_range  = remove_non_consecutive_indices(incident_range,  4)
    reflected_range = flip_range(incident_range)
    reflected_range = remove_non_consecutive_indices(reflected_range, 8)
    incident_range  = flip_range(reflected_range)
    return incident_range, reflected_range


def compute_reflection_coefficient(filename, print_on_screen=False, make_plot=False):
    data = read_data(filename)
    timeseries = data['t']
    amplitudes = data['f']
    velocities = data['u']
    amplitudes = filter_harmonics(timeseries, amplitudes)
    velocities = filter_harmonics(timeseries, velocities)
    incident_range, reflected_range = get_incident_and_reflected_ranges(amplitudes, velocities)

    incident_amplitudes = amplitudes * incident_range
    incident_amplitude = max(incident_amplitudes) - min(incident_amplitudes)

    reflected_amplitudes = amplitudes * reflected_range
    reflected_amplitude = max(reflected_amplitudes) - min(reflected_amplitudes)

    reflection_coefficient = reflected_amplitude / incident_amplitude

    if print_on_screen:
        print('reflected amplitude', reflected_amplitude)
        print('incident amplitudes', incident_amplitude)
        print('reflection coefficient', )

    if make_plot:
        ax0 = plt.subplot(511)
        plt.plot(timeseries, amplitudes)
        plt.subplot(512, sharex=ax0)
        plt.plot(timeseries, velocities)
        plt.subplot(513, sharex=ax0)
        plt.plot(timeseries, reflected_range)
        plt.subplot(514, sharex=ax0)
        plt.plot(timeseries, reflected_amplitudes)
        plt.subplot(515, sharex=ax0)
        plt.plot(timeseries, incident_amplitudes)
        plt.show()

    return reflection_coefficient

if args.mode == 'compute_single':
    compute_reflection_coefficient('reflection_coefficient/time_series_1.dat', True, True)

elif args.mode == 'compute_matrix':
    base_filename_1 = 'reflection_coefficient/time_series_{}long_{}damp_1.dat'
    base_filename_2 = 'reflection_coefficient/time_series_{}long_{}damp_1.dat'

    relative_dampings = 10**np.linspace(-.5, 1, 15)
    relative_wavelengths = np.array([0.5, 0.7, 1.0, 2.0, 3.0, 5.0])

    coefficients = np.zeros(shape=(len(relative_wavelengths), len(relative_dampings)), dtype=float)

    for l, rel_dist in enumerate(relative_wavelengths):
        for d, rel_damping in enumerate(relative_dampings):

            filename_1 = base_filename_1.format(l, d)
            filename_2 = base_filename_2.format(l, d)

            coeff_1 = compute_reflection_coefficient(filename_1)
            coeff_2 = compute_reflection_coefficient(filename_2)

            coefficients[l,d] = max(coeff_1, coeff_2)

    np.savetxt('coefficients_matrix.dat', coefficients)

elif args.mode == 'print_matrix':
    coefficients = np.loadtxt('coefficients_matrix.dat')
    relative_dampings = 10**np.linspace(-.5, 1, 15)
    relative_wavelengths = np.array([0.5, 0.7, 1.0, 2.0, 3.0, 5.0])
    x, y = np.meshgrid(relative_dampings, relative_wavelengths)

    fig, ax = plt.subplots()#subplot_kw={"projection": "3d"})
    surf = ax.contourf(x, y, coefficients, locator=tck.LogLocator(), cmap=plt.get_cmap('coolwarm'))
    lines = ax.contour(surf, linewidths=0, colors='ghostwhite')

    cbar = fig.colorbar(surf)
    cbar.add_lines(lines)

    ax.set_xlabel('relative damping')
    ax.set_ylabel('relative length')
    plt.show()
