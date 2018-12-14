The given case is prepared for MPI.
Depending on the computational resources available, the user may wish for a higher resolution.
To achive this, the following steps are recommended:

- Opening the project in GiD
- Refining the mesh (if possible without altering names of groups)
- Generating the new *.mdpa by starting a run of the simulation.
  The simulation can be canceled once the file was written.
- Modification of the *.mdpa file.
  The first lines should look like this:

Begin ModelPartData
//  VARIABLE_NAME value
End ModelPartData

Begin Properties 0
End Properties

Begin Properties 1
    DENSITY < value for your fluid >
    DYNAMIC_VISCOSITY < value for your fluid >
End Properties

Begin Properties 2
    DENSITY < value for your fluid >
    DYNAMIC_VISCOSITY < value for your fluid >
End Properties

Begin Nodes
    1   0.0000000000   1.0000000000   0.0000000000
    2   0.0240509017   0.9791931353   0.0320937254
	.......


Reference values:

- given case set-up: 			100.000 elements (splashes are under-represented)
- case in pictures 	  		  1.200.000 elements (splashes are well-represented)
