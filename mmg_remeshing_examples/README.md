# MMG remeshing Examples

This folder contains examples related to  the remeshig process implemented in *Kratos* using the *MMG* library.

## MMG Libray 
> Copyright (c) Bx INP/Inria/UBordeaux/UPMC, 2004

>  mmg is free software: you can redistribute it and/or modify it  under the terms of the GNU Lesser General Public License as published by the Free Software Foundation, either version 3 of the License, or  (at your option) any later version.

>  mmg is distributed in the hope that it will be useful, but WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.

>  You should have received a copy of the GNU Lesser General Public  License and of the GNU General Public License along with mmg (in files COPYING.LESSER and COPYING). If not, [see the license description](http://www.gnu.org/licenses/). Please read their terms carefully and  use this copy of the mmg distribution only if you accept them.

They are realized using the __MeshingApplication__ using the *MMG* library. For that pourpose download the library *MMG*:

[MMG Download](http://www.mmgtools.org/mmg-remesher-downloads)

or with:

	git clone https://github.com/MmgTools/mmg.git

Add the following to the main Kratos configure.sh: 

	-DINCLUDE_MMG=ON                                                                  \
	-DMMG_INCLUDE_DIR="installation_directory/mmg/include/"\
	-DMMG2D_INCLUDE_DIR="installation_directory/mmg/include/mmg/mmg2d/"\
	-DMMG3D_INCLUDE_DIR="installation_directory/mmg/include/mmg/mmg3d/"\
	-DMMGS_INCLUDE_DIR="installation_directory/mmg/include/mmg/mmgs/"\
	-DMMG_LIBRARY="installation_directory/mmg/lib/libmmg.a"     \
	-DMMG2D_LIBRARY="installation_directory/mmg/lib/libmmg2d.a" \
	-DMMG3D_LIBRARY="installation_directoryl_libraries/mmg/lib/libmmg3d.a" \
	-DMMGS_LIBRARY="installation_directory/mmg/lib/libmmgs.a"   \

# Examples

The Examples are continously updated and extended

## Validation

- [Hessian2D](validation/hessian2D/README.md)
- [Hessian3D](validation/hessian3D/README.md)
- [Bunny example](validation/bunny/README.md)

## Use Cases

- [Beam 2D](use_cases/beam2D/README.md)
- [Cavity 2D](use_cases/cavity2D/README.md)
- [Lamborghini example](use_cases/lamborghini/README.md)
- [Channel sphere 2D](use_cases/channel_sphere2D/README.md)



