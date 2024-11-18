if __name__ == "__main__":

    # --- STD Imports ---
    import sys
    import argparse
    import pathlib

    # --- Kratos Imports ---
    import KratosMultiphysics
    from KratosMultiphysics.analysis_stage import AnalysisStage
    from KratosMultiphysics.StructuralMechanicsApplication.structural_mechanics_analysis import StructuralMechanicsAnalysis

    try:
        import KratosMultiphysics.LinearSolversApplication
    except ImportError as exception:
        print(str(exception), file = sys.stderr)
        print("This example requires the LinearSolversApplication", file = sys.stderr)
        exit(1)

    try:
        import KratosMultiphysics.StructuralMechanicsApplication
    except ImportError as exception:
        print(str(exception), file = sys.stderr)
        print("This example requires the StructuralMechanicsApplication", file = sys.stderr)
        exit(1)

    try:
        import KratosMultiphysics.ConstitutiveLawsApplication
    except ImportError as exception:
        print(str(exception), file = sys.stderr)
        print("This example requires the ConstitutiveLawsApplication", file = sys.stderr)
        exit(1)

    # Parse input arguments
    parser: argparse.ArgumentParser = argparse.ArgumentParser("TrussSnapThrough")
    parser.add_argument("json_input",
                        type = pathlib.Path,
                        choices = [pathlib.Path("ProjectParametersLoadControl.json"),
                                   pathlib.Path("ProjectParametersDisplacementControl.json")],
                        default = pathlib.Path("ProjectParametersLoadControl.json"),
                        nargs = "?")
    arguments = parser.parse_args()

    # Read settings.
    parameters: KratosMultiphysics.Parameters
    with open(arguments.json_input, 'r') as file:
        parameters = KratosMultiphysics.Parameters(file.read())

    # Run the example.
    model = KratosMultiphysics.Model()
    analysis: AnalysisStage = StructuralMechanicsAnalysis(model, parameters)
    analysis.Run()
