import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import FormatStrFormatter

def PlotReflectionCoefficient(file_name, ax, title, **kwargs):
    df = pd.read_csv(file_name, header=None)
    c_reflection = np.array(df[0])
    rel_dampings = 10**np.linspace(-1, 1, 31)
    ax.loglog(rel_dampings, c_reflection, **kwargs)
    for axis in [ax.xaxis, ax.yaxis] : axis.set_major_formatter(FormatStrFormatter('%.1f'))
    if title:
        ax.set_title(title)

fig, axes = plt.subplots()#nrows=2, ncols=2, sharex=True, sharey=True, gridspec_kw={'height_ratios': [3, 2]})
title = ''
label = r'$^d/_\lambda={:.1f}$'
name = 'reflection_coefficient_{:.1f}.dat'

PlotReflectionCoefficient(name.format(1.0), axes, title, label=label.format(1.0), marker='^')
PlotReflectionCoefficient(name.format(1.5), axes, title, label=label.format(1.5), marker='o')
PlotReflectionCoefficient(name.format(2.0), axes, title, label=label.format(2.0), marker='v')
PlotReflectionCoefficient(name.format(4.0), axes, title, label=label.format(4.0), marker='s')

plt.xlabel(r'Relative absorption $\gamma/\omega$')
plt.ylabel(r'Reflection coefficient')
plt.legend()
plt.tight_layout()
plt.show()
