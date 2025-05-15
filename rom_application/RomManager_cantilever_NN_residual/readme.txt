To run this code it is essential that you compile this particular branch of KratosMultiphysics:
https://github.com/KratosMultiphysics/Kratos/tree/RomApp_RomManager_ResidualTrainingStructural

It is also essential that you modify the scripts/standard_configure.sh file for Kratos' compilation by addig the next lines:
add_app ${KRATOS_APP_DIR}/StructuralMechanicsApplication
add_app ${KRATOS_APP_DIR}/ConstitutiveLawsApplication
add_app ${KRATOS_APP_DIR}/RomApplication

This will compile the needed applications from Kratos