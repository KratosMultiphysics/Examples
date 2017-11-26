# Poromechanics Examples

All the examples shown here use the following applications of Kratos:

* ExternalSolversApplication
* FluidDynamicsApplication
* PoromechanicsApplication
* SolidMechanicsApplication

## How to run the examples

There are two different ways for running an example of the Poromechanics Application: using python from the terminal, and using the GUI from GiD.

**Run the example from the terminal**

*Linux/macOS*

Open a terminal, go to the source folder of the case and type:

>
    python3 MainKratos.py

*Windows*

First create a "run.bat" file inside the source folder of the example. It should contain the path of the installed Kratos libs and the order to run the python script. If Kratos is installed in C:

> set PATH=C:\\KratosInstall;C:\\KratosInstall\\libs;%PATH%

> C:\\KratosInstall\\runkratos MainKratos.py

After that, open a Windows command line, go to the source folder of the case and call the "run.bat" file to run the case:

>
    run.bat

**Run the example from GiD**

Ona can also run any example using a GUI based on the "problemtype" modules of GiD [https://www.gidhome.com](https://www.gidhome.com).

First copy the folder [Poromechanics_Application.gid](https://github.com/KratosMultiphysics/Kratos/tree/master/applications/PoromechanicsApplication/custom_problemtype) inside the problemtype folder of GiD.

After that, copy all source files of the example inside a new folder named "_example\_name_.gid".

Open the latter folder from GiD and you will be able to modify the boundary conditions, the properties, or the solver settings of the example, mesh the geometry and run the case.