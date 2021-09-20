# Import Python libraries
import sys
sys.dont_write_bytecode = True
import os
import json
import time
import pickle

# Import Kratos, XMC, PyCOMPSs API
import KratosMultiphysics
import KratosMultiphysics.MultilevelMonteCarloApplication
import xmc
import xmc.methodDefs_momentEstimator.computeCentralMoments as mdccm
from exaqute import get_value_from_remote

if __name__ == "__main__":

    if(len(sys.argv)==2):
        parametersPath = str(sys.argv[1]) # set path to the parameters
    else:
        parametersPath = "problem_settings/parameters_xmc_asynchronous_mlmc_potentialFlow.json"

    # read parameters
    with open(parametersPath,'r') as parameter_file:
            parameters = json.load(parameter_file)

    # SolverWrapper
    parameters["solverWrapperInputDictionary"]["qoiEstimator"] = parameters["monteCarloIndexInputDictionary"]["qoiEstimator"]

    # SampleGenerator
    samplerInputDictionary = parameters["samplerInputDictionary"]
    samplerInputDictionary['randomGeneratorInputDictionary'] = parameters["randomGeneratorInputDictionary"]
    samplerInputDictionary['solverWrapperInputDictionary'] = parameters["solverWrapperInputDictionary"]

    # MonteCarloIndex
    monteCarloIndexInputDictionary = parameters["monteCarloIndexInputDictionary"]
    monteCarloIndexInputDictionary["samplerInputDictionary"] = samplerInputDictionary

    # MonoCriterion
    criteriaArray = []
    criteriaInputs = []
    for monoCriterion in (parameters["monoCriteriaInpuctDict"]):
        criteriaArray.append(xmc.monoCriterion.MonoCriterion(\
            parameters["monoCriteriaInpuctDict"][monoCriterion]["criteria"],\
            parameters["monoCriteriaInpuctDict"][monoCriterion]["tolerance"]))
        criteriaInputs.append([parameters["monoCriteriaInpuctDict"][monoCriterion]["input"]])

    # MultiCriterion
    multiCriterionInputDictionary=parameters["multiCriterionInputDictionary"]
    multiCriterionInputDictionary["criteria"] = criteriaArray
    multiCriterionInputDictionary["inputsForCriterion"] = criteriaInputs
    criterion = xmc.multiCriterion.MultiCriterion(**multiCriterionInputDictionary)

    # ErrorEstimator
    MSEErrorEstimator = xmc.errorEstimator.ErrorEstimator(**parameters["errorEstimatorInputDictionary"])

    # HierarchyOptimiser
    hierarchyCostOptimiser = xmc.hierarchyOptimiser.HierarchyOptimiser(**parameters["hierarchyOptimiserInputDictionary"])

    # EstimationAssembler
    if "expectationAssembler" in parameters["estimationAssemblerInputDictionary"].keys():
        expectationAssembler = xmc.estimationAssembler.EstimationAssembler(**parameters["estimationAssemblerInputDictionary"]["expectationAssembler"])
    if "discretizationErrorAssembler" in parameters["estimationAssemblerInputDictionary"].keys():
        discretizationErrorAssembler = xmc.estimationAssembler.EstimationAssembler(**parameters["estimationAssemblerInputDictionary"]["discretizationErrorAssembler"])
    if "varianceAssembler" in parameters["estimationAssemblerInputDictionary"].keys():
        varianceAssembler = xmc.estimationAssembler.EstimationAssembler(**parameters["estimationAssemblerInputDictionary"]["varianceAssembler"])

    # MonteCarloSampler
    monteCarloSamplerInputDictionary = parameters["monteCarloSamplerInputDictionary"]
    monteCarloSamplerInputDictionary["indexConstructorDictionary"] = monteCarloIndexInputDictionary
    monteCarloSamplerInputDictionary["assemblers"] =  [expectationAssembler,discretizationErrorAssembler,varianceAssembler]
    monteCarloSamplerInputDictionary["errorEstimators"] = [MSEErrorEstimator]
    mcSampler = xmc.monteCarloSampler.MonteCarloSampler(**monteCarloSamplerInputDictionary)

    # XMCAlgorithm
    XMCAlgorithmInputDictionary = parameters["XMCAlgorithmInputDictionary"]
    XMCAlgorithmInputDictionary["monteCarloSampler"] = mcSampler
    XMCAlgorithmInputDictionary["hierarchyOptimiser"] = hierarchyCostOptimiser
    XMCAlgorithmInputDictionary["stoppingCriterion"] = criterion

    algo = xmc.XMCAlgorithm(**XMCAlgorithmInputDictionary)

    time_start = time.time()
    if (parameters["solverWrapperInputDictionary"]["asynchronous"] is True):
        algo.runAsynchronousXMC()
    else:
        algo.runXMC()
    time_end = time.time()
    print("[SCREENING] time to solution:",time_end-time_start)

    ########################################################################################################################################################################################################
    ########################################################################################################################################################################################################
    ########################################################################################################################################################################################################

    # retrieve project parameters and mdpa
    with open(parameters["solverWrapperInputDictionary"]["projectParametersPath"][0],'r') as parameter_file:
        project_parameters = json.load(parameter_file)
    pickled_model = algo.monteCarloSampler.indices[0].sampler.solvers[0].pickled_model[0]
    serialized_model = pickle.loads(pickled_model)
    current_model = KratosMultiphysics.Model()
    serialized_model.Load("ModelSerialization",current_model)
    model_part_of_interest = "model.Body2D_Body"

    # writing to file a dictionary
    qoi_dict = {}
    # save Kratos project parameters and mdpa info
    qoi_dict["KratosMultiphysics_project_parameters"] = {"project_parameters":project_parameters}
    qoi_dict["model_part"] = {"mdpa_names":current_model.GetModelPartNames(),"mdpa_of_interest":model_part_of_interest}
    # save xmc parameters
    if(len(sys.argv)==2):
        parametersPath_dict = str(sys.argv[1]) # set path to the parameters
    else:
        parametersPath_dict = "problem_settings/parameters_xmc_asynchronous_mlmc_potentialFlow.json"
    # read parameters
    with open(parametersPath_dict,'r') as parameter_file_dict:
            parameters_dict = json.load(parameter_file_dict)
    qoi_dict["XMC_parameters"] = {"parameters":parameters_dict}

    # add legend
    qoi_dict["qoi_id_legend"] = {"index_legend":{}}
    qoi_dict["qoi_id_legend"]["index_legend"] = {"qoi_id":"qoi id", "index": "Monte Carlo index/level", "instances": "number of samples/contributions for current level", "Sa": "power sum order a", "ha": "moment order a","type":"qoi type","tag":"physical quantity name","node_id": "mesh node id", "node_coordinates": "coordinates of the node"}

    # save lift coefficient
    for qoi_counter in range (0,1):
        qoi_dict["qoi_id_"+str(qoi_counter)] = {"index_"+str(index): {} for index in range (len(algo.monteCarloSampler.indices))}
        for index in range (len(algo.monteCarloSampler.indices)):
            algo.monteCarloSampler.indices[index].qoiEstimator[qoi_counter] = get_value_from_remote(algo.monteCarloSampler.indices[index].qoiEstimator[qoi_counter])
            sample_counter = algo.monteCarloSampler.indices[index].qoiEstimator[qoi_counter]._sampleCounter
            S10 = float(get_value_from_remote(algo.monteCarloSampler.indices[index].qoiEstimator[qoi_counter].powerSums[0][0]))
            S01 = float(get_value_from_remote(algo.monteCarloSampler.indices[index].qoiEstimator[qoi_counter].powerSums[0][1]))
            S20 = float(get_value_from_remote(algo.monteCarloSampler.indices[index].qoiEstimator[qoi_counter].powerSums[1][0]))
            S11 = float(get_value_from_remote(algo.monteCarloSampler.indices[index].qoiEstimator[qoi_counter].powerSums[1][1]))
            S02 = float(get_value_from_remote(algo.monteCarloSampler.indices[index].qoiEstimator[qoi_counter].powerSums[1][2]))
            h1 = float(get_value_from_remote(mdccm.computeCentralMomentsOrderOneDimensionOne(S10,S01,sample_counter)))
            h2 = float(get_value_from_remote(mdccm.computeCentralMomentsOrderTwoDimensionOne(S10,S01,S20,S11,S02,sample_counter)))
            qoi_dict["qoi_id_"+str(qoi_counter)]["index_"+str(index)] = {"qoi_id":qoi_counter, "index": index, "instances": sample_counter, "S10": S10, "S01": S01, "S20": S20, "S11": S11, "S02": S02, "h1": h1, "h2": h2,"type":"scalar_quantity","tag":"lift_coefficient"}

    # save pressure coefficient
    qoi_counter = qoi_counter + 1
    qoi_dict["qoi_id_"+str(qoi_counter)] = {"member_"+str(member): {} for member in range (algo.monteCarloSampler.indices[index].qoiEstimator[qoi_counter]._variableDimension)}
    member = 0
    for node in current_model.GetModelPart(model_part_of_interest).Nodes:
        qoi_dict["qoi_id_"+str(qoi_counter)]["member_"+str(member)] = {"index_"+str(index): {} for index in range (len(algo.monteCarloSampler.indices))}
        for index in range (len(algo.monteCarloSampler.indices)):
            algo.monteCarloSampler.indices[index].qoiEstimator[qoi_counter] = get_value_from_remote(algo.monteCarloSampler.indices[index].qoiEstimator[qoi_counter])
            sample_counter = algo.monteCarloSampler.indices[index].qoiEstimator[qoi_counter]._sampleCounter
            S10 = float(get_value_from_remote(algo.monteCarloSampler.indices[index].qoiEstimator[qoi_counter]._powerSums["10"][member]))
            S01 = float(get_value_from_remote(algo.monteCarloSampler.indices[index].qoiEstimator[qoi_counter]._powerSums["01"][member]))
            S20 = float(get_value_from_remote(algo.monteCarloSampler.indices[index].qoiEstimator[qoi_counter]._powerSums["20"][member]))
            S11 = float(get_value_from_remote(algo.monteCarloSampler.indices[index].qoiEstimator[qoi_counter]._powerSums["11"][member]))
            S02 = float(get_value_from_remote(algo.monteCarloSampler.indices[index].qoiEstimator[qoi_counter]._powerSums["02"][member]))
            h1 = float(get_value_from_remote(mdccm.computeCentralMomentsOrderOneDimensionOne(S10,S01,sample_counter)))
            h2 = float(get_value_from_remote(mdccm.computeCentralMomentsOrderTwoDimensionOne(S10,S01,S20,S11,S02,sample_counter)))
            qoi_dict["qoi_id_"+str(qoi_counter)]["member_"+str(member)]["index_"+str(index)] = {"qoi_id":qoi_counter, "member":member, "index": index, "instances": sample_counter, "S10": S10, "S01": S01, "S20": S20, "S11": S11, "S02": S02, "h1": h1, "h2": h2,"type":"scalar_quantity","tag":"pressure coefficent","node_id":node.Id,"node_coordinates":[node.X,node.Y,node.Z]}
        member += 1

    # save to file
    with open('power_sums_outputs/MLMC_asynchronous_power_sums_' +str(time.time()) + '.json', 'w') as f:
        json.dump(qoi_dict, f, indent=2)