from matplotlib.ticker import TickHelper
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
plt.style.use('seaborn')

history = "Optimization_Results"

plots = [
    {
        "name": "mass",
        "column_names": [
            "f"
        ]
    },
    {
        "name": "strain energy: main load",
        "column_names": [
            "c1: <=",
            "c1_ref",
        ]
    },
    {
        "name": "strain energy: tip load",
        "column_names": [
            "c2: <=",
            "c2_ref",
        ]
    },
    {
        "name": "packaging: bounding mesh",
        "column_names": [
            "c3: <=",
            "c3_ref",
        ]
    },
    {
        "name": "step length",
        "column_names": [
            "step_size",
            "inf_norm_s",
            "inf_norm_c",
        ]
    }
]

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


fig, axs = plt.subplots(2, 3)
axs_list = [axs[0][0], axs[0][1], axs[0][2], axs[1][0], axs[1][1]]
for plot, ax in zip(plots, axs_list):
    for column_name in plot["column_names"]:
        ax.plot(df[column_name], label=column_name)
    ax.legend()
    ax.set_title(plot["name"])"""

grid = plt.GridSpec(2, 3)
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
    ax.set_title(plot["name"], fontsize=12)
    ax.tick_params(axis='x', labelsize=12)
    ax.tick_params(axis='y', labelsize=12)
    ax.xaxis.set_major_locator(ticker.MultipleLocator(4))   # tick_spacing is 4
    if plot['name'] == 'mass':
        ax.yaxis.set_major_locator(ticker.MultipleLocator(1))

plt.tight_layout()
plt.show()
