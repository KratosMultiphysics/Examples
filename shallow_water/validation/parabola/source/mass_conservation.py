import argparse
import matplotlib.pyplot as plt
import pandas as pd

parser = argparse.ArgumentParser()
parser.add_argument("-p", "--path", type=str, default="mass_conservation")
args = parser.parse_args()

def ReadDataFrame(file_name):
    df = pd.read_csv(file_name, sep='\s+', skiprows=1)
    df.columns = df.columns.str.replace('#', '')
    return df

def PrintTotalMassConservation(ax, identifier="", label=""):
    file_name = args.path + '/total_mass' + identifier + '.dat'
    df = ReadDataFrame(file_name)
    initial_mass = df['Mass'][0]
    df['Mass'] -= initial_mass
    df['Mass'] /= initial_mass
    df.plot(x='Time', y='Mass', ax=ax, label='Total mass' + label, color='k')

def PrintWetMassConservation(ax, identifier="", label=""):
    file_name = args.path + '/wet_mass' + identifier + '.dat'
    df = ReadDataFrame(file_name)
    initial_mass = df['Mass'][0]
    df['Mass'] -= initial_mass
    df['Mass'] /= initial_mass
    df.plot(x='Time', y='Mass', ax=ax, label='Wet mass' + label)

def PrintMassConservation(ax, identifier="", label=""):
    PrintTotalMassConservation(ax, identifier, label)
    PrintWetMassConservation(ax, identifier, label)

fig, axes = plt.subplots(figsize=(7,3))
PrintMassConservation(axes)
# PrintTotalMassConservation(axes, '_rv', ' RV, GJV, FC')
# PrintWetMassConservation(axes, '_rv', ' RV')
# PrintWetMassConservation(axes, '_gj', ' GJV')
# PrintWetMassConservation(axes, '_fc', ' Fc')
axes.legend()
axes.set_xlabel('Time $[s]$')
axes.set_ylabel('Relative mass variation')
fig.tight_layout()
plt.show()
