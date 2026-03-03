# Benchmarks: Verification Cases

**Author:** Ihar Antonau

**Kratos version:** X.X

## Benchmarks Specification

This benchmark suit contains five scenarios to test damage localizations in structures. All examples are based on 2D Plate with a hole. The source file to prepare model can be find in /prep_mdpa folder. Each scenario folder contains tree folders:
 - /damaged_system: simple FE run to compute displacements and strains of the damaged model. One can modify the damage intensity or position by choosing different sub mesh in Material.JSON file.
  - /sensor_placement contains sensor_data.json to describe the sensor set to use in damage identification process.
  - /system_identification contains all file to run SI process. Here you can change all optimization settings or redefine optimization problem.
