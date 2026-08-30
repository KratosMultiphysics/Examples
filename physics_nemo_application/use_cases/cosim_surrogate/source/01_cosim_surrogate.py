"""A trained surrogate inside CoSimulationApplication's coupling loop.

The application's cosim_surrogate_solver_wrapper makes a checkpoint a
first-class CoSimulation citizen: it is addressed by dotted path in the
"solvers" block, exposes interface data like any solver wrapper, and the
coupled solver drives it - here gauss_seidel_strong with an Aitken
accelerator and a kratos_mapping data transfer.

The coupled problem is a nonlinear interface fixed point,

    d = S(f) = 0.5 tanh(f) + 1,    f = d   (identity feedback)

whose solution d* solves d = 0.5 tanh(d) + 1. S is played by a TRAINED
MLP (fit to samples of the operator - standing in for an expensive
solver's interface response); the identity side is a second wrapper. The
run must land on the mathematical fixed point of the *learned* operator,
and does, to machine precision.

The convergence comparison (plain fixed-point vs Aitken) is REPLAYED
outside CoSimulation with the same learned operator, so the curves are
exact rather than parsed from solver logs.

Run time: under a minute.
"""

import json
import pathlib

import numpy
import torch
from matplotlib import pyplot
from scipy.optimize import brentq

import KratosMultiphysics as Kratos
import KratosMultiphysics.PhysicsNeMoApplication  # registers the application  # noqa: F401

OUTPUT = pathlib.Path("output")
DATA = pathlib.Path("..") / "data"

MDPA_STEM = "surrogate_interface_meshed"


def TrainInterfaceSurrogate():
    """An MLP fit to the interface operator S(f) = 0.5 tanh(f) + 1."""
    rng = numpy.random.default_rng(0)
    samples = rng.uniform(-3.0, 3.0, (4096, 1))
    inputs = torch.tensor(samples, dtype=torch.float64)
    targets = 0.5 * torch.tanh(inputs) + 1.0

    torch.manual_seed(0)
    trunk = torch.nn.Sequential(
        torch.nn.Linear(1, 32), torch.nn.Tanh(),
        torch.nn.Linear(32, 32), torch.nn.Tanh(), torch.nn.Linear(32, 1)).double()
    optimizer = torch.optim.Adam(trunk.parameters(), lr=2e-3)
    for _ in range(2000):
        optimizer.zero_grad()
        torch.nn.functional.mse_loss(trunk(inputs), targets).backward()
        optimizer.step()
    trunk.eval()

    class Componentwise(torch.nn.Module):
        """(N, 3) -> (N, 3): the scalar operator applied per component."""

        def __init__(self, inner):
            super().__init__()
            self.inner = inner

        def forward(self, x):
            flat = x.reshape(-1, 1)
            return self.inner(flat).reshape(x.shape)

    with torch.no_grad():
        probe = torch.linspace(-2, 2, 41, dtype=torch.float64)[:, None]
        fit_error = float((trunk(probe) - (0.5 * torch.tanh(probe) + 1)).abs().max())
    scripted = torch.jit.script(Componentwise(trunk))
    scripted.save(str(OUTPUT / "interface_surrogate.pt"))
    return fit_error


def IdentityCheckpoint():
    class Identity(torch.nn.Module):
        def forward(self, x):
            return x
    torch.jit.script(Identity()).save(str(OUTPUT / "identity.pt"))


def WrapperBlock(checkpoint, time_step=0.0):
    return Kratos.Parameters("""{
        "type" : "KratosMultiphysics.PhysicsNeMoApplication.cosim_surrogate_solver_wrapper",
        "solver_wrapper_settings" : {
            "mdpa_file"      : "%s",
            "time_step"      : %f,
            "model_settings" : { "checkpoint_file" : "%s", "device" : "cpu" },
            "input_fields"   : [ { "variable_name" : "FORCE",        "data_location" : "node_historical" } ],
            "output_fields"  : [ { "variable_name" : "DISPLACEMENT", "data_location" : "node_historical" } ]
        },
        "data" : {
            "load" : { "model_part_name" : "Surrogate", "variable_name" : "FORCE",        "dimension" : 3 },
            "disp" : { "model_part_name" : "Surrogate", "variable_name" : "DISPLACEMENT", "dimension" : 3 }
        }
    }""" % (MDPA_STEM, time_step, checkpoint))


def main():
    OUTPUT.mkdir(exist_ok=True)
    DATA.mkdir(exist_ok=True)
    Kratos.Logger.GetDefaultOutput().SetSeverity(Kratos.Logger.Severity.WARNING)

    fit_error = TrainInterfaceSurrogate()
    IdentityCheckpoint()
    print(f"interface surrogate fit: max |error| {fit_error:.2e} on [-2, 2]")

    # ---- the coupled run ---------------------------------------------------
    from KratosMultiphysics.CoSimulationApplication.co_simulation_analysis import (
        CoSimulationAnalysis)

    parameters = Kratos.Parameters("""{
        "problem_data" : {
            "start_time"    : 0.0,
            "end_time"      : 1.0,
            "echo_level"    : 0,
            "print_colors"  : false,
            "parallel_type" : "OpenMP"
        },
        "solver_settings" : {
            "type"                    : "coupled_solvers.gauss_seidel_strong",
            "echo_level"              : 0,
            "num_coupling_iterations" : 25,
            "convergence_accelerators" : [{
                "type"      : "aitken",
                "solver"    : "surrogate",
                "data_name" : "load"
            }],
            "convergence_criteria" : [{
                "type"          : "relative_norm_previous_residual",
                "solver"        : "surrogate",
                "data_name"     : "load",
                "abs_tolerance" : 1e-12,
                "rel_tolerance" : 1e-12
            }],
            "data_transfer_operators" : {
                "mapper" : {
                    "type"            : "kratos_mapping",
                    "mapper_settings" : { "mapper_type" : "nearest_neighbor" }
                }
            },
            "coupling_sequence" : [
                {
                    "name"            : "surrogate",
                    "input_data_list" : [{
                        "data"                   : "load",
                        "from_solver"            : "feedback",
                        "from_solver_data"       : "disp",
                        "data_transfer_operator" : "mapper"
                    }],
                    "output_data_list" : []
                },
                {
                    "name"            : "feedback",
                    "input_data_list" : [{
                        "data"                   : "load",
                        "from_solver"            : "surrogate",
                        "from_solver_data"       : "disp",
                        "data_transfer_operator" : "mapper"
                    }],
                    "output_data_list" : []
                }
            ],
            "solvers" : {}
        }
    }""")
    parameters["solver_settings"]["solvers"].AddValue(
        "surrogate", WrapperBlock("output/interface_surrogate.pt", time_step=1.0))
    parameters["solver_settings"]["solvers"].AddValue(
        "feedback", WrapperBlock("output/identity.pt"))

    analysis = CoSimulationAnalysis(parameters)
    analysis.Initialize()
    # a nonzero start: an all-zero state trivially satisfies the RELATIVE
    # convergence criterion and the loop would stop after one iteration
    wrappers = analysis._GetSolver().solver_wrappers
    for node in wrappers["feedback"].model_part.Nodes:
        node.SetSolutionStepValue(Kratos.DISPLACEMENT, [5.0, 5.0, 5.0])
    analysis.RunSolutionLoop()
    analysis.Finalize()
    converged = numpy.array(
        [node.GetSolutionStepValue(Kratos.DISPLACEMENT)
         for node in wrappers["surrogate"].model_part.Nodes])

    # the mathematical fixed point of the LEARNED operator (per component)
    surrogate = torch.jit.load(str(OUTPUT / "interface_surrogate.pt")).eval()

    def LearnedOperator(value):
        with torch.no_grad():
            return float(surrogate(torch.tensor([[value] * 3], dtype=torch.float64))[0, 0])

    fixed_point = brentq(lambda d: LearnedOperator(d) - d, 0.5, 2.5)
    coupling_error = float(numpy.abs(converged - fixed_point).max())
    print(f"CoSimulation converged to {converged.mean():.9f}; "
          f"learned operator's fixed point {fixed_point:.9f}; "
          f"max |difference| {coupling_error:.2e}")

    # ---- the convergence comparison, replayed exactly ----------------------
    def Replay(accelerated, iterations=15):
        d, history = 5.0, []
        previous_residual = previous_relaxed = None
        relaxation = 1.0
        for _ in range(iterations):
            proposal = LearnedOperator(d)
            residual = proposal - d
            history.append(abs(residual))
            if accelerated and previous_residual is not None:
                delta = residual - previous_residual
                if abs(delta) > 1e-15:
                    relaxation = -relaxation * previous_residual / delta
            d = d + relaxation * residual if accelerated else proposal
            previous_residual = residual
        return history

    plain = Replay(False)
    aitken = Replay(True)

    figure, axis = pyplot.subplots(figsize=(6.8, 4.0))
    axis.semilogy(range(1, len(plain) + 1), plain, "s-", label="plain fixed point")
    axis.semilogy(range(1, len(aitken) + 1), aitken, "o-", label="Aitken accelerated")
    axis.set_xlabel("coupling iteration")
    axis.set_ylabel("|interface residual|")
    axis.set_title("Convergence of the learned interface operator")
    axis.legend()
    axis.grid(True, which="both", alpha=0.3)
    figure.tight_layout()
    figure.savefig(DATA / "cosim_convergence.png", dpi=130)

    with open(OUTPUT / "cosim_summary.json", "w") as handle:
        json.dump({"fit_error": fit_error, "fixed_point": fixed_point,
                   "coupling_error": coupling_error,
                   "plain_residuals": plain, "aitken_residuals": aitken},
                  handle, indent=1)
    print(f"figure : {DATA / 'cosim_convergence.png'}")


if __name__ == "__main__":
    main()
