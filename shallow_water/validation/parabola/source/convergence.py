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

convergence.AddFilter(label='rv_fic', time=1.0)
convergence.Plot("spatial", "HEIGHT_ERROR", "EXACT_HEIGHT", ax=ax, marker='o', label='RV')

convergence.SetFilter(label='gj_fic', time=1.0)
convergence.Plot("spatial", "HEIGHT_ERROR", "EXACT_HEIGHT", ax=ax, marker='^', label='GJV')

convergence.SetFilter(label='fc_fic', time=1.0)
convergence.Plot("spatial", "HEIGHT_ERROR", "EXACT_HEIGHT", ax=ax, marker='s', label='FC')

# convergence.SetFilter(label='rv_none', time=1.0)
# convergence.Plot("spatial", "HEIGHT_ERROR", "EXACT_HEIGHT", ax=ax, marker='o', label='RV w/o stab', color='C0', linestyle='--')

convergence.SetFilter(label='gj_none', time=1.0)
convergence.Plot("spatial", "HEIGHT_ERROR", "EXACT_HEIGHT", ax=ax, marker='^', label='GJV w/o stab', color='C1', linestyle='--', alpha=.5)

convergence.SetFilter(label='fc_none', time=1.0)
convergence.Plot("spatial", "HEIGHT_ERROR", "EXACT_HEIGHT", ax=ax, marker='s', label='FC w/o stab', color='C2', linestyle='--', alpha=.5)

fig.tight_layout()
ax.legend()
plt.show()
