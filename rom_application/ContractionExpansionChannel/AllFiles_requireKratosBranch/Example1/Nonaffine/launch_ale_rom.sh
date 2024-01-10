#!/bin/sh
#SBATCH -N 1      # nodes requested
#SBATCH -n 1      # tasks requested
#SBATCH -c 16     # cores requested
#SBATCH -t 20:00:00  # time requested in hour:minute:second
##### --constraint='highmem'


export OMP_NUM_THREADS=16
export PROBLEMS_PATH=$PWD/ProblemFiles
export LANGUAGE=en_GB.utf8
export LC_ALL=en_GB.utf8


FOM=True  #(storing results)
FOM_test=True #(storing results)
Run_ROM=True #3 (storing results)
ROM_test=True #4 =  (storing results)
Train_HROM_Step1=True #5 = (creating projected residuals matrices {Sr_i}_i=1^k (one per basis))
Train_HROM_Step2=True #6 = ontain a reduced set of elements and weights starting from the projected residuals matrices Sr_i
Run_HROM=True #7 = RunHROM Train Trajectory
HROM_test=True #8 = RunHROM Test Trajectory

plot_partial_hysteresis=False

#parameters used in Local POD:

# parameters for the simulations
Launch_Simulation=1
Number_Of_Clusters=1 #not used in global POD
svd_truncation_tolerance_list=(1e-3 1e-4 1e-5 1e-6)
clustering="narrowing"  #time #
overlapping=30
residuals_svd_truncation_tolerance_list=(1e-3 1e-4 1e-5 1e-6)
residuals_svd_relative_to_global_residuals_snapshots=1


if [ $FOM = True ]
    then
    #### LAUNCH FOM TRAIN TRAJECTORY ####
    # MASTER
    source /gpfs/projects/bsc44/bsc44011/KratosInstallations/KratosMaster/Kratos/scripts/Kratos_env.sh
    echo "\n\n\n\n\n\nLauching FOM \n\n\n\n\n\n"
    python3 ProblemFiles/FOM.py $PWD
fi
if [ $FOM_test = True ]
    then
    # NEW MASTER
    source /gpfs/projects/bsc44/bsc44011/KratosInstallations/KratosMaster/Kratos/scripts/Kratos_env.sh
    echo "\n\n\n\n\n\nLaunching FOM test trajectory \n\n\n\n\n\n"
    python3 ProblemFiles/FOM_TestTrajectory.py $PWD
fi
for j in ${svd_truncation_tolerance_list[@]}
do
    svd_truncation_tolerance=$j
    if [ $Run_ROM = True ]
        then
            source /gpfs/projects/bsc44/bsc44011/KratosInstallations/UpdatedKratosALE/Kratos_POD_ALE/Kratos/scripts/Kratos_env.sh
            echo "\n\n\n\n\n\nLaunching ROM \n\n\n\n\n\n"
            python3 ProblemFiles/Run_ROM.py $Launch_Simulation $Number_Of_Clusters $svd_truncation_tolerance $clustering $overlapping $PWD
    fi
    if [ $ROM_test = True ]
        then
        #### LAUNCH ROM TEST TRAJECTORY ####
            source /gpfs/projects/bsc44/bsc44011/KratosInstallations/UpdatedKratosALE/Kratos_POD_ALE/Kratos/scripts/Kratos_env.sh
            echo '\n\n\n\nlaunching ROM test\n\n\n\n'
            python3 ProblemFiles/ROM_TestTrajectory.py $Launch_Simulation $Number_Of_Clusters $svd_truncation_tolerance $clustering $overlapping $PWD
    fi
    if [ $Train_HROM_Step1 = True  ]
        then
        #### TrainHROM (Creating Matrix of projected resduals Sr)  ####
            source /gpfs/projects/bsc44/bsc44011/KratosInstallations/UpdatedKratosALE/Kratos_POD_ALE/Kratos/scripts/Kratos_env.sh
            echo '\n\n\n\n\nlaunching TrainHROM train\n\n\n\n\n\n'
            python3 ProblemFiles/TrainHROM_Step1.py $Launch_Simulation $Number_Of_Clusters $svd_truncation_tolerance $clustering $overlapping $PWD
    fi
    for k in ${residuals_svd_truncation_tolerance_list[@]}
    do
        residuals_svd_truncation_tolerance=$k
        if [ $Train_HROM_Step2 = True ]
            then
            ### Obtain Reduced Elements and Weights  ####
                source /gpfs/projects/bsc44/bsc44011/KratosInstallations/UpdatedKratosALE/Kratos_POD_ALE/Kratos/scripts/Kratos_env.sh
                echo '\n\n\n\n\n\nlaunching HROM elements and Weights\n\n\n\n\n\n'
                python3 ProblemFiles/TrainHROM_Step2.py $Launch_Simulation $Number_Of_Clusters $svd_truncation_tolerance $clustering $overlapping $PWD $residuals_svd_truncation_tolerance $residuals_svd_relative_to_global_residuals_snapshots
        fi
        if [ $Run_HROM = True ]
            then
            #### LAUNCH HROM TRAIN TRAJECTORY ####
                source /gpfs/projects/bsc44/bsc44011/KratosInstallations/UpdatedKratosALE/Kratos_POD_ALE/Kratos/scripts/Kratos_env.sh
                echo '\n\n\n\n\n\nLaunching HROM train\n\n\n\n\n\n\n'
                python3 ProblemFiles/Run_HROM.py $Launch_Simulation $Number_Of_Clusters $svd_truncation_tolerance $clustering $overlapping $PWD $residuals_svd_truncation_tolerance  $residuals_svd_relative_to_global_residuals_snapshots
        fi
        if [ $HROM_test = True ]
            then
            #### LAUNCH HROM TEST TRAJECTORY ####
                source /gpfs/projects/bsc44/bsc44011/KratosInstallations/UpdatedKratosALE/Kratos_POD_ALE/Kratos/scripts/Kratos_env.sh
                echo 'Launching HROM test'
                python3 ProblemFiles/HROM_TestTrajectory.py $Launch_Simulation $Number_Of_Clusters $svd_truncation_tolerance $clustering $overlapping $PWD $residuals_svd_truncation_tolerance  $residuals_svd_relative_to_global_residuals_snapshots
        fi
    done
done

