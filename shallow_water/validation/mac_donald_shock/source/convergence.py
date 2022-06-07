import matplotlib.pyplot as plt
import sys, os
sys.path.append(os.path.join('..','..'))
from python_scripts.convergence_analysis import ConvergenceAnalysis

convergence = ConvergenceAnalysis(filename='convergence', area=10)
# convergence.AddFilter(label='label', time=1.0)
# convergence.Plot("spatial", "HEIGHT_ERROR", "EXACT_HEIGHT", marker='o')
# convergence.PrintLatexTable("HEIGHT_ERROR", "EXACT_HEIGHT")
# slope = convergence.Slope("spatial", "HEIGHT_ERROR", "EXACT_HEIGHT")
# print("slope :  ", slope)

plt.style.use('seaborn-deep')
fig, ax = plt.subplots()

convergence.AddFilter(label='rv')
convergence.Plot("spatial", "MOMENTUM_ERROR_X", "EXACT_MOMENTUM_X", ax=ax, marker='o', label='RV')

convergence.SetFilter(label='gj')
convergence.Plot("spatial", "MOMENTUM_ERROR_X", "EXACT_MOMENTUM_X", ax=ax, marker='^', label='GJV')

convergence.SetFilter(label='fc')
convergence.Plot("spatial", "MOMENTUM_ERROR_X", "EXACT_MOMENTUM_X", ax=ax, marker='s', label='FC')

fig.tight_layout()
ax.legend()
plt.show()
