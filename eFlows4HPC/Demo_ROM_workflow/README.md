# Overview
This example presents the HPC workflow implemented using the [COMPSs](https://compss-doc.readthedocs.io/en/stable/) framework and the [dislib](https://dislib.readthedocs.io/en/release-0.7/) library for the training stage of a projection-based Reduced Order Model using the [RomApplication](https://github.com/KratosMultiphysics/Kratos/tree/master/applications/RomApplication) of Kratos.

# Content
* [Introducing the Workflow][presentation]
    * [Demo Model][example]
    * [The Reduced Order Model][rom]
    * [The Workflow][workflow]
    
* [Launching the example][launching]
    * [Requirements][requirements]
        * [Kratos][kratos]
        * [COMPSs][compss]
        * [dislib][dislib]
        * [EZyRB][EZyRB]       
    * [Launching in Local Machine][local]
    * [Launching in Cluster][cluster]
    * [Results][results]
    
    

[presentation]:https://github.com/KratosMultiphysics/Examples/tree/master/eFlows4HPC/Demo_ROM_workflow#introducing-the-workflow
[launching]:https://github.com/KratosMultiphysics/Examples/tree/master/eFlows4HPC/Demo_ROM_workflow#launching-the-example
[example]:https://github.com/KratosMultiphysics/Examples/tree/master/eFlows4HPC/Demo_ROM_workflow#demo-model
[rom]://https:github.com/KratosMultiphysics/Examples/tree/master/eFlows4HPC/Demo_ROM_workflow#the-reduced-order-model
[workflow]:https://github.com/KratosMultiphysics/Examples/tree/master/eFlows4HPC/Demo_ROM_workflow#the-workflow
[launching]:https://github.com/KratosMultiphysics/Examples/tree/master/eFlows4HPC/Demo_ROM_workflow#launching-the-example
[requirements]:https://github.com/KratosMultiphysics/Examples/tree/master/eFlows4HPC/Demo_ROM_workflow#requirements
[kratos]:https://github.com/KratosMultiphysics/Examples/tree/master/eFlows4HPC/Demo_ROM_workflow#kratos
[compss]:https://github.com/KratosMultiphysics/Examples/tree/master/eFlows4HPC/Demo_ROM_workflow#compss
[dislib]:https://github.com/KratosMultiphysics/Examples/tree/master/eFlows4HPC/Demo_ROM_workflow#dislib
[EZyRB]:https://github.com/KratosMultiphysics/Examples/tree/master/eFlows4HPC/Demo_ROM_workflow#ezyrb
[local]:https://github.com/KratosMultiphysics/Examples/tree/master/eFlows4HPC/Demo_ROM_workflow#launching-in-local-machine
[cluster]:https://github.com/KratosMultiphysics/Examples/tree/master/eFlows4HPC/Demo_ROM_workflow#launching-in-cluster
[results]:https://github.com/KratosMultiphysics/Examples/tree/master/eFlows4HPC/Demo_ROM_workflow#checking-the-results

# Introducing the Workflow

## Demo model

This example uses a flow pass a cylinder in 2D model. For a breve description of this example check [this page](https://github.com/KratosMultiphysics/Examples/tree/master/fluid_dynamics/validation/body_fitted_cylinder_100Re)

<p align="center">
  <img src="https://github.com/KratosMultiphysics/Examples/blob/master/eFlows4HPC/Demo_ROM_workflow/data/Animation_README.gif" alt="Temperature Field for [100000, 400] - RPM of 400 and heat flux of 100000 W/m^3." style="width: 600px;"/>
</p>

## The Reduced Order Model

The goal of the ROM is to cheaply and fastly evaluate the solution for a given parameter of interest $\boldsymbol{\mu}$ (in this example, the inlet velocity of the fluid) 

<p align=center><img height="72.125%" width="72.125%" src="./data/surrogate.png"></p>

In oder to obtain such a ROM, a campain of expensive Full Order Model FOM simulations should be launched and the collected data should be analysed.




## The workflow

We have defined 5 stages of the workflow, each of which finds a one-to-one correspondance to the functions included in the file [WorkflowExample.py](./WorkflowExample.py) 


<p align=center><img height="72.125%" width="72.125%" src="./data/Steps.png"></p>

The simulations in Kratos using the CoSimulation capabilities aim to store the outputs:
<p align=center><img height="72.125%" width="72.125%" src="./data/CoSimLogic.png"></p>

To accomplish parallelization on these simulations, Kratos simulations are done using [COMPSs](https://compss-doc.readthedocs.io/en/stable/)

<p align=center><img height="72.125%" width="72.125%" src="./data/simulations_parallel.png"></p>

And the snapshots will be gathered in dislib ([dislib](https://dislib.readthedocs.io/en/release-0.7/) and can be found [here]) arrays:
<p align=center><img height="72.125%" width="72.125%" src="./data/Snapshots_matrix.png"></p>

Moreover, a fixed-precision randomized svd (using tall and skinny QR decomposition) was used in this workflow to find the reduced basis and perform hyper-reduction. To delve into parallelization, partitioned hyper-reduction was implemented:
<p align=center><img height="72.125%" width="72.125%" src="./data/PartitionedSVD.png"></p>


# Launching the Example

## Requirements

### Kratos

This example requires the LinearSolversApplication, ConvectionDiffusionApplication, CoSimulationApplication, RomApplication, and the MappingApplication.

If you compiled Kratos, add all of these applications to the Kratos configure file. 

Linux:
```shell
add_app ${KRATOS_APP_DIR}/LinearSolversApplication
add_app ${KRATOS_APP_DIR}/ConvectionDiffusionApplication
add_app ${KRATOS_APP_DIR}/CoSimulationApplication
add_app ${KRATOS_APP_DIR}/RomApplication
add_app ${KRATOS_APP_DIR}/MappingApplication
```

Windows:
```shell
CALL :add_app %KRATOS_APP_DIR%/LinearSolversApplication
CALL :add_app %KRATOS_APP_DIR%/ConvectionDiffusionApplication
CALL :add_app %KRATOS_APP_DIR%/CoSimulationApplication
CALL :add_app %KRATOS_APP_DIR%/RomApplication
CALL :add_app %KRATOS_APP_DIR%/MappingApplication
```

If on the other hand, you are using the precompiled version of Kratos, do

pip:
```shell
pip install KratosRomApplication KratosCoSimulationApplication
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

### EZyRB

The latest version of EZyRB can be obtained from [here](https://mathlab.github.io/EZyRB/)

The official distribution is on GitHub, and you can clone the repository using
```shell
git clone https://github.com/mathLab/EZyRB
```

To install the package just type:
```shell
python setup.py install
```

## Launching in Local Machine

In you own computer, use the `runcompss` command to launch the workflow. 

The [Workflow.py](./Workflow.py) expects the directory to be passed, since COMPSs works with absolute paths.

Activate tracing `-t` and graph `-g` generation flags to better analyse the results

So, in order to launch the workflow, do

```shell
runcompss --lang=python --python_interpreter=python3 -g Workflow.py $PWD
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
 --num_nodes=$num_nodes Workflow.py $PWD
 ```

## Checking the results

The graph of the job allows to see the execution order of the tasks.

In this example the graph generated looks like this
<p align=center><img height="72.125%" width="72.125%" src="./data/GrapghColors.png"></p>
<p align=center><img height="72.125%" width="72.125%" src="./data/Grapgh.png"></p>

Where the coloured circles represent the following tasks

<p align=center><img height="50.125%" width="50.125%" src="./data/Trace.png"></p>

