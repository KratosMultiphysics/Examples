"""Stage 2 - train an FNO ensemble with governance artifacts.

Trains three FNO members (identical architecture, different seeds) on the
Stage-1 dataset. Three artifacts per member come out of this stage, and
each is load-bearing at deployment:

* the checkpoint itself (.mdlus, PhysicsNeMo's native format);
* a **model card** declaring the input/output fields and grid shape the
  member was trained for - the deployment process validates its own
  configuration against it, so wiring TEMPERATURE where CONDUCTIVITY
  belongs fails loudly instead of producing plausible garbage;
* for member 0, an **OOD guard** calibrated on the training inputs during
  training - at deployment it scores every input grid against what the
  model has seen, catching the silent failure mode of surrogates
  (extrapolation *looks* exactly like interpolation in the output field).

The ensemble members exist for uncertainty: their per-node disagreement at
deployment is an error bar that costs three forward passes.

Run time: ~2 minutes on CPU, less on any GPU.
"""

import pathlib

import numpy
import torch
from matplotlib import pyplot
from physicsnemo.models.fno import FNO

import KratosMultiphysics as Kratos
from KratosMultiphysics.PhysicsNeMoApplication import training_utils

OUTPUT = pathlib.Path("output")
DATA = pathlib.Path("..") / "data"

MEMBERS = 3
GRID_SHAPE = [32, 32, 2]
INPUT_FIELDS = [{"variable_name": "CONDUCTIVITY", "data_location": "node_historical"},
                {"variable_name": "HEAT_FLUX", "data_location": "node_historical"}]
OUTPUT_FIELDS = [{"variable_name": "TEMPERATURE", "data_location": "node_non_historical"}]


class GridDataset(torch.utils.data.Dataset):
    def __init__(self, inputs, targets):
        self.inputs = torch.from_numpy(inputs).float()
        self.targets = torch.from_numpy(targets).float()

    def __len__(self):
        return len(self.inputs)

    def __getitem__(self, index):
        return self.inputs[index], self.targets[index]


def main():
    data = numpy.load(OUTPUT / "thermal_dataset.npz")
    dataset = GridDataset(data["inputs"], data["targets"])
    print(f"dataset: {len(dataset)} cases, inputs {tuple(dataset.inputs.shape[1:])}, "
          f"targets {tuple(dataset.targets.shape[1:])}")

    histories = []
    for member in range(MEMBERS):
        model = FNO(in_channels=2, out_channels=1, dimension=3,
                    latent_channels=16, num_fno_layers=3,
                    num_fno_modes=[8, 8, 1], padding=2)

        settings = Kratos.Parameters("""{
            "epochs"        : 300,
            "batch_size"    : 8,
            "learning_rate" : 2e-3,
            "device"        : "auto",
            "seed"          : %d,
            "echo_interval" : 100
        }""" % member)
        if member == 0:
            # calibrate the OOD guard on the training inputs as part of
            # training - the sidecar the deployment stage loads
            # knn_k/sensitivity tuned on a held-out conductivity ramp: at the
            # defaults the kNN check flags edge-of-range inputs that are in
            # fact inside the training distribution; sensitivity 6 separates
            # cleanly (0 false flags inside k in [0.5, 2], all caught outside)
            settings.AddEmptyValue("ood_guard")
            settings["ood_guard"].AddString(
                "guard_file", str(OUTPUT / "thermal_fno.ood_guard.pt"))
            settings["ood_guard"].AddInt("knn_k", 10)
            settings["ood_guard"].AddDouble("sensitivity", 6.0)

        history = training_utils.TrainModel(model, dataset, settings)
        histories.append(history)

        checkpoint = OUTPUT / (f"thermal_fno.mdlus" if member == 0
                               else f"thermal_fno_member{member}.mdlus")
        training_utils.SaveTrainedModel(model, checkpoint, card={
            "description": "FNO surrogate of the stationary thermal plate "
                           "(-k lap(u) = f, Gaussian source)",
            "input_fields": INPUT_FIELDS,
            "output_fields": OUTPUT_FIELDS,
            "grid_shape": GRID_SHAPE,
            "training": {"cases": len(dataset), "epochs": 300, "seed": member},
        })
        print(f"member {member}: final loss {history[-1]:.3e} -> {checkpoint}")

    figure, axis = pyplot.subplots(figsize=(6.5, 4.2))
    for member, history in enumerate(histories):
        axis.semilogy(history, label=f"member {member} (seed {member})")
    axis.set_xlabel("epoch")
    axis.set_ylabel("MSE loss")
    axis.set_title("FNO ensemble training")
    axis.legend()
    axis.grid(True, which="both", alpha=0.3)
    figure.tight_layout()
    figure.savefig(DATA / "training_loss.png", dpi=130)
    print(f"figure : {DATA / 'training_loss.png'}")


if __name__ == "__main__":
    main()
