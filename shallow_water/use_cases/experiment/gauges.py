import argparse
import matplotlib.pyplot as plt
import pandas as pd
from math import floor

parser = argparse.ArgumentParser()
parser.add_argument('-p','--path', help="path to the gauges files", default=".", type= str)
parser.add_argument('-v','--variable', help="'height' (default) or 'velocity'", default="height", type=str)
parser.add_argument('-g','--gauge_num', help="'all' (default) or [1-6]", default="all")
args = parser.parse_args()

reference_file_name_pattern = 'data/building_gauges_{}.txt'
results_file_name_pattern = args.path + '/gauge_{}.dat'
image_file_name_pattern = 'data/gauge_{}.png'

def row(i):
    return floor(i/2)

def col(i):
    return i % 2

def set_xlabel(i):
    if row(i) == 2:
        return True
    else:
        return False

def set_ylabel(i):
    if col(i) == 0:
        return True
    else:
        return False

def plot_gauge(id, var, ref, ax, *, title='Gauge {}', legend_pos=None, inset_img=True, inset_pos=[0.62, 0.6, 0.4, 0.35], set_xlabel=True, set_ylabel=True):
    # Read the numerical results and the image of the gauge position
    results_file_name = results_file_name_pattern.format(id)
    res = pd.read_csv(results_file_name, header=None, skiprows=2, delimiter=r'\s+', names=['time', 'h', 'u', 'v', 'w'])
    arr_img = plt.imread(image_file_name_pattern.format(id))

    # Put the image of the gauge position
    if inset_img:
        ax_in = ax.inset_axes(inset_pos) # relative position, relative size
        ax_in.imshow(arr_img)
        ax_in.set_axis_off()

    # Plot the results and reference values
    res.plot(x='time', y=var, label='Numerical', ax=ax)
    ref.plot(x='time', y='G{}_{}'.format(id, var), label='Experiment', color='k', linewidth=.5, ax=ax)

    # Set the given legend, title and labels
    ax.set_title(title.format(id))
    if legend_pos is not None:
        ax.legend(loc=legend_pos)
    else:
        ax.legend().remove()

    if set_xlabel:
        ax.set_xlabel('time [s]')
    if set_ylabel:
        if var == 'h':
            ax.set_ylabel('depth [m]')
        elif var == 'u':
            ax.set_ylabel('velocity [m/s]')

if args.variable == 'height':
    # Read the reference data
    reference_file_name = reference_file_name_pattern.format('h')
    ref = pd.read_csv(reference_file_name, header=None, skiprows=2, delimiter=r'\s+', names=['time','G1_h','G2_h','G3_h','G4_h','G5_h','G6_h'])

    if args.gauge_num == 'all':
        fig, axes = plt.subplots(nrows=3, ncols=2, sharex=True, sharey=False)

        for i in range(6):
            id = i + 1
            ax = axes[row(i), col(i)]
            plot_gauge(id, 'h', ref, ax, legend_pos=None, set_ylabel=set_ylabel(i))
            ax.set_ylim([-.01,.21])

        # The 6th gauge has a different format
        ax.set_ylim([-.01,.41])
        ax.legend(loc='lower left')

        fig.set_size_inches(7, 7, forward=True)
        fig.tight_layout()
        plt.show()

    else:
        fig, axes = plt.subplots()
        plot_gauge(args.gauge_num, 'h', ref, axes)
        fig.tight_layout()
        plt.show()

elif args.variable == 'velocity':
    if args.gauge_num == 'all':
        raise Exception('It is not possible to print all the gauges for the velocity at the same time.')
    else:
        reference_file_name = reference_file_name_pattern.format('uv')
        ref = pd.read_csv(reference_file_name, header=None, skiprows=2, delimiter=r'\s+', names=['time','G1_u','G1_v','G2_u','G2_v','G3_u','G3_v','G4_u','G4_v','G5_u','G5_v','G6_u','G6_v'])
        fig, axes = plt.subplots(ncols=2)
        plot_gauge(args.gauge_num, 'u', ref, axes[0], title=r'Gauge {} $u_1$')
        plot_gauge(args.gauge_num, 'v', ref, axes[1], title=r'Gauge {} $u_2$', inset_img=False, legend_pos='best')
        fig.set_size_inches(7, 2.5, forward=True)
        fig.tight_layout()
        plt.show()

else:
    parser.print_help()
