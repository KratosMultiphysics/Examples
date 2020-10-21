# DEM Application Examples

[<img
  src="main_data/swimming_dem2.png?raw=true"
  width="400"
  title="Angle of repose test. DEMs rising.">
](main_data/swimming_dem2.png)

## Applications used

For the DEM-only examples, the only application that must be active is:

* DEMApplication

Nevertheless, when using the Swimming DEM application, the following applications must be also added:

* ExternalSolversApplication
* FluidDynamicsApplication
* IncompressibleFluidApplication
* SwimmingDEMApplication

## Use cases

Every use case in the DEM Application is composed of a folder containing all the necessary files to run the simulation. Some of the files are used by the GiD GUI and some others by Kratos. The most important ones are the following:

* KratosDEMAnalysis.py or KratosSwimmingDEMAnalysis.py: they are the main scripts of the examples. We call them using python to run the simulations.
* _example\_name_.mdpa: it contains the information about the _modelpart_. It lists the material properties, nodes, elements, conditions and _submodelparts_.
* ProjectParametersDEM.json: it includes the main parameters of the example such as time steps, solver types, list of variables to print, etc.

## How to run the examples

*Linux*

Open a terminal, go to the folder of the case and type:

>
    python3 KratosDEMAnalysis.py

or

>
    python3 KratosSwimmingDEMAnalysis.py


*Windows*

First create a "run.bat" file inside the example folder. It should contain the path of the installed Kratos libs and the order to run the python script. If Kratos is installed in C:

> set PATH=C:\\KratosInstall;C:\\KratosInstall\\libs;%PATH%
>
> C:\\KratosInstall\\runkratos KratosDEMAnalysis.py

or

> set PATH=C:\\KratosInstall;C:\\KratosInstall\\libs;%PATH%
>
> C:\\KratosInstall\\runkratos KratosSwimmingDEMAnalysis.py

After that, open a Windows command line, go to the problem folder launch the "run.bat" file to run the simulation:

>
    run.bat

