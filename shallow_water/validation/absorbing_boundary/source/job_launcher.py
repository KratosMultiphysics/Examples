import os
import numpy as np

command_execution = 'sbatch --job-name {} run.sh'  # parallel run
#command_execution = 'python3 MainKratos.py'        # serial run

count = 0

output_base_name = 'time_series_{}long_{}damp'
relative_dampings = 10**np.linspace(-1, 2, 20)
relative_wavelengths = np.array([0.5, 0.7, 1.0, 2.0, 3.0, 5.0])

for l, rel_distance in enumerate(relative_wavelengths):
    for d, rel_damping in enumerate(relative_dampings):
        count += 1
        output_name = output_base_name.format(l, d)
        job_name = f'absorbing_boundary_{count}'
        command  = command_execution.format(job_name)
        command += f' --rel_damping {rel_damping}'
        command += f' --rel_distance {rel_distance}'
        command += f' --output_name {output_name}'
        command += f' --remove_output True'
        os.system(command=command)
