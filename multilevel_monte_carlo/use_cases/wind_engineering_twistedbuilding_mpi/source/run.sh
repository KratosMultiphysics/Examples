export EXAQUTE_BACKEND=pycompss
export OMP_NUM_THREADS=1;
export computing_units_mlmc_execute_0=1;
export computing_procs_mlmc_execute_0=4;

mpirun -n 4 python3 run_mc_Kratos.py problem_settings/parameters_xmc.json
#runcompss \
#    --lang=python \
#    --cpu_affinity="disabled" \
#    --python_interpreter=python3 \
#    ./run_mc_Kratos.py problem_settings/parameters_xmc.json
