import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
plt.style.use('seaborn')

history = "Optimization_Results"

plot = {
    "name": "strain energy",
    "column_name": "f"
}

path = f"{history}/optimization_log.csv"

df = pd.read_csv(path, delimiter=",")
df.columns = [x.strip() for x in df.columns]

fig, ax = plt.subplots(1, 1, figsize=(4, 6))
ax.plot(df[plot["column_name"]], label=plot["column_name"])
ax.legend(fontsize=11)
ax.set_title(plot["name"], fontsize=13)
ax.tick_params(axis='x', labelsize=13)
ax.tick_params(axis='y', labelsize=13)
ax.yaxis.set_major_locator(ticker.MultipleLocator(0.001))   # tick_spacing
ax.xaxis.set_major_locator(ticker.MultipleLocator(10))   # tick_spacing

plt.show()
