from matplotlib.ticker import TickHelper
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
plt.style.use('seaborn')

history = "Optimization_Results_3.0"

plot = {
    "name": "strain energy",
    "column_name": "f"
}


path = f"{history}/optimization_log.csv"

df = pd.read_csv(path, delimiter=",")
df.columns = [x.strip() for x in df.columns]

"""
fig, axs = plt.subplots(1, len(plots), figsize=(18, 6))

for plot, ax in zip(plots, axs):
    for column_name in plot["column_names"]:
        ax.plot(df[column_name], label=column_name)
    ax.legend()
    ax.set_title(plot["name"])
"""

fig, ax = plt.subplots(1, 1, figsize=(4, 6))
ax.plot(df[plot["column_name"]], label=plot["column_name"])
ax.legend(fontsize=11)
ax.set_title(plot["name"], fontsize=13)
ax.tick_params(axis='x', labelsize=13)
ax.tick_params(axis='y', labelsize=13)
ax.yaxis.set_major_locator(ticker.MultipleLocator(0.5))   # tick_spacing
ax.xaxis.set_major_locator(ticker.MultipleLocator(10))   # tick_spacing

"""grid = plt.GridSpec(2, 3)
plot_f = plt.subplot(grid[:, 0])
plot_c1 = plt.subplot(grid[0, 1])
plot_c2 = plt.subplot(grid[0, 2])
plot_c3 = plt.subplot(grid[1, 1])
plot_stp = plt.subplot(grid[1, 2])
axs_list = [plot_f, plot_c1, plot_c2, plot_c3, plot_stp]
for plot, ax in zip(plots, axs_list):
    for column_name in plot["column_names"]:
        ax.plot(df[column_name], label=column_name)
    ax.legend(fontsize=11)
    ax.set_title(plot["name"], fontsize=13)
    ax.tick_params(axis='x', labelsize=13)
    ax.tick_params(axis='y', labelsize=13)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(4))   # tick_spacing is 4
    if plot['name'] == 'mass':
        ax.yaxis.set_major_locator(ticker.MultipleLocator(1))
plt.tight_layout()
"""
plt.show()
