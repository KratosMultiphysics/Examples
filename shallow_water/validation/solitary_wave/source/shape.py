import matplotlib.pyplot as plt
import KratosMultiphysics.ShallowWaterApplication.utilities.solitary_wave_utilities as solitary_wave
import gauges


results_pattern = '{:02.0f}/gauges/gauge_{}.dat'


def plot_gauge(ax, amplitude):
    gauge_id = 2
    coord = gauges.coordinates_map[gauge_id]
    w = solitary_wave.BoussinesqSolution(1.0, amplitude=amplitude)
    c = w.phase_speed
    k = w.wavenumber
    data_a = gauges.read_data(results_pattern.format(10*amplitude, gauge_id), skiprows=2, names=['t', 'h', 'u', 'v', 'w'])
    ax.plot(k*(coord - c*data_a['t']), data_a['h'], label=f"{coord:>3}m")

    gauge_id = 3
    coord = gauges.coordinates_map[gauge_id]
    w = solitary_wave.BoussinesqSolution(1.0, amplitude=amplitude)
    c = w.phase_speed
    k = w.wavenumber
    data_b = gauges.read_data(results_pattern.format(10*amplitude, gauge_id), skiprows=2, names=['t', 'h', 'u', 'v', 'w'])
    ax.plot(k*(coord - c*data_b['t']), data_b['h'], label=f"{coord:>3}m")

    analyt = gauges.analytical_data(coord, amplitude)
    ax.plot(k*(coord - c*analyt['t']), analyt['h'], label="Analytical", color='k', linewidth=1, dashes=[3,6])

    ax.set_xlabel('$k(x-ct)$')
    ax.set_ylabel('$\eta/H$ [m]')


if __name__ == '__main__':
    plt.style.use('seaborn-muted')
    fig, axes = plt.subplots(3, sharex=True, figsize=(6, 4.5))
    ids = range(3)
    amplitudes = [0.1, 0.2, 0.3]
    for i, amplitude in enumerate(amplitudes):
        plot_gauge(axes[i], amplitude)
        axes[i].set_xlim([-4, 4])
        axes[i].set_ylim([-0.04, 0.34])
    axes[0].legend()
    fig.tight_layout()
    plt.show()
