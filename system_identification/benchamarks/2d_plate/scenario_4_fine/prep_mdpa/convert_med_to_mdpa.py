import sys

# sys.path.append("/home/wessels/Software/git/Kratos/bin/Release")
# sys.path.append("/home/wessels/Software/git/Kratos/build/Release")

import KratosMultiphysics as Kratos
import KratosMultiphysics.MedApplication as KratosMED
from KratosMultiphysics.StructuralMechanicsApplication.structural_mechanics_analysis import StructuralMechanicsAnalysis

# Setup basic model to be filled later on
model = Kratos.Model()
Structure = model.CreateModelPart("Structure")

# Use to MED App to read med-file and write it to the previously created model part
KratosMED.MedModelPartIO("plate_mm_offset_z_3.med", Kratos.ModelPartIO.READ | Kratos.ModelPartIO.MESH_ONLY).ReadModelPart(Structure)


# From the med-file only geometries are read. So we need to convert them.
# To tell Kratos how to convert the different geometries we are defining a conversion table in the following:
# Note that you can only have one element type per model part. If you want to have different elements you need to have them grouped in different model parts. 
# The different element_ and condition_names are found in the wide space of Kratos files.
# Use Structure.NAME_OF_GROUP_IN_SALOME.
entity_params = Kratos.Parameters("""{
    "elements_list": [
        {
            "model_part_name": "Structure.main",
            "element_name": "ShellThinElement3D3N"
        },
        {
            "model_part_name": "Structure.damage_1",
            "element_name": "ShellThinElement3D3N"
        },
        {
            "model_part_name": "Structure.damage_2",
            "element_name": "ShellThinElement3D3N"
        },
        {
            "model_part_name": "Structure.damage_3",
            "element_name": "ShellThinElement3D3N"
        },
        {
            "model_part_name": "Structure.damage_4",
            "element_name": "ShellThinElement3D3N"
        },
        {
            "model_part_name": "Structure.damage_5",
            "element_name": "ShellThinElement3D3N"
        }                       
    ],
    "conditions_list": [
        {
            "model_part_name": "Structure.right_force",
            "condition_name": "LineLoadCondition3D2N"
        }
    ]    
}""")

# Now, we use the previously defined table to convert our geometries
modeler = Kratos.CreateEntitiesFromGeometriesModeler(model, entity_params)
modeler.SetupModelPart()

# All that's left is to assign a fresh properties container to the model
properties = Structure.CreateNewProperties(1)
cond: Kratos.Condition
for cond in Structure.Conditions:
    cond.Properties = properties

for elem in Structure.Elements:
    elem.Properties = properties

geometry_ids = []
for geom in Structure.Geometries:
    geometry_ids.append(geom.Id)

for geom_id in geometry_ids:
    Structure.RemoveGeometryFromAllLevels(geom_id)

node_ids = []
for node in Structure.Nodes:
    # We need to set the Z coordinate to 0.0, because the med-file has a z-offset
    node.Z = 0.0
    node.Z0 = 0.0
    node_ids.append(node.Id)

elem_ids = []
for elem in Structure.Elements:
    elem_ids.append(elem.Id)
all_nodes_elements = Structure.CreateSubModelPart("all_nodes_elements")
all_nodes_elements.AddNodes(node_ids)
all_nodes_elements.AddElements(elem_ids)

# In the end we write the model to a mdpa-file
Kratos.ModelPartIO("Structure", Kratos.ModelPartIO.MESH_ONLY | Kratos.ModelPartIO.WRITE).WriteModelPart(Structure)

print(Structure)

# ... and clean up unused classes
del model

 
