# Overview
This example presents the HPC workflow implemented using the [COMPSs](https://compss-doc.readthedocs.io/en/stable/) framework and the [dislib](https://dislib.readthedocs.io/en/release-0.7/) library for the training stage of a projection-based Reduced Order Model using the [RomApplication](https://github.com/KratosMultiphysics/Kratos/tree/master/applications/RomApplication) of Kratos.

# Content
* [Introducing the Workflow][presentation]
    * [Toy Example][example]
    * [The Reduced Order Model][rom]
    * [The Workflow][workflow]
    
* [Launching the example][launching]
    * [Requirements][requirements]
        * [Kratos][kratos]
        * [COMPSs][compss]
        * [dislib][dislib]        
    * [Launching in Local Machine][local]
    * [Launching in Cluster][cluster]
    * [Results][results]
    
    

[presentation]: https://github.com/KratosMultiphysics/Examples/tree/master/eFlows4HPC/ROM_workflow#introducing-the-workflow
[launching]://https://github.com/KratosMultiphysics/Examples/tree/master/eFlows4HPC/ROM_workflow#launching-the-example
[example]://https://github.com/KratosMultiphysics/Examples/tree/master/eFlows4HPC/ROM_workflow#toy-model-used
[rom]://https://github.com/KratosMultiphysics/Examples/tree/master/eFlows4HPC/ROM_workflow#the-reduced-order-model
[workflow]://https://github.com/KratosMultiphysics/Examples/tree/master/eFlows4HPC/ROM_workflow#the-workflow
[launching]://https://github.com/KratosMultiphysics/Examples/tree/master/eFlows4HPC/ROM_workflow#launching-the-example
[requirements]://https://github.com/KratosMultiphysics/Examples/tree/master/eFlows4HPC/ROM_workflow#requirements
[kratos]://https://github.com/KratosMultiphysics/Examples/tree/master/eFlows4HPC/ROM_workflow#kratos
[compss]://https://github.com/KratosMultiphysics/Examples/tree/master/eFlows4HPC/ROM_workflow#compss
[dislib]://https://github.com/KratosMultiphysics/Examples/tree/master/eFlows4HPC/ROM_workflow#dislib
[local]://https://github.com/KratosMultiphysics/Examples/tree/master/eFlows4HPC/ROM_workflow#launching-in-local-machine
[cluster]://https://github.com/KratosMultiphysics/Examples/tree/master/eFlows4HPC/ROM_workflow#launching-in-cluster
[results]://https://github.com/KratosMultiphysics/Examples/tree/master/eFlows4HPC/ROM_workflow#checking-the-results

# Introducing the Workflow

## Toy model used

This example uses a flow pass a cylinder in 2D model. For a breve description of this example check [this page](https://github.com/KratosMultiphysics/Examples/tree/master/fluid_dynamics/validation/body_fitted_cylinder_100Re)

<p align="center">
  <img src="https://github.com/KratosMultiphysics/Examples/blob/master/fluid_dynamics/validation/body_fitted_cylinder_100Re/data/body_fitted_cylinder_100Re_v.gif" alt="Body-fitted 100 Re cylinder velocity field [m/s]." style="width: 600px;"/>
</p>

## The Reduced Order Model

The goal of the ROM is to cheaply and fastly evaluate the solution for a given parameter of interest $\boldsymbol{\mu}$ (in this example, the inlet velocity of the fluid) 

<p align=center><img height="72.125%" width="72.125%" src="./data/surrogate.png"></p>

In oder to obtain such a ROM, a campain of expensive Full Order Model FOM simulations should be launched and the collected data should be analysed.




## The workflow

We have defined 5 stages of the workflow, each of which finds a one-to-one correspondance to the functions included in the file [WorkflowExample.py](https://github.com/KratosMultiphysics/Examples/blob/eFlows4HPC_M20/eFlows4HPC/ROM_workflow/WorkflowExample.py)


<p align=center><img height="72.125%" width="72.125%" src="./data/workflowcorrect.png"></p>


The parallelization of the Kratos simulations is done using [COMPSs](https://compss-doc.readthedocs.io/en/stable/)

<p align=center><img height="72.125%" width="72.125%" src="./data/simulations_parallel.png"></p>


Moreover, the fixed-rank randomized svd used in this workflow is implemented using [dislib](https://dislib.readthedocs.io/en/release-0.7/) and can be found [here](https://github.com/KratosMultiphysics/Kratos/blob/master/applications/RomApplication/python_scripts/parallel_svd.py)


# Launching the Example

## Requirements

### Kratos

This example requires the RomApplication and the FluidDynamicsApplication.

If you compiled Kratos, add both these application to the Kratos configure file. 

Linux:
```shell
add_app ${KRATOS_APP_DIR}/FluidDynamicsApplication
add_app ${KRATOS_APP_DIR}/RomApplication
```

Windows:
```shell
CALL :add_app %KRATOS_APP_DIR%/FluidDynamicsApplication
CALL :add_app %KRATOS_APP_DIR%/RomApplication
```

If on the other hand, you are using the precompiled version of Kratos, do

pip:
```shell
pip install KratosRomApplication KratosFluidDynamicsApplication
```

### COMPSs

The latest version of COMPSs can be obtained [here](https://www.bsc.es/research-and-development/software-and-apps/software-list/comp-superscalar/downloads). 

Building it in your local machine can be a bit tricky, but a docker image is also available. 

In case of doubts, or to install in a cluster, get in touch with the developers Jorge Ejarque (jorge.ejarque@bsc.es), Rosa M. Badia (rosa.m.badia@bsc.es), Support mailing list (support-compss@bsc.es).




### Dislib

The latest version of dislib can be obtained from [here](https://github.com/bsc-wdc/dislib)

Else, you can use pip

```shell
pip install dislib
```


## Launching in Local Machine

In you own computer, use the `runcompss` command to launch the workflow. 

The [WorkflowExample.py](https://github.com/KratosMultiphysics/Examples/blob/eFlows4HPC_M20/eFlows4HPC/ROM_workflow/WorkflowExample.py) expects the directory to be passed, since COMPSs works with absolute paths.

Activate tracing `-t` and graph `-g` generation flags to better analyse the results

So, in order to launch the workflow, do

```shell
runcompss --lang=python --python_interpreter=python3 -g WorkflowExample.py $PWD
```

## Launching in Cluster

In a cluster, use the `enqueue_compss` command with the appropriate flags. For example: 

```shell
enqueue_compss \
 --qos=$queue \
 -t -g \
 --log_level=info \
 --base_log_dir=${base_log_dir} \
 --worker_in_master_cpus=0 \
 --max_tasks_per_node=12 \
 --exec_time=$time_limit \
 --python_interpreter=python3 \
 --num_nodes=$num_nodes WorkflowExample.py $PWD
 ```

## Checking the results

The graph of the job allows to see the execution order of the tasks.

In this example the graph generated looks like this

<p align=center><img height="72.125%" width="72.125%" src="./data/workflow_graph.JPG"></p>

Where the coloured circles represent the following tasks

<p align=center><img height="50.125%" width="50.125%" src="./data/tasks.png"></p>


Moreover, two numpy files are obtained representing each of the two validation stages in [the workflow](https://github.com/KratosMultiphysics/Examples/tree/master/eFlows4HPC/ROM_workflow#the-workflow)

