import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path


class ConvergenceAnalysis:
    '''Tool for plotting convergence graphs.
    
    The source data shall be stored in text file and
    must follow the format of ConvergenceOutputProcess.
    '''

    def __init__(self, filename, area=1.0):
        '''Construct the plotter, read the file and initialize the variables.

        Parameters
        ----------
        file_name : str
            The file name without extension
        area : float
            The area of the domain. It is used to compute the average element size
        '''
        # Read the file
        self.data = self._ReadData(filename)

        # General data
        self.data['elem_size'] = np.sqrt(area / self.data["num_elems"])

        # Initialize the filter
        self.filter = self._TrueFilter()


    def SetFilter(self, *, label=None, time=None):
        '''Override the current filter.'''
        self.filter = self._TrueFilter()
        self.AddFilter(label=label, time=time)


    def AddFilter(self, *, label=None, time=None):
        '''Merge the current filter with the new conditions.'''
        if label is not None:
            label_filter = self.data["label"] == label
            self._AppendFilter(label_filter)
        if time is not None:
            time_filter = abs(self.data["time"] - time) < self.data['time_step']
            self._AppendFilter(time_filter)


    def Plot(self, convergence, variable, ref_variable=None, ax=None, set_labels=True, **kwargs):
        '''Add a plot to the given axes.

        Parameters
        ----------
        convergence : str
            'spatial' or 'temporal'
        variable : str
            The name of the error variable to plot
        ref_variable : str
            If it is specified, the variable will be scaled to it. Optional
        ax : Axes
            An axes instance. Optional
        set_labels : bool
            Add labels to the plot. Optional
        kwargs
            Other arguments to pass to the plot
        '''
        # Get the data
        error, increments = self._GetData(convergence, variable, ref_variable)

        # Generate the figure
        if ax is None:
            ax = plt.gca()
        if len(error) > 0:
            ax.loglog(increments, error, **kwargs)
            if set_labels:
                self._SetLabels(convergence, ax)
        else:
            print("[WARNING]: There is no data to plot")
        return ax


    def Slope(self, convergence, variable, ref_variable=None):
        '''Get the average convergence slope.

        Parameters
        ----------
        convergence : str
            'spatial' or 'temporal'
        variable : str
            The name of the error variable to compute the convergence slope
        ref_variable : str
            If it is specified, the variable will be scaled to it

        Returns
        -------
        float 
            The convergence slope
        '''
        # Get the data
        error, increments = self._GetData(convergence, variable, ref_variable)

        # Compute the slope
        if len(error) > 0:
            slopes = []
            for i in range(len(increments)-1):
                d_incr = increments[i] / increments[i+1]
                d_err = error[i] / error[i+1]
                slopes.append(d_err / d_incr)
        return sum(slopes) / len(slopes)


    def PrintLatexTable(self, variable, ref_variable=None):
        '''Print to screen the contents of a LaTeX tabular.

        Parameters
        ----------
        variable : str
            The name of the error variable to include in the tabular
        ref_variable : str
            If it is specified, the variable will be scaled to it
        '''

        # Get the data
        num_nodes = self.data[self.filter]['num_nodes']
        elem_sizes = self.data[self.filter]['elem_size']
        time_steps = self.data[self.filter]['time_step']
        error = self.data[self.filter][variable]
        if ref_variable is not None:
            error /= self.data[self.filter][ref_variable]

        # Print the LaTeX table
        if len(error) > 0:
            header = '$n_{nodes}$ & $\\Delta x$ & $\\Delta t$ & $e_r$ \\\\ \\hline'
            row = '{:,} & {:.2} & {:.1} & {:.2} \\\\'
            print(header)
            for num, dx, dt, err in zip(num_nodes, elem_sizes, time_steps, error):
                print(row.format(num, dx, dt, err))
        else:
            print("[WARNING]: There is no data to generate the table")


    @staticmethod
    def _ReadData(filename):
        path = Path(filename).with_suffix('.dat')
        df = pd.read_csv(path, delimiter=r'\s+|\t+|\s+\t+|\t+\s+', skiprows=1, engine='python')
        df.columns = df.columns.str.replace('#','')
        return df


    def _GetData(self, convergence, variable, ref_variable):
        increment_names = {
            'spatial'  : 'elem_size',
            'temporal' : 'time_step'
        }
        error = self.data[variable]
        if ref_variable is not None:
            error /= self.data[ref_variable]
        increments = self.data[increment_names[convergence]]
        return error[self.filter], increments[self.filter]


    def _SetLabels(self, convergence, ax):
        label_names = {
            'spatial'  : 'mesh size, $\log(\Delta x)$',
            'temporal' : 'time step, $\log(\Delta t)$'
        }
        x_label = label_names[convergence]
        y_label = 'rel error norm, $\log(L_2)$'
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)


    def _AppendFilter(self, new_filter):
        self.filter = [a and b for a, b in zip(new_filter, self.filter)]


    def _TrueFilter(self):
        return [True] * len(self.data)


if __name__ == '__main__':
    convergence = ConvergenceAnalysis(filename='convergence', area=10)
    # convergence.AddFilter(label='label', time=1.0)
    # convergence.Plot("spatial", "HEIGHT_ERROR", "EXACT_HEIGHT", marker='o', label='GJV')
    # convergence.PrintLatexTable("HEIGHT_ERROR", "EXACT_HEIGHT")
    # slope = convergence.Slope("spatial", "HEIGHT_ERROR", "EXACT_HEIGHT")
    # print("slope :  ", slope)

    fig, ax = plt.subplots()

    convergence.AddFilter(label='rv', time=1.0)
    convergence.Plot("spatial", "HEIGHT_ERROR", "EXACT_HEIGHT", ax=ax, marker='o', label='RV')

    convergence.SetFilter(label='gj', time=1.0)
    convergence.Plot("spatial", "HEIGHT_ERROR", "EXACT_HEIGHT", ax=ax, marker='^', label='GJV')

    convergence.SetFilter(label='fc', time=1.0)
    convergence.Plot("spatial", "HEIGHT_ERROR", "EXACT_HEIGHT", ax=ax, marker='s', label='FC')

    fig.tight_layout()
    ax.legend()
    plt.show()