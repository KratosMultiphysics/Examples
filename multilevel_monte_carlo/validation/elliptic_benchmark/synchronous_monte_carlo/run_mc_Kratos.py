# Import Python libraries
import sys
sys.dont_write_bytecode = True
import os
import json

# Import Kratos, XMC
import KratosMultiphysics
import KratosMultiphysics.MultilevelMonteCarloApplication
import xmc

if __name__ == "__main__":

    if(len(sys.argv)==2):
        parametersPath = str(sys.argv[1]) # set path to the parameters
    else:
        parametersPath = "../problem_settings/parameters_xmc_test_mc_Kratos_poisson_2d.json"

    # read parameters
    with open(parametersPath,'r') as parameter_file:
            parameters = json.load(parameter_file)

    # SolverWrapper
    parameters["solverWrapperInputDictionary"]["qoiEstimator"] = parameters[
        "monteCarloIndexInputDictionary"
    ]["qoiEstimator"]
    # SampleGenerator
    samplerInputDictionary = parameters["samplerInputDictionary"]
    samplerInputDictionary["randomGeneratorInputDictionary"] = parameters[
        "randomGeneratorInputDictionary"
    ]
    samplerInputDictionary["solverWrapperInputDictionary"] = parameters[
        "solverWrapperInputDictionary"
    ]
    # MonteCarloIndex
    monteCarloIndexInputDictionary = parameters["monteCarloIndexInputDictionary"]
    monteCarloIndexInputDictionary["samplerInputDictionary"] = samplerInputDictionary
    # MonoCriterion
    criteriaArray = []
    criteriaInputs = []
    for monoCriterion in parameters["monoCriteriaInputDictionary"]:
        criteriaArray.append(
            xmc.monoCriterion.MonoCriterion(
                parameters["monoCriteriaInputDictionary"][monoCriterion]["criteria"],
                parameters["monoCriteriaInputDictionary"][monoCriterion]["tolerance"],
            )
        )
        criteriaInputs.append(
            [parameters["monoCriteriaInputDictionary"][monoCriterion]["input"]]
        )
    # MultiCriterion
    multiCriterionInputDictionary = parameters["multiCriterionInputDictionary"]
    multiCriterionInputDictionary["criteria"] = criteriaArray
    multiCriterionInputDictionary["inputsForCriterion"] = criteriaInputs
    criterion = xmc.multiCriterion.MultiCriterion(**multiCriterionInputDictionary)
    # ErrorEstimator
    statErrorEstimator = xmc.errorEstimator.ErrorEstimator(
        **parameters["errorEstimatorInputDictionary"]
    )
    # HierarchyOptimiser
    # Set tolerance from stopping criterion
    parameters["hierarchyOptimiserInputDictionary"]["tolerance"] = parameters["monoCriteriaInputDictionary"]["statisticalError"]["tolerance"]
    hierarchyCostOptimiser = xmc.hierarchyOptimiser.HierarchyOptimiser(
        **parameters["hierarchyOptimiserInputDictionary"]
    )
    # EstimationAssembler
    if (
        "expectationAssembler"
        in parameters["estimationAssemblerInputDictionary"].keys()
    ):
        expectationAssembler = xmc.estimationAssembler.EstimationAssembler(
            **parameters["estimationAssemblerInputDictionary"]["expectationAssembler"]
        )
    if "varianceAssembler" in parameters["estimationAssemblerInputDictionary"].keys():
        varianceAssembler = xmc.estimationAssembler.EstimationAssembler(
            **parameters["estimationAssemblerInputDictionary"]["varianceAssembler"]
        )
    # MonteCarloSampler
    monteCarloSamplerInputDictionary = parameters["monteCarloSamplerInputDictionary"]
    monteCarloSamplerInputDictionary[
        "indexConstructorDictionary"
    ] = monteCarloIndexInputDictionary
    monteCarloSamplerInputDictionary["assemblers"] = [
        expectationAssembler,
        varianceAssembler,
    ]
    monteCarloSamplerInputDictionary["errorEstimators"] = [statErrorEstimator]
    # build Monte Carlo sampler object
    mcSampler = xmc.monteCarloSampler.MonteCarloSampler(
        **monteCarloSamplerInputDictionary
    )
    # XMCAlgorithm
    XMCAlgorithmInputDictionary = parameters["XMCAlgorithmInputDictionary"]
    XMCAlgorithmInputDictionary["monteCarloSampler"] = mcSampler
    XMCAlgorithmInputDictionary["hierarchyOptimiser"] = hierarchyCostOptimiser
    XMCAlgorithmInputDictionary["stoppingCriterion"] = criterion
    algo = xmc.XMCAlgorithm(**XMCAlgorithmInputDictionary)

    if parameters["solverWrapperInputDictionary"]["asynchronous"] is True:
        algo.runAsynchronousXMC()
    else:
        algo.runXMC()