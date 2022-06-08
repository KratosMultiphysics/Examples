import os

command_execution = 'sbatch --job-name {} run.sh'  # parallel run
#command_execution = 'python3 MainKratos.py'        # serial run

automatic_time_step = True
courant_number = 0.5
modes = ['residual_viscosity','gradient_jump','flux_correction']
labels = ['rv','gj','fc']
meshes = [2.0, 1.0, 0.5, 0.2, 0.1]
steps = [0.005] * len(meshes)
steps[-1] = 0.002
input_filename_pattern = 'mac_donald_{}'

count = 0
for mode, label in zip(modes, labels):
    for mesh, time_step in zip(meshes, steps):
        count += 1
        input_filename = input_filename_pattern.format(mesh)
        job_name = f'mac_donald_conv_analysis_{count}'
        command  = command_execution.format(job_name)
        command += f' --automatic_time_step {automatic_time_step}'
        command += f' --courant_number {courant_number}'
        command += f' --time_step {time_step}'
        command += f' --shock_capturing_type {mode}'
        command += f' --input_filename {input_filename}'
        command += f' --analysis_label {label}'
        command += f' --remove_output True'
        os.system(command=command)
