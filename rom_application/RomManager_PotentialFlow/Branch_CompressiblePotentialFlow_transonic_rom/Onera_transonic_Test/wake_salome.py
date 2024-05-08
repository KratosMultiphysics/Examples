#!/usr/bin/env python

###
### This file is generated automatically by SALOME v9.10.0 with dump python functionality
###

import os
import numpy as np
import sys
import salome # type: ignore

salome.salome_init()
study = salome.myStudy
import salome_notebook # type: ignore
notebook = salome_notebook.NoteBook()

Wing_angle              = 0.0

Wake_angles             = np.loadtxt('wake_angles.dat', usecols=(0,))

Wake_length             = 3.0
Wake_max_mesh_size      = 1.0
Wake_min_mesh_size      = 0.01
TE_Wing_mesh_size       = 0.01

Dir                     = os.getcwd()
onera_geometry_igs_path = Dir + "/onera_m6_geometry/Onera_M6_geometry.igs"

if not os.path.exists(f'{Dir}/SalomeFiles'):
  os.mkdir(f'{Dir}/SalomeFiles')

###
### GEOM component
###

import GEOM # type: ignore
from salome.geom import geomBuilder # type: ignore
import math
import SALOMEDS # type: ignore

for Wake_angle in Wake_angles:

    Wake_output_name = f'{Dir}/SalomeFiles/Wake_{Wake_angle}.stl'

    geompy = geomBuilder.New()

    O = geompy.MakeVertex(0, 0, 0)
    OX = geompy.MakeVectorDXDYDZ(1, 0, 0)
    OY = geompy.MakeVectorDXDYDZ(0, 1, 0)
    OZ = geompy.MakeVectorDXDYDZ(0, 0, 1)
    onera_geometry = geompy.ImportIGES(onera_geometry_igs_path)
    geompy.Rotate(onera_geometry, OY, Wing_angle*math.pi/180.0)
    TE_wing_base = geompy.CreateGroup(onera_geometry, geompy.ShapeType["EDGE"])
    geompy.UnionIDs(TE_wing_base, [16])
    wake_base = geompy.MakePrismDXDYDZ(TE_wing_base, Wake_length, 0, 0)
    aux_wake_base = geompy.MakePrismDXDYDZ(TE_wing_base, -0.1, 0, 0)
    geompy.Rotate(wake_base, TE_wing_base, Wake_angle*math.pi/180.0)
    geompy.Rotate(aux_wake_base, TE_wing_base, -Wing_angle*math.pi/180.0)
    wake_aux = geompy.MakeFuseList([wake_base, aux_wake_base], True, True)
    Left_Boundary = geompy.CreateGroup(wake_aux, geompy.ShapeType["EDGE"])
    geompy.UnionIDs(Left_Boundary, [7, 16])
    Right_Boundary = geompy.CreateGroup(wake_aux, geompy.ShapeType["EDGE"])
    geompy.UnionIDs(Right_Boundary, [4])
    Extrusion_Left = geompy.MakePrismDXDYDZ(Left_Boundary, 0, -0.1, 0)
    Extrusion_Right = geompy.MakePrismDXDYDZ(Right_Boundary, 0, 0.1, 0)
    wake = geompy.MakeFuseList([wake_aux, Extrusion_Left, Extrusion_Right], True, True)

    geompy.addToStudy( O, 'O' )
    geompy.addToStudy( OX, 'OX' )
    geompy.addToStudy( OY, 'OY' )
    geompy.addToStudy( OZ, 'OZ' )
    geompy.addToStudy( onera_geometry, 'onera_geometry' )
    geompy.addToStudyInFather( onera_geometry, TE_wing_base, 'TE_wing_base' )
    geompy.addToStudy( wake_base, 'wake_base' )
    geompy.addToStudy( aux_wake_base, 'aux_wake_base' )
    geompy.addToStudy( wake_aux, 'wake_aux' )
    geompy.addToStudyInFather( wake_aux, Left_Boundary, 'Left_Boundary' )
    geompy.addToStudyInFather( wake_aux, Right_Boundary, 'Right_Boundary' )
    geompy.addToStudy( Extrusion_Left, 'Extrusion_Left' )
    geompy.addToStudy( Extrusion_Right, 'Extrusion_Right' )
    geompy.addToStudy( wake, 'wake' )

    ###
    ### SMESH component
    ###

    import  SMESH, SALOMEDS # type: ignore
    from salome.smesh import smeshBuilder # type: ignore

    smesh = smeshBuilder.New()
    #smesh.SetEnablePublish( False ) # Set to False to avoid publish in study if not needed or in some particular situations:
                                    # multiples meshes built in parallel, complex and numerous mesh edition (performance)

    Wake = smesh.Mesh(wake,'Wake')
    NETGEN_1D_2D = Wake.Triangle(algo=smeshBuilder.NETGEN_1D2D)
    NETGEN_2D_Parameters = NETGEN_1D_2D.Parameters()
    NETGEN_2D_Parameters.SetMaxSize( Wake_max_mesh_size )
    NETGEN_2D_Parameters.SetMinSize( Wake_min_mesh_size )
    NETGEN_2D_Parameters.SetSecondOrder( 0 )
    NETGEN_2D_Parameters.SetOptimize( 1 )
    NETGEN_2D_Parameters.SetFineness( 2 )
    NETGEN_2D_Parameters.SetChordalError( -1 )
    NETGEN_2D_Parameters.SetChordalErrorEnabled( 0 )
    NETGEN_2D_Parameters.SetUseSurfaceCurvature( 1 )
    NETGEN_2D_Parameters.SetFuseEdges( 1 )
    NETGEN_2D_Parameters.SetWorstElemMeasure( 0 )
    NETGEN_2D_Parameters.SetQuadAllowed( 0 )
    NETGEN_2D_Parameters.SetLocalSizeOnShape(TE_wing_base, TE_Wing_mesh_size)
    NETGEN_2D_Parameters.SetUseDelauney( 128 )
    NETGEN_2D_Parameters.SetCheckChartBoundary( 3 )
    isDone = Wake.Compute()
    try:
      Wake.ExportSTL( Wake_output_name, 1 )
      pass
    except:
      print('ExportSTL() failed. Invalid file name?')

    ## Set names of Mesh objects
    smesh.SetName(NETGEN_1D_2D.GetAlgorithm(), 'NETGEN 1D-2D')
    smesh.SetName(NETGEN_2D_Parameters, 'NETGEN 2D Parameters')
    smesh.SetName(Wake.GetMesh(), 'Wake')

    #Save salome files
    salome.myStudy.SaveAs(f'{Dir}/SalomeFiles/salome_wake_model_{Wake_angle}.hdf', study, False)

    print(' Information about wake mesh:')
    print(' Number of nodes       :', Wake.NbNodes())
    print(' Number of elements    :', Wake.NbTriangles())

if salome.sg.hasDesktop():
  salome.sg.updateObjBrowser()
