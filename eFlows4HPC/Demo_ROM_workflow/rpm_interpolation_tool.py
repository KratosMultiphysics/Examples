from sys import argv
from demo_case_non_intrusive import interpolate_parameters

if __name__ == '__main__':

    mu = [200, 300, 400, 500]

    # Get the analysis directory path from the command line argument
    analysis_directory_path = argv[1]

    # Define the RPM values for which we want to interpolate
    # Exclude RPM values of 200, 300, 400, and 500 from mu
    interpolated_rpms = [value for value in mu if value not in [200, 300, 400, 500]]

    # Call the interpolate_parameters function to perform non-intrusive interpolation
    # for the defined RPM values using the given analysis directory
    interpolate_parameters(analysis_directory_path, interpolated_rpms)
