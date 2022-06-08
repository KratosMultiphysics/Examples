import subprocess
import sys

automatic_time_step = True
courant_number = 0.5
modes = ['residual_viscosity','gradient_jump','flux_correction']
labels = ['rv','gj','fc']
meshes = [2.0, 1.0, 0.5, 0.2, 0.1]
steps = [0.005] * len(meshes)
steps[-1] = 0.002
input_filename_pattern = 'mac_donald_{}'

for mode, label in zip(modes, labels):
    for mesh, time_step in zip(meshes, steps):
        input_filename = input_filename_pattern.format(mesh)
        process = subprocess.Popen([
            sys.executable,
            "MainKratos2.py",
            '--automatic_time_step' + str(automatic_time_step),
            '--courant_number' + str(courant_number),
            '--time_step' + str(time_step),
            '--shock_capturing_type' + mode,
            '--input_filename' + input_filename,
            '--analysis_label' + label,
            '--remove_output_processes' + str(True)
        ])
