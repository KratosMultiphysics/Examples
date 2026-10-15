import KratosMultiphysics.kratos_utilities

def ClearAll():
    KratosMultiphysics.kratos_utilities.DeleteDirectoryIfExisting('Mu_parameters')
    KratosMultiphysics.kratos_utilities.DeleteDirectoryIfExisting('rom_data')
    KratosMultiphysics.kratos_utilities.DeleteDirectoryIfExisting('__pycache__')
    KratosMultiphysics.kratos_utilities.DeleteDirectoryIfExisting('Results')
    KratosMultiphysics.kratos_utilities.DeleteFileIfExisting('data.xlsx')
    KratosMultiphysics.kratos_utilities.DeleteFileIfExisting('naca0012HROM.med')
    KratosMultiphysics.kratos_utilities.DeleteFileIfExisting('naca0012HROMVisualization.med')
    KratosMultiphysics.kratos_utilities.DeleteFileIfExisting('2d_naca0012_rom_potential_flow.post.lst')

if __name__ == "__main__":
    ClearAll()