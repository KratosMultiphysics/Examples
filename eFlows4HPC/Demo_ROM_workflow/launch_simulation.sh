export PYTHONPATH=$PWD:/gpfs/projects/bsc19/threadpoolctl:$PYTHONPATH
export OMP_NUM_THREADS=8
#### python was here...
num_nodes=5
###module load dlb

worker_working_dir=$PWD/raul_runs/nodes${num_nodes/}/worker
master_working_dir=$PWD/raul_runs/nodes${num_nodes/}
base_log_dir=$PWD/raul_runs
remove_worker=true
mkdir -p ${master_working_dir}
mkdir -p ${worker_working_dir}

export ComputingUnits=8
export LANGUAGE=en_GB.utf8
export LC_ALL=en_GB.utf8

source /home/bsc44/bsc44531/Kratos_M30_Master/scripts/Kratos_env.sh


module load dislib/master
module load python/3.9.10
## its here now


#queue=debug
queue=bsc_cs
#queue=class_a
time_limit=60*16

# -g -t \
# --constraints=highmem  \
# --scheduler=es.bsc.compss.scheduler.fifodatalocation.FIFODataLocationScheduler
#  --cpu_affinity="dlb"   \

enqueue_compss \
 --qos=$queue \
 -t -g \
 --log_level=info \
 --base_log_dir=${base_log_dir} \
 --worker_in_master_cpus=0 \
 --max_tasks_per_node=2 \
 --exec_time=$time_limit \
 --python_interpreter=python3 \
 --job_name="workflow_without_flag" \
 --num_nodes=$num_nodes Workflow.py $PWD $ComputingUnits


