import os
import numpy as np

#command_execution = 'sbatch --job-name {} run.sh'  # parallel run
command_execution = 'python3 MainKratos.py'        # serial run

count = 0

stab_factors = [0, 0.01]
stab_labels = ['none', 'fic']
modes = ['residual_viscosity','gradient_jump','flux_correction']
labels = ['rv','gj','fc']
meshes = [0.25, 0.1, 0.05, 0.03, 0.01]
steps = [0.002] * len(meshes)
steps[-1] = 0.0005
input_filename_pattern = 'rectangle_{}'
output_filename_pattern = 'convergence_{}'

for stab, stab_label in zip(stab_factors, stab_labels):
    for mode, label in zip(modes, labels):
        for mesh, step in zip(meshes, steps):
            count += 1
            input_filename = input_filename_pattern.format(mesh)
            output_filename = output_filename_pattern.format(count)
            full_label = label + '_' + stab_label
            job_name = f'absorbing_boundary_{count}'
            command  = command_execution.format(job_name)
            command += f' --input_filename {input_filename}'
            command += f' --output_filename {output_filename}'
            command += f' --analysis_label {full_label}'
            command += f' --remove_output True'
            os.system(command=command)
