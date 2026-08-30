"""The autoregressive step model shared by the training and rollout scripts.

A residual next-state parameterization: the model returns
``last state + net(window)``. The identity part makes the network learn the
per-step *increment*, which is small - without it a plain next-state MLP
reproduces the state to ~0.1% per step, and 0.1% compounded over 38
autoregressive steps is a useless rollout. The wrapper is a plain
torch.nn.Module, so every stock API of the application (TrainModel,
TrainAutoregressive, EvaluateRollout, RolloutPredictions) uses it
unchanged.
"""

import torch

HISTORY = 4
WIDTH = 3  # per-node channels: displacement x/y and temperature


class ResidualStep(torch.nn.Module):
    def __init__(self, width: int = WIDTH, history: int = HISTORY):
        super().__init__()
        self.width = width
        self.net = torch.nn.Sequential(
            torch.nn.Linear(history * width, 128), torch.nn.Tanh(),
            torch.nn.Linear(128, 128), torch.nn.Tanh(),
            torch.nn.Linear(128, width))

    def forward(self, window):
        # windows are (..., history*width), oldest first - the trailing
        # width columns are the newest state
        return window[..., -self.width:] + self.net(window)


def Create(seed: int) -> ResidualStep:
    torch.manual_seed(seed)
    return ResidualStep()
