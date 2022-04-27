import argparse
import matplotlib.pyplot as plt
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--path", type=str, default=".")
args = parser.parse_args()

def ReadDataFrame(file_name):
    df = pd.read_csv(file_name, sep='\s+', skiprows=1)
    df.columns = df.columns.str.replace('[#,@,&]', '', regex=True)
    return df

file_name_total = args.path + '/total_mass.dat'
file_name_wet = args.path + '/wet_mass.dat'

df1 = ReadDataFrame(file_name_total)
df2 = ReadDataFrame(file_name_wet)

end_time = df1['Time'][len(df1['Time'])-1]
initial_mass = df1['Mass'][0]
df1['Mass'] -= initial_mass
df1['Mass'] /= initial_mass
df2['Mass'] -= initial_mass
df2['Mass'] /= initial_mass

fig, axes = plt.subplots()

df1.plot(x='Time', y='Mass', ax=axes, label='Total mass', color='k')
df2.plot(x='Time', y='Mass', ax=axes, label='Wet mass', color='tab:blue')

axes.legend()
axes.set_xlabel('Time $[s]$')
axes.set_ylabel('Relative mass error')
axes.set_xlim([0, end_time])
axes.set_ylim([-0.01, 0.005])

fig.set_size_inches(7, 3, forward=True)
fig.tight_layout()
plt.show()
