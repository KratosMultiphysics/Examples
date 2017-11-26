# Poromechanics Examples

TODO

## How to run the examples

There are essentially two ways of running any example of the Poromechanics Application: using python from the terminal, and using the GUI from GiD.

**Run the example from the terminal**

*Linux/macOS*

Open a terminal, go to the folder of the case and type:

>
    python3 MainKratos.py

*Windows*

First create a "run.bat" file to run the case. It should contain the path of the installed Kratos libs and the order to run the python script. If Kratos is installed in C:

> set PATH=C:\\KratosInstall;C:\\KratosInstall\\libs;%PATH%

> C:\\KratosInstall\\runkratos MainKratos.py

After that, open a Windows command line, go to the folder of the case and call the "run.bat" file to run the case:

>
    run.bat

**Run the example from GiD**

In this case we will run the example using a GUI from the pre and post processing software GiD.

TODO