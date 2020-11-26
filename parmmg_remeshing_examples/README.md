# ParMmg remeshing Examples

This folders contains MPI parallel examples using *Kratos* and *ParMMG*.

They are built using the __MeshingApplication__ using the *ParMMG* library. For that purpose download the library *ParMMG*:

	git clone https://github.com/MmgTools/ParMmg

And follow their install guide.

To compile *Kratos* with *ParMMG*, add the following variable in your *Kratos* configure.sh file:
	
	-DINCLUDE_PMMG=ON
	-DPMMG_ROOT=/path/to/parmmg/build/

The path to *MMG* will also be required:

	-DINCLUDE_MMG=ON
	-DMMG_ROOT=/path/to/mmg/build/
## Use Cases

- [Body-fitted cylinder hessian 3D](use_cases/body_fitted_hessian_cylinder3D/README.md)
- [Embedded building level-set 3D](use_cases/embedded_level_set_building3D/README.md)
