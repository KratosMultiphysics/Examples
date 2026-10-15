import os
import numpy as np
from scipy.stats import qmc  
import matplotlib
import matplotlib.pyplot as plt
matplotlib.use('Agg')
import matplotlib.patheffects as path_effects
import KratosMultiphysics


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# get multiple parameters by Halton or LatinHypercube methods
#
def get_multiple_parameters( number_of_train_values, number_of_test_values=0, mu_validation=[],
    angle_range=[], mach_range=[], method='Halton', beta1_values=[1.0], beta2_values=[1.0], folder_name='Mu_parameters'):

    os.makedirs(folder_name, exist_ok=True)
    Sampler = qmc.Halton if method == 'Halton' else qmc.LatinHypercube

    # =========================
    # TRAIN (acumulativo)
    # =========================
    for beta1 in beta1_values:

        sampler = Sampler(d=2)
        mu_train = []
        previous_n = 0

        for id, n_values in enumerate(number_of_train_values):

            if n_values <= previous_n:
                continue

            new_points = n_values - previous_n
            previous_n = n_values

            sample = sampler.random(new_points)

            transformed = np.zeros_like(sample)
            transformed[:,0] = sample[:,0]**beta1  # alpha
            transformed[:,1] = sample[:,1]**beta1  # mach

            values = qmc.scale( transformed, [angle_range[0], mach_range[0]], [angle_range[1], mach_range[1]])

            for i in range(new_points):
                mu_train.append([
                    values[i, 0], values[i, 1], 1.0, 1.0, 1.0, 1.0, 1.0])

            suffix = f"{beta1}"
            file_path = f"{folder_name}/mu_train_{id}_{suffix}.npy"
            np.save(file_path, mu_train)

    # =========================
    # TEST
    # =========================
    mu_test = []
    if number_of_test_values > 0:
        sampler = Sampler(d=2)
        sample = sampler.random(number_of_test_values)

        values = qmc.scale(
            sample,
            [angle_range[0], mach_range[0]],
            [angle_range[1], mach_range[1]]
        )

        mu_test = [
            [values[i, 0], values[i, 1], 1., 1., 1., 1., 1.]
            for i in range(number_of_test_values)
        ]

        np.save(f'{folder_name}/mu_test.npy', mu_test)

    # =========================
    # VALIDATION
    # =========================
    if mu_validation:
        np.save(f'{folder_name}/mu_validation.npy', mu_validation)

    # =========================
    # PLOTS
    # =========================
    mu_test_xy = [[m[0], m[1]] for m in mu_test]
    mu_val_xy = [[m[0], m[1]] for m in mu_validation]

    for id, _ in enumerate(number_of_train_values):
        for beta1 in beta1_values:

            suffix = f"{beta1}"
            name = f"mu_train_{id}_{suffix}"

            mu_train = np.load(f"{folder_name}/{name}.npy")
            mu_train_xy = [[m[0], m[1]] for m in mu_train]

            plot_mu_values( mu_train_xy, mu_test_xy, mu_val_xy, name, folder_name)


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# plot parameters
#
def plot_mu_values(mu_train, mu_test, mu_validation, name, folder_name='Mu_parameters'):
    fig, ax = plt.subplots()
    fig.set_figwidth(10.0)
    fig.set_figheight(6.0)
    mu_train = np.array(mu_train).reshape(-1, 2) if len(mu_train) > 0 else np.empty((0, 2))
    mu_test = np.array(mu_test).reshape(-1, 2) if len(mu_test) > 0 else np.empty((0, 2))
    mu_validation = np.array(mu_validation).reshape(-1, 2) if len(mu_validation) > 0 else np.empty((0, 2))
    if len(mu_train) + len(mu_test) + len(mu_validation) > 0:
        all_mu_values = np.concatenate((mu_train, mu_test, mu_validation), axis=0)
        min_alpha, min_mach = np.min(all_mu_values[:, 0]), np.min(all_mu_values[:, 1])
        max_alpha, max_mach = np.max(all_mu_values[:, 0]), np.max(all_mu_values[:, 1])
        regions = [
            ((min_mach, min_alpha), (max_mach, max_alpha), 'red')
        ]
        for bottom_left, top_right, color in regions:
            rect = plt.Rectangle(
                bottom_left,
                top_right[0] - bottom_left[0],
                top_right[1] - bottom_left[1],
                facecolor=color, edgecolor=color, alpha=0.25
            )
            ax.add_patch(rect)
    def plot_points_with_labels(data, marker, color, label, dx=0.0, dy=-0.08):
        if len(data) > 0:
            for i, (alpha, mach) in enumerate(data):
                ax.plot(mach, alpha, marker, color=color, label=label if i == 0 else "", markersize=8)
                text = ax.text(mach + dx, alpha + dy, str(i), fontsize=8, ha='center', va='center', color=color)
                text.set_path_effects([
                    path_effects.Stroke(linewidth=1.5, foreground='black'),
                    path_effects.Normal()
                ])
    plot_points_with_labels(mu_train, 's', 'blue', "Train Values")
    plot_points_with_labels(mu_test, 'x', 'red', "Test Values")
    plot_points_with_labels(mu_validation, '*', 'green', "Validation Values")
    plt.title('Mu Values')
    plt.ylabel('Alpha')
    plt.xlabel('Mach')
    plt.grid(True)
    plt.legend(bbox_to_anchor=(1.02, 1), loc='upper left', borderaxespad=0.)
    plt.tight_layout()
    plt.savefig(f"{folder_name}/{name}.png", bbox_inches='tight', dpi=400)
    plt.close('all')


# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
#
# load parameters
#
def load_mu_parameters(name, folder_name='Mu_parameters'):
    filename = f'{folder_name}/{name}.npy'
    if os.path.exists(filename):
        mu_npy = np.load(filename)
        mu =  [mu.tolist() for mu in mu_npy]
    else:
        mu = []
    return mu
    
# # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #



if __name__ == "__main__":

    ###########################################################
    # PARAMETERS SETTINGS
    update_parameters   = True
    VALIDATION          = True
    number_of_mu_train  = [5, 10, 15]
    number_of_mu_test   = 3
    beta_values         = [1.00, 0.75]
    mach_range          = [0.70, 0.75]
    angle_range         = [0.00, 2.00]
    ###########################################################

    mu_validation = []
    if VALIDATION:
        if angle_range[0] <= 1.0 and angle_range[1]>= 1.0 and mach_range[0] <= 0.72 and mach_range[1]>=0.72:
            mu_validation.append([1.0,0.72,1.0,1.0,1.0,1.0,1.0])
        if angle_range[0] <= 1.0 and angle_range[1]>= 1.0 and mach_range[0] <= 0.73 and mach_range[1]>=0.73:
            mu_validation.append([1.0,0.73,1.0,1.0,1.0,1.0,1.0])
        if angle_range[0] <= 1.0 and angle_range[1]>= 1.0 and mach_range[0] <= 0.75 and mach_range[1]>=0.75:
            mu_validation.append([1.0,0.75,1.0,1.0,1.0,1.0,1.0])
        if angle_range[0] <= 2.0 and angle_range[1]>= 2.0 and mach_range[0] <= 0.75 and mach_range[1]>=0.75:
            mu_validation.append([2.0,0.75,1.0,1.0,1.0,1.0,1.0])

    if update_parameters:
        KratosMultiphysics.kratos_utilities.DeleteDirectoryIfExisting('Mu_parameters')
        get_multiple_parameters(number_of_train_values = number_of_mu_train,
                                number_of_test_values  = number_of_mu_test , 
                                mu_validation          = mu_validation     ,
                                angle_range            = angle_range       , 
                                mach_range             = mach_range        , 
                                method                 = 'Halton'          ,
                                beta1_values = beta_values, beta2_values = beta_values)
    else:
        mu_test  = [[mu[0],mu[1]] for mu in load_mu_parameters('mu_test')] 
        mu_validation = [[mu[0],mu[1]] for mu in load_mu_parameters('mu_validation')]
        for id, mu in enumerate(number_of_mu_train):
            for beta in beta_values:
                mu_train = [[mu[0],mu[1]] for mu in load_mu_parameters(f'mu_train_{id}_{beta}')]
                plot_mu_values(mu_train, mu_test, mu_validation, f'Mu_values_{id}_{beta}')