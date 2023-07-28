# Poromechanics Examples

[<img
  src="https://github.com/KratosMultiphysics/Examples/blob/master/poromechanics/validation/undrained_soil_column_2D/data/height-pressure.png?raw=true"
  width="350"
  title="Undrained soil column 2D test.">
](https://github.com/KratosMultiphysics/Examples/tree/master/poromechanics/validation/undrained_soil_column_2D/)
[<img
  src="https://github.com/KratosMultiphysics/Examples/blob/master/poromechanics/use_cases/fluid_pumping_2D/data/intersec_pw.png?raw=true"
  width="450"
  title="Fluid flow in pre-existing fractures network.">
](https://github.com/KratosMultiphysics/Examples/tree/master/poromechanics/use_cases/fluid_pumping_2D/)

## Applications used

All the examples shown here use the following applications of Kratos:

* LinearSolversApplication
* FluidDynamicsApplication
* StructuralMechanicsApplication
* PoromechanicsApplication

## Source files

Any example of the Poromechanics Application has a source folder containing all the necessary files to run the case. Some of the files are used by the GUI of GiD and others are used by Kratos. The most important ones are the following:

* MainKratos.py: is the main script of the example. We call it from python to run the case.
* _example\_name_.mdpa: contains information of the _modelpart_. Lists the material properties of conditions, the nodes, the elements, the conditions and the _submodelparts_.
* ProjectParameters.json: saves the parameters of the example such as the dimension, the time step or the linear solver, and also lists the processes used in the example.
* PoroMaterials.json: Lists the material properties of elements.


## How to run the examples

There are two different ways for running an example of the Poromechanics Application: using python from the terminal, and using the GUI from GiD.

**Run the example from the terminal**

*Linux/macOS*

Open a terminal, go to the source folder of the case and type:

>
    python3 MainKratos.py

*Windows*

Open a terminal, go to the source folder of the case and type:

>
    python MainKratos.py