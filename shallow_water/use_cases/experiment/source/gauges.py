import matplotlib.pyplot as plt
import pandas as pd
import argparse
from math import floor


parser = argparse.ArgumentParser()
parser.add_argument('-p','--path', nargs='+', help="list of paths to the gauges files", default=["."])
parser.add_argument('-l','--label', nargs='+', help="the label for each plot")
parser.add_argument('-v','--variable', help="'height' (default) or 'velocity'", default="height", type=str)
parser.add_argument('-g','--gauge_id', help="'all' (default) or [1-6]", default="all")


class gauges:
    reference_file_name_pattern = '../data/building_gauges_{}.txt'
    results_file_name_pattern = '/gauge_{}.dat'
    image_file_name_pattern = '../data/gauge_{}.png'

    @staticmethod
    def row(i):
        return floor(i/2)

    @staticmethod
    def col(i):
        return i % 2

    def set_ylabel(self, i):
        if self.col(i) == 0:
            return True
        else:
            return False

    def plot_reference(self, ax, gauge_id, var, **kwargs):
        if var == 'h':
            var_key = 'h'
            var_names = ['time','G1_h','G2_h','G3_h','G4_h','G5_h','G6_h']
        elif var == 'u1' or 'u2':
            var_key = 'uv'
            var_names = ['time','G1_u1','G1_u2','G2_u1','G2_u2','G3_u1','G3_u2','G4_u1','G4_u2','G5_u1','G5_u2','G6_u1','G6_u2']
        else:
            raise Exception(f'Unknown var "{var}". Possible options are "h", "u1" or "u2".')

        reference_file_name = self.reference_file_name_pattern.format(var_key)
        ref = pd.read_csv(reference_file_name, header=None, skiprows=2, delimiter=r'\s+', names=var_names)
        ref.plot(x='time', y='G{}_{}'.format(gauge_id, var), ax=ax, **kwargs)

    def plot_results(self, ax, gauge_id, var, path='', **kwargs):
        results_file_name = path + self.results_file_name_pattern.format(gauge_id)
        res = pd.read_csv(results_file_name, header=None, skiprows=2, delimiter=r'\s+', names=['time', 'h', 'u1', 'u2', 'u3'])
        res.plot(x='time', y=var, ax=ax, **kwargs)

    def plot_image(self, ax, gauge_id, inset_pos=[0.62, 0.6, 0.4, 0.35]):
        arr_img = plt.imread(self.image_file_name_pattern.format(gauge_id))
        ax_in = ax.inset_axes(inset_pos) # relative position, relative size
        ax_in.imshow(arr_img)
        ax_in.set_axis_off()

    def plot_gauge(self, ax, gauge_id, var, path_list, label_list):
        for path, label in zip(path_list, label_list):
            self.plot_results(ax, gauge_id, var, path, label=label)
        self.plot_reference(ax, gauge_id, var, label='Exper.', color='k', linewidth=.5)

    def set_layout(self, ax, gauge_id, var, index=0):
        if var == 'h' or var == 'u1':
            self.plot_image(ax, gauge_id)

        if self.set_ylabel(index):
            if var == 'h':
                ax.set_ylabel('depth [m]')
            elif var == 'u1':
                ax.set_ylabel('velocity [m/s]')
        ax.set_xlabel('time [s]')

        if var == 'h' and index == 5:
            ax.legend(loc='lower left')
        elif var == 'u2':
            ax.legend()
        else:
            ax.legend().remove()

        if var == 'h':
            ax.set_title(f'Gauge {gauge_id}')
        elif var == 'u1':
            ax.set_title(f'Gauge {gauge_id} $u_1$')
        elif var == 'u2':
            ax.set_title(f'Gauge {gauge_id} $u_2$')

        if var == 'h':
            if index < 5:
                ax.set_ylim([-.01, .21])
            else:
                ax.set_ylim([-.01, .41])


    def plot(self, gauge_id, variable, path_list, labels_list):
        if variable == 'height':
            if gauge_id == 'all':
                fig, axes = plt.subplots(nrows=3, ncols=2, sharex=True, sharey=False, figsize=(7, 7))

                for i in range(6):
                    id = i + 1
                    ax = axes[self.row(i), self.col(i)]
                    self.plot_gauge(ax, id, 'h', path_list, labels_list)
                    self.set_layout(ax, id, 'h', i)

            else:
                fig, axes = plt.subplots()
                self.plot_gauge(axes, gauge_id, 'h', path_list, labels_list)
                self.set_layout(axes, gauge_id, 'h')

        elif variable == 'velocity':
            if gauge_id == 'all':
                raise Exception('It is not possible to print all the gauges for the velocity at the same time.')
            else:
                fig, axes = plt.subplots(ncols=2, figsize=(7, 2.5))
                self.plot_gauge(axes[0], gauge_id, 'u1', path_list, labels_list)
                self.plot_gauge(axes[1], gauge_id, 'u2', path_list, labels_list)
                self.set_layout(axes[0], gauge_id, 'u1')
                self.set_layout(axes[1], gauge_id, 'u2')

        fig.tight_layout()
        plt.show()


args = parser.parse_args()
if not args.label:
    labels = [path.upper() for path in args.path]
else:
    labels = args.label
gauges().plot(args.gauge_id, args.variable, args.path, labels)
