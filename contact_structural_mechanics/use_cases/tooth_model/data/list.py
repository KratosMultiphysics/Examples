from __future__ import print_function, absolute_import, division
import KratosMultiphysics
import KratosMultiphysics.StructuralMechanicsApplication

current_model = KratosMultiphysics.Model()

model_part = current_model.CreateModelPart("Main")
model_part_io = KratosMultiphysics.ModelPartIO("composite15+enamel05+dentine25")
model_part_io.ReadModelPart(model_part)

lista = []
for node in model_part.Nodes:
    if node.Y > 0.004999999999:
        lista.append(node.Id)

print(lista)
