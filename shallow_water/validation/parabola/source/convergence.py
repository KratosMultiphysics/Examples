import matplotlib.pyplot as plt
from KratosMultiphysics.ShallowWaterApplication.benchmarks.tools.convergence_plotter import ConvergencePlotter

convergence = ConvergencePlotter(file_name='gjv/convergence', area=10)
convergence.AddFilter(time=1.0)
convergence.Plot("spatial", "HEIGHT_ERROR", "EXACT_HEIGHT", marker='o')
convergence.PrintLatexTable("HEIGHT_ERROR", "EXACT_HEIGHT")

plt.show()

# rv_convergence = ConvergencePlotter(file_name='rv/convergence', area=area)
# rv_results = rv_convergence.TimeFilter(time=time)
# rv_slope = rv_convergence.Slope("spatial", "HEIGHT_ERROR", "EXACT_HEIGHT", filter=rv_results)
# rv_convergence.Plot("spatial", "HEIGHT_ERROR", "EXACT_HEIGHT", filter=rv_results, marker='o', label='RV')

# gjv_convergence = ConvergencePlotter(file_name='gjv/convergence', area=area)
# gjv_results = gjv_convergence.TimeFilter(time=time)
# gjv_slope = gjv_convergence.Slope("spatial", "HEIGHT_ERROR", "EXACT_HEIGHT", filter=gjv_results)
# gjv_convergence.Plot("spatial", "HEIGHT_ERROR", "EXACT_HEIGHT", filter=gjv_results, marker='^', label='GJV', linestyle='dashed')

# print("slope rv:  ", rv_slope)
# print("slope gjv: ", gjv_slope)

# plt.tight_layout()
# plt.legend()
# plt.show()
