
#this script plots the erros between the ROM and HROM, and FOM and HROM for solution and QoI

import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.colors import LinearSegmentedColormap
import os
from matplotlib import rc
# Configure Matplotlib to use LaTeX
rc('text', usetex=True)
rc('font', family='serif')
from matplotlib import rcParams
rcParams['text.latex.preamble'] = r'\usepackage{bm}'


def GetPercentualError(reference, approx):
    return np.linalg.norm(reference - approx) / np.linalg.norm(reference) *100



def load_rom_data(example,model,add_to_name, svd):

    resuts_path = f'./Example_{example}/' +f'{model}/'

    if model=='Affine':
        vy_rom = np.load(resuts_path+f'y_velocity_ROM_{svd}{add_to_name}.npy')
        w_rom = np.load(resuts_path+f'narrowing_ROM_{svd}{add_to_name}.npy')
    elif model=='FFD_RBF':
        vy_rom = np.load(resuts_path+f'y_velocity_ROM{add_to_name}_{svd}.npy')
        w_rom = np.load(resuts_path+f'narrowing_ROM{add_to_name}_{svd}.npy')
    else:
        error

    return vy_rom,w_rom



def load_hrom_data(example,model,add_to_name, svd,res):

    resuts_path = f'./Example_{example}/' +f'{model}/'

    if model=='Affine':
        vy_rom = np.load(resuts_path+f'y_velocity_HROM{add_to_name}_{svd}_{res}.npy')
        w_rom =  np.load(resuts_path+f'narrowing_HROM{add_to_name}_{svd}_{res}.npy')
    elif model=='FFD_RBF':
        vy_rom =  np.load(resuts_path+f'y_velocity_HROM{add_to_name}_{svd}_{res}.npy')
        w_rom = np.load(resuts_path+f'narrowing_HROM{add_to_name}_{svd}_{res}.npy')
    else:
        error

    return vy_rom,w_rom


def load_rom_snapshots(example,model,add_to_name, svd):

    resuts_path = f'./Example_{example}/' +f'{model}/'

    if model=='Affine':
        rom_snapshots = np.load(resuts_path+f'ROM_snapshots_{svd}{add_to_name}.npy')
    elif model=='FFD_RBF':
        rom_snapshots = np.load(resuts_path+f'ROM_snapshots{add_to_name}_{svd}.npy')
    else:
        error

    return rom_snapshots


def load_hrom_snapshots(example,model,add_to_name, svd,res):

    resuts_path = f'./Example_{example}/' +f'{model}/'

    if model=='Affine':
        hrom_snapshots = np.load(resuts_path+f'HROM_snapshots{add_to_name}_{svd}_{res}.npy')
    elif model=='FFD_RBF':
        hrom_snapshots = np.load(resuts_path+f'HROM_snapshots{add_to_name}_{svd}_{res}.npy')
    else:
        error

    return hrom_snapshots


def plot_numpy_array(filled_array, title, store_path):

    # Define the colors for the colormap
    colors = [(0, 1, 0), (1, 1, 0), (1, 0, 0)]  # Green to Yellow to Red

    # Create the colormap
    cmap = LinearSegmentedColormap.from_list('green_to_red', colors, N=256)

    max_value_allowed_before_black = 250

    # Set the color for values below and above a threshold
    cmap.set_under(color='black')
    cmap.set_over(color='black')

    # Plotting
    fig, ax = plt.subplots(1, 1, figsize=(4, 4))

    im = ax.imshow(filled_array, cmap=cmap, aspect='auto', vmin=0, vmax=max_value_allowed_before_black)

    # Add values and background color for each cell
    for i in range(filled_array.shape[0]):
        for j in range(filled_array.shape[1]):
            value = filled_array[i, j]
            if value < max_value_allowed_before_black:
                textcolour = 'black'
            else:
                textcolour = 'white'
            if value>1.0:
                presicion = 1
            else:
                presicion = 4
            ax.text(j, i, f'{value:.{presicion}f}', ha="center", va="center", color=textcolour, weight='bold')

    # Set axis labels and ticks
    ax.set_xticks(np.arange(filled_array.shape[1]))
    ax.set_yticks(np.arange(filled_array.shape[0]))
    ax.set_xticklabels(["1e-3", "1e-4", "1e-5", "1e-6"])
    ax.set_yticklabels(["1e-3", "1e-4", "1e-5", "1e-6"])

    # Set axis labels
    ax.set_xlabel(r'$\epsilon_{RES}$', fontsize=14)
    ax.set_ylabel(r'$\epsilon_{SOL}$',  fontsize=14)

    cbar = plt.colorbar(im, ax=ax)
    if not os.path.exists(store_path):
        os.makedirs(store_path)
    plt.savefig(store_path+f'{title}.pdf',bbox_inches='tight')
    #plt.show()

# def plot_rom_fom_numpy_array(filled_array, title, store_path):

#     # Define the colors for the colormap
#     colors = [(0, 1, 0), (1, 1, 0), (1, 0, 0)]  # Green to Yellow to Red

#     # Create the colormap
#     cmap = LinearSegmentedColormap.from_list('green_to_red', colors, N=256)

#     max_value_allowed_before_black = 250

#     # Set the color for values below and above a threshold
#     cmap.set_under(color='black')
#     cmap.set_over(color='black')

#     # Plotting
#     fig, ax = plt.subplots(1, 1, figsize=(4, 1.5))

#     im = ax.imshow(filled_array, cmap=cmap, aspect='auto', vmin=0, vmax=max_value_allowed_before_black)

#     # Add values and background color for each cell
#     for i in range(filled_array.shape[0]):
#         for j in range(filled_array.shape[1]):
#             value = filled_array[i, j]
#             if value < max_value_allowed_before_black:
#                 textcolour = 'black'
#             else:
#                 textcolour = 'white'
#             if value>1.0:
#                 presicion = 1
#             else:
#                 presicion = 4
#             ax.text(j, i, f'{value:.{presicion}f}', ha="center", va="center", color=textcolour, weight='bold')

#     # Set axis labels and ticks
#     ax.set_xticks(np.arange(filled_array.shape[1]))
#     ax.set_yticks(np.arange(filled_array.shape[0]))
#     ax.set_xticklabels([r"$e(y^*_{FOM}, y^*_{ROM})$", r"$e(\mathbf{S}_{FOM}, \mathbf{S}_{ROM})$"])
#     ax.set_yticklabels(["1e-3", "1e-4", "1e-5", "1e-6"])

#     # Set axis labels
#     #ax.set_xlabel(r'$\epsilon_{RES}$', fontsize=14)
#     ax.set_ylabel(r'$\epsilon_{SOL}$',  fontsize=14)

#     cbar = plt.colorbar(im, ax=ax)

#     plt.savefig(store_path+f'{title}.pdf',bbox_inches='tight')
#     #plt.show()
















def plot_average_errors_numpy_array(filled_array, title, store_path):

    # Define the colors for the colormap
    colors = [(0, 1, 0), (1, 1, 0), (1, 0, 0)]  # Green to Yellow to Red

    # Create the colormap
    cmap = LinearSegmentedColormap.from_list('green_to_red', colors, N=256)

    max_value_allowed_before_black = 250

    # Set the color for values below and above a threshold
    cmap.set_under(color='black')
    cmap.set_over(color='black')

    # Plotting
    fig, ax = plt.subplots(1, 1, figsize=(4, 4))

    im = ax.imshow(filled_array, cmap=cmap, aspect='auto', vmin=0, vmax=max_value_allowed_before_black)

    # Add values and background color for each cell
    for i in range(filled_array.shape[0]):
        for j in range(filled_array.shape[1]):
            value = filled_array[i, j]
            if value < max_value_allowed_before_black:
                textcolour = 'black'
            else:
                textcolour = 'white'
            if value>1.0:
                presicion = 1
            else:
                presicion = 4
            ax.text(j, i, f'{value:.{presicion}f}', ha="center", va="center", color=textcolour, weight='bold')

    # Set axis labels and ticks
    ax.set_xticks(np.arange(filled_array.shape[1]))
    ax.set_yticks(np.arange(filled_array.shape[0]))
    ax.set_xticklabels(["(ROM)", "1e-3", "1e-4", "1e-5", "1e-6"])
    ax.set_yticklabels(["1e-3", "1e-4", "1e-5", "1e-6"])

    # Set axis labels
    ax.set_xlabel(r'$\epsilon_{RES}$', fontsize=14)
    ax.set_ylabel(r'$\epsilon_{SOL}$',  fontsize=14)

    cbar = plt.colorbar(im, ax=ax)
    if not os.path.exists(store_path):
        os.makedirs(store_path)
    plt.savefig(store_path+f'{title}.pdf',bbox_inches='tight')
    #plt.show()

def plot_rom_fom_numpy_array(filled_array, title, store_path):

    # Define the colors for the colormap
    colors = [(0, 1, 0), (1, 1, 0), (1, 0, 0)]  # Green to Yellow to Red

    # Create the colormap
    cmap = LinearSegmentedColormap.from_list('green_to_red', colors, N=256)

    max_value_allowed_before_black = 250

    # Set the color for values below and above a threshold
    cmap.set_under(color='black')
    cmap.set_over(color='black')

    # Plotting
    fig, ax = plt.subplots(1, 1, figsize=(4, 1.5))

    im = ax.imshow(filled_array, cmap=cmap, aspect='auto', vmin=0, vmax=max_value_allowed_before_black)

    # Add values and background color for each cell
    for i in range(filled_array.shape[0]):
        for j in range(filled_array.shape[1]):
            value = filled_array[i, j]
            if value < max_value_allowed_before_black:
                textcolour = 'black'
            else:
                textcolour = 'white'
            if value>1.0:
                presicion = 1
            else:
                presicion = 4
            ax.text(j, i, f'{value:.{presicion}f}', ha="center", va="center", color=textcolour, weight='bold')

    # Set axis labels and ticks
    ax.set_xticks(np.arange(filled_array.shape[1]))
    ax.set_yticks(np.arange(filled_array.shape[0]))
    ax.set_xticklabels([r"$e(y^*_{FOM}, y^*_{ROM})$", r"$e(\mathbf{S}_{FOM}, \mathbf{S}_{ROM})$"])
    ax.set_yticklabels(["1e-3", "1e-4", "1e-5", "1e-6"])

    # Set axis labels
    #ax.set_xlabel(r'$\epsilon_{RES}$', fontsize=14)
    ax.set_ylabel(r'$\epsilon_{SOL}$',  fontsize=14)

    cbar = plt.colorbar(im, ax=ax)
    if not os.path.exists(store_path):
        os.makedirs(store_path)
    plt.savefig(store_path+f'{title}.pdf',bbox_inches='tight')
    #plt.show()



















def plot_number_of_elements_numpy_array(filled_array, title, store_path, number_of_elems):

    # Define the colors for the colormap
    colors = [(1, 1, 1), (1, 0, 0)]  # Green to Yellow to Red

    # Create the colormap
    cmap = LinearSegmentedColormap.from_list('green_to_red', colors, N=256)

    max_value_allowed_before_black = number_of_elems

    # Set the color for values below and above a threshold
    cmap.set_under(color='black')
    cmap.set_over(color='black')

    # Plotting
    fig, ax = plt.subplots(1, 1, figsize=(4, 4))

    im = ax.imshow(filled_array, cmap=cmap, aspect='auto', vmin=0, vmax=max_value_allowed_before_black)

    # Add values and background color for each cell
    for i in range(filled_array.shape[0]):
        for j in range(filled_array.shape[1]):
            value = filled_array[i, j]
            if value < max_value_allowed_before_black:
                textcolour = 'black'
            else:
                textcolour = 'white'
            if value>1.0:
                presicion = 1
            else:
                presicion = 4
            ax.text(j, i, f'{int(value)}', ha="center", va="center", color=textcolour, weight='bold')

    # Set axis labels and ticks
    ax.set_xticks(np.arange(filled_array.shape[1]))
    ax.set_yticks(np.arange(filled_array.shape[0]))
    ax.set_xticklabels(["1e-3", "1e-4", "1e-5", "1e-6"])
    ax.set_yticklabels(["1e-3", "1e-4", "1e-5", "1e-6"])

    # Set axis labels
    ax.set_xlabel(r'$\epsilon_{RES}$', fontsize=14)
    ax.set_ylabel(r'$\epsilon_{SOL}$',  fontsize=14)

    cbar = plt.colorbar(im, ax=ax)
    if not os.path.exists(store_path):
        os.makedirs(store_path)
    plt.savefig(store_path+f'{title}.pdf',bbox_inches='tight')
    #plt.show()





def plot_rom_fom_numpy_array(filled_array, title, store_path):

    # Define the colors for the colormap
    colors = [(0, 1, 0), (1, 1, 0), (1, 0, 0)]  # Green to Yellow to Red

    # Create the colormap
    cmap = LinearSegmentedColormap.from_list('green_to_red', colors, N=256)

    max_value_allowed_before_black = 250

    # Set the color for values below and above a threshold
    cmap.set_under(color='black')
    cmap.set_over(color='black')

    # Plotting
    fig, ax = plt.subplots(1, 1, figsize=(4, 1.5))

    im = ax.imshow(filled_array, cmap=cmap, aspect='auto', vmin=0, vmax=max_value_allowed_before_black)

    # Add values and background color for each cell
    for i in range(filled_array.shape[0]):
        for j in range(filled_array.shape[1]):
            value = filled_array[i, j]
            if value < max_value_allowed_before_black:
                textcolour = 'black'
            else:
                textcolour = 'white'
            if value>1.0:
                presicion = 1
            else:
                presicion = 4
            ax.text(j, i, f'{value:.{presicion}f}', ha="center", va="center", color=textcolour, weight='bold')

    # Set axis labels and ticks
    ax.set_xticks(np.arange(filled_array.shape[1]))
    ax.set_yticks(np.arange(filled_array.shape[0]))
    ax.set_xticklabels([r"$e(\bm{v}^*_y{_{FOM}}, \bm{v}^*_y{_{ROM}})$", r"$e(\bm{S}_{FOM}, \bm{S}_{ROM})$"])
    ax.set_yticklabels(["1e-3", "1e-4", "1e-5", "1e-6"])

    # Set axis labels
    #ax.set_xlabel(r'$\epsilon_{RES}$', fontsize=14)
    ax.set_ylabel(r'$\epsilon_{SOL}$',  fontsize=14)

    cbar = plt.colorbar(im, ax=ax)
    if not os.path.exists(store_path):
        os.makedirs(store_path)
    plt.savefig(store_path+f'{title}.pdf',bbox_inches='tight')
    #plt.show()




















def plot_QoI_errors_ROM_HROM(solution_svd,residuals_svd,example,model,stage, store_path):


    if stage == "train":
        add_to_name = ''
    elif stage == "test":
        add_to_name = '_test'

    filled_array = np.empty((len(solution_svd),len(residuals_svd)))

    title = f'Example_{example}_'+model+'_'+stage+'_QoI_ROM_vs_HROM'

    for i in range(len(solution_svd)):
        svd = solution_svd[i]
        ROM, _ = load_rom_data(example,model,add_to_name, svd)
        for j in range(len(residuals_svd)):
            res = residuals_svd[j]
            HROM, _ = load_hrom_data(example,model,add_to_name, svd,res)
            filled_array[i,j] = GetPercentualError(ROM,HROM)

    plot_numpy_array(filled_array, title, store_path)


def plot_QoI_and_Solution_errors_FOM_ROM(solution_svd,example,model,stage, store_path):

    if stage == "train":
        add_to_name = ''
    elif stage == "test":
        add_to_name = '_test'

    filled_array = np.empty((len(solution_svd),2))
    title = f'Example_{example}_'+model+'_'+stage+'_FOM_vs_ROM'

    FOM = np.load(f'./Example_{example}/' +f'{model}/'+f'Velocity_y{add_to_name}.npy')

    for i in range(len(solution_svd)):
        svd = solution_svd[i]
        ROM, _ = load_rom_data(example,model,add_to_name, svd)
        filled_array[i,0] = GetPercentualError(FOM,ROM)

    FOM = np.load(f'./Example_{example}/' +f'{model}/'+f'SnapshotMatrix{add_to_name}.npy')

    for i in range(len(solution_svd)):
        svd = solution_svd[i]
        ROM = load_rom_snapshots(example,model,add_to_name, svd)
        filled_array[i,1] = GetPercentualError(FOM,ROM)

    plot_rom_fom_numpy_array(filled_array, title, store_path)



def plot_QoI_errors_FOM_HROM(solution_svd,residuals_svd,example,model,stage, store_path):


    if stage == "train":
        add_to_name = ''
    elif stage == "test":
        add_to_name = '_test'

    filled_array = np.empty((len(solution_svd),len(residuals_svd)))

    title = f'Example_{example}_'+model+'_'+stage+'_QoI_FOM_vs_HROM'

    FOM =  np.load(f'./Example_{example}/' +f'{model}/'+f'Velocity_y{add_to_name}.npy')

    for i in range(len(solution_svd)):
        svd = solution_svd[i]
        for j in range(len(residuals_svd)):
            res = residuals_svd[j]
            HROM, _= load_hrom_data(example,model,add_to_name, svd,res)
            filled_array[i,j] = GetPercentualError(FOM,HROM)

    plot_numpy_array(filled_array, title, store_path)


def plot_solution_errors_FOM_HROM(solution_svd,residuals_svd,example,model,stage, store_path):

    if stage == "train":
        add_to_name = ''
    elif stage == "test":
        add_to_name = '_test'

    filled_array = np.empty((len(solution_svd),len(residuals_svd)))
    title = f'Example_{example}_'+model+'_'+stage+'_Solution_FOM_vs_HROM'

    FOM =  np.load(f'./Example_{example}/' +f'{model}/'+f'SnapshotMatrix{add_to_name}.npy')

    for i in range(len(solution_svd)):
        svd = solution_svd[i]
        for j in range(len(residuals_svd)):
            res = residuals_svd[j]
            HROM = load_hrom_snapshots(example,model,add_to_name, svd,res)
            filled_array[i,j] = GetPercentualError(FOM,HROM)

    plot_numpy_array(filled_array, title, store_path)

def plot_solution_errors_ROM_HROM(solution_svd,residuals_svd,example,model,stage, store_path):

    if stage == "train":
        add_to_name = ''
    elif stage == "test":
        add_to_name = '_test'

    filled_array = np.empty((len(solution_svd),len(residuals_svd)))

    title = f'Example_{example}_'+model+'_'+stage+'_Solution_ROM_vs_HROM'

    for i in range(len(solution_svd)):
        svd = solution_svd[i]
        ROM = load_rom_snapshots(example,model,add_to_name, svd)
        for j in range(len(residuals_svd)):
            res = residuals_svd[j]
            HROM = load_hrom_snapshots(example,model,add_to_name, svd,res)
            filled_array[i,j] = GetPercentualError(ROM,HROM)

    plot_numpy_array(filled_array, title, store_path)



def plot_errors_ROM_vs_HROM(examples_to_plot, models_to_plot, store_path, solution_svd, residuals_svd):

    for example in examples_to_plot:
        for model in models_to_plot:

            #trajectory_1 and trajectory 2 are train or test depending on the model run
            # - Example 1: Trajectory 1 is train, Trajectory 2 is test
            # - Example 2: Trajectory 2 is train, Trajectory 1 is test
            # - Example 3. Trajectory 1 and 2 are train. Trajectory 3 is Test
            if example ==4:
                stages = ['test']
            else:
                stages = ['train', 'test']
            for stage in stages:
                plot_QoI_errors_ROM_HROM(solution_svd,residuals_svd,example,model,stage, store_path)
                plot_QoI_errors_FOM_HROM(solution_svd,residuals_svd,example,model,stage, store_path)
                # plot_solution_errors_ROM_HROM(solution_svd,residuals_svd,example,model,stage, store_path)
                # plot_solution_errors_FOM_HROM(solution_svd,residuals_svd,example,model,stage, store_path)



def plot_errors_FOM_vs_ROM(examples_to_plot, models_to_plot, store_path, solution_svd):

    for example in examples_to_plot:
        for model in models_to_plot:

            #trajectory_1 and trajectory 2 are train or test depending on the model run
            # - Example 1: Trajectory 1 is train, Trajectory 2 is test
            # - Example 2: Trajectory 2 is train, Trajectory 1 is test
            # - Example 3. Trajectory 1 and 2 are train. Trajectory 3 is Test
            if example ==4:
                stages = ['test']
            else:
                stages = ['train', 'test']
            for stage in stages:
                plot_QoI_and_Solution_errors_FOM_ROM(solution_svd,example,model,stage, store_path)





def QoIErrorsArrayAddition(solution_svd,example,model,stage, residuals_svd, QoI_array):

    if stage == "train":
        add_to_name = ''
    elif stage == "test":
        add_to_name = '_test'

    FOM = np.load(f'./Example_{example}/' +f'{model}/'+f'Velocity_y{add_to_name}.npy')

    for i in range(len(solution_svd)):
        svd = solution_svd[i]
        ROM, _ = load_rom_data(example,model,add_to_name, svd)
        QoI_array[i,0] += GetPercentualError(FOM,ROM)
        for j in range(len(residuals_svd)):
            res = residuals_svd[j]
            HROM, _ = load_hrom_data(example,model,add_to_name, svd,res)
            QoI_array[i,j+1] += GetPercentualError(FOM,HROM)

    return QoI_array






def SolutionErrorsArrayAddition(solution_svd,example,model,stage, residuals_svd, Solution_array):

    if stage == "train":
        add_to_name = ''
    elif stage == "test":
        add_to_name = '_test'

    FOM =  np.load(f'./Example_{example}/' +f'{model}/'+f'SnapshotMatrix{add_to_name}.npy')

    for i in range(len(solution_svd)):
        svd = solution_svd[i]
        ROM = load_rom_snapshots(example,model,add_to_name, svd)
        Solution_array[i,0] += GetPercentualError(FOM,ROM)
        for j in range(len(residuals_svd)):
            res = residuals_svd[j]
            HROM = load_hrom_snapshots(example,model,add_to_name, svd,res)
            Solution_array[i,j+1] += GetPercentualError(FOM,HROM)

    return Solution_array






def plot_average_errors_FOM_ROM_HROM_QoI_and_Solution(examples_to_plot, models_to_plot, store_path, solution_svd, residuals_svd):




    examples = [[1], [2], [3,4], [1], [2], [3,4]]
    cases = [['Affine'],['Affine'],['Affine'],['FFD_RBF'],['FFD_RBF'],['FFD_RBF']]
    for examples_to_plot, models_to_plot in zip(examples, cases):
        number_of_cases=0
        QoI_array= np.zeros((4,5))
        Solution_array= np.zeros((4,5))
        for example in examples_to_plot:
            for model in models_to_plot:

                #trajectory_1 and trajectory 2 are train or test depending on the model run
                # - Example 1: Trajectory 1 is train, Trajectory 2 is test
                # - Example 2: Trajectory 2 is train, Trajectory 1 is test
                # - Example 3. Trajectory 1 and 2 are train. Trajectory 3 is Test
                if example ==4:
                    stages = ['test']
                else:
                    stages = ['train', 'test']
                for stage in stages:
                    QoI_array = QoIErrorsArrayAddition(solution_svd,example,model,stage, residuals_svd, QoI_array)
                    #Solution_array = SolutionErrorsArrayAddition(solution_svd,example,model,stage, residuals_svd, Solution_array)

                number_of_cases+=1

        plot_average_errors_numpy_array(QoI_array/number_of_cases, f"QoI_{model}_Ex_{example}_AverageErrors", store_path)
        #plot_average_errors_numpy_array(Solution_array/number_of_cases, f"Solution_{model}_Ex_{example}_AverageErrors", store_path)



def plot_residuals_singular_values(examples_to_plot, models_to_plot,store_path, solution_svd, residuals_svd):

    examples_to_plot = [1,2,3]




    for example in examples_to_plot:
        for model in models_to_plot:
            for tol in solution_svd:
                sigma =  np.load(f'./Example_{example}/' +f'{model}/'+f'global_singular_values_{tol}.npy')
                plt.plot(sigma/sigma[0], linewidth = 3, label = r"$\epsilon_{SOL}=$" + "{:.0e}".format(tol), alpha=0.9) #alpha=0.5, #alpha=0.5
            plt.ylim(1e-17, 1.1e1)
            plt.yscale('log')
            plt.ylabel(r'$\frac{\sigma_i }{\sigma_1}$ log scale',size=15)
            plt.xlabel(r'index $i$')
            plt.legend()
            plt.grid()
            if not os.path.exists(store_path):
                os.makedirs(store_path)
            plt.savefig(f'{store_path}singular_values_residuals_Ex_{example}_{model}.pdf')
            #plt.show()



def plot_solutions_singular_values(examples_to_plot, models_to_plot,store_path, solution_svd, residuals_svd):


    for example in examples_to_plot:
        sigma_affine =  np.load(f'./Example_{example}/Affine/'+f'singular_values.npy')
        sigma_nonlinear =  np.load(f'./Example_{example}/FFD_RBF/'+f'singular_values.npy')
        plt.plot(sigma_affine/sigma_affine[0],'r',  marker='s',markevery=10 , linewidth = 1, label="Affine") #alpha=0.9
        plt.plot(sigma_nonlinear/sigma_nonlinear[0], 'b', marker='s',markevery=10 , linewidth = 1, label="FFD+RBF") #alpha=0.9
        plt.yscale('log')
        plt.ylabel(r'$\frac{\sigma_i }{\sigma_1}$ log scale',size=15)
        plt.xlabel(r'index $i$')
        plt.legend()
        plt.grid()
        if not os.path.exists(store_path):
            os.makedirs(store_path)
        plt.savefig(f'{store_path}singular_values_solution_Ex_{example}.pdf')
        #plt.show()





    s_affine = np.load('./Analytic_Mapping/ROM/global_singular_values.npy')
    s_nonlinear = np.load('./FFD_plus_RBF/ROM/global_singular_values.npy')

    plt.plot(s_affine,'r',  marker='s',markevery=10 , linewidth = 1, label="Affine") #alpha=0.9
    plt.plot(s_nonlinear, 'b', marker='s',markevery=10 , linewidth = 1, label="FFD+RBF") #alpha=0.9

    plt.yscale('log')
    plt.ylabel(r'$\frac{\sigma_i }{\sigma_1}$ log scale',size=15)
    plt.legend()
    plt.grid()
    plt.savefig('singular_values_decay.pdf')
    #plt.show()




def plot_number_of_selected_elements():

    ########      Example 1     ########

    a = np.array([[60, 143, 243, 388],
                  [140, 354, 621, 930],
                  [233, 555, 1033, 1652],
                  [348, 802, 1442, 2238]
        ])
    b = np.array([[174, 351, 561, 819],
                  [268, 545, 930, 1412],
                  [381, 740, 1232, 1873],
                  [541, 1018, 1659, 2428]
        ])

    #############################################


    ########      Example 2     ########

    c = np.array([[103, 303, 551, 898],
                  [241, 703, 1345, 2078],
                  [353, 945, 1733, 2618],
                  [490, 1255, 2204, 3142]
        ])

    d = np.array([[219, 446, 708, 1039],
                  [318, 652, 1094, 1642],
                  [446, 877, 1440, 2144],
                  [623, 1195, 1924, 2467]
        ])

    #############################################

    ########      Example 3     ########

    e = np.array([[131, 381, 705, 1139],
                  [326, 866, 1617, 2472],
                  [475, 1241, 2233, 3219],
                  [590, 1520, 2651, 3615]
        ])
    f = np.array([[331, 672, 1102, 1672],
                  [501, 965, 1601, 2358],
                  [676, 1254, 2020, 2866],
                  [903, 1657, 2591, 3489]
        ])

    #############################################

    {'1_affine':a,'1_ffd_rbf':b,'2_affine':c,'2_ffd_rbf':d,'3_affine':e,'3_ffd_rbf':f }

    plot_number_of_elements_numpy_array(a, '1_affine', './NumberOfElementsSelected/', 5147)
    plot_number_of_elements_numpy_array(b, '1_ffd_rbf',  './NumberOfElementsSelected/', 5412)
    plot_number_of_elements_numpy_array(c, '2_affine',  './NumberOfElementsSelected/', 5147)
    plot_number_of_elements_numpy_array(d, '2_ffd_rbf',  './NumberOfElementsSelected/',5412)
    plot_number_of_elements_numpy_array(e, '3_affine',  './NumberOfElementsSelected/', 5147)
    plot_number_of_elements_numpy_array(f, '3_ffd_rbf',  './NumberOfElementsSelected/',5412)



def plot_speedups_in_loop(title, store_path):



    # data ignoring some cases explote
    # Example 1 Affine
    if title == 'Example_1_Affine':
        data_array = np.array([
            [[7.12, 0], [276.13, 1], [154.45, 1], [126.21, 1], [84.16, 1]],
            [[6.21, 0], [94.23, 1], [50.84, 1], [30.65, 1], [20.48, 1]],
            [[5.54, 0], [30.11, 1], [13.09, 0], [9.83, 0], [9.04, 0]],
            [[5.21, 0], [12.02, 0], [10.05, 0], [9.17, 0], [8.81, 0]]
        ])

    # Example 1 Nonlinear
    elif title == 'Example_1_Nonlinear':
        data_array = np.array([
            [[4.01, 0], [57.39, 1], [28.72, 1], [21.95, 1], [15.09, 1]],
            [[3.84, 0], [20.11, 1], [11.14, 1], [7.35, 0], [6.40, 0]],
            [[3.29, 0], [7.51, 0], [7.33, 0], [5.77, 0], [5.51, 0]],
            [[2.97, 0], [6.04, 0], [5.58, 0], [5.52, 0], [4.51, 0]]
        ])

    #Example 2 Affine
    elif title == 'Example_2_Affine':
        data_array = np.array([
            [[7.4, 0], [152.7, 1], [76.14, 1], [47.73, 1], [33.17, 1]],
            [[6.0, 0], [36.44, 1], [12.34, 1], [10.73, 0], [9.72, 0]],
            [[5.9, 0], [14.32, 0], [10.6, 0], [10.1, 0], [9.7, 0]],
            [[5.5, 0], [8.92, 0], [8.80, 0], [8.60, 0], [8.0, 0]]
        ])

    #Example 2 Nonlinear
    elif title == 'Example_2_Nonlinear':
        data_array = np.array([
            [[3.64, 0], [44.07, 1], [26.72, 1], [16.57, 1], [12.29, 1]],
            [[3.29, 0], [15.49, 1], [9.34, 1], [6.19, 0], [5.91, 0]],
            [[3.19, 0], [6.00, 0], [5.80, 0], [5.78, 0], [5.11, 0]],
            [[2.97, 0], [5.04, 0], [4.83, 0], [4.79, 0], [4.67, 0]]
        ])

    # Example 3 Affine
    elif title == 'Example_3_Affine':
        data_array = np.array([
            [[8.83, 0], [164.02, 1], [69.76, 1], [42.37, 1], [26.41, 1]],
            [[7.80, 0], [24.47, 1], [13.73, 0], [13.08, 0], [12.92, 0]],
            [[7.33, 0], [12.03, 0], [11.94, 0], [11.72, 0], [11.26, 0]],
            [[6.36, 0], [9.78, 0], [9.77, 0], [9.51, 0], [9.23, 0]]
        ])

    # #Example 3 Nonlinear
    elif title == 'Example_3_Nonlinear':
        data_array = np.array([
            [[3.46, 0], [25.09, 1], [12.94, 1], [7.73, 0], [6.66, 0]],
            [[3.39, 0], [6.06, 0], [5.34, 0], [5.25, 0], [5.01, 0]],
            [[3.00, 0], [5.25, 0], [5.18, 0], [5.04, 0], [4.81, 0]],
            [[2.63, 0], [3.81, 0], [3.65, 0], [3.51, 0], [3.48, 0]]
        ])
    else:
        error

    # Define the colors for the colormap
    colors = [(1, 0, 0), (1, 1, 0),(0, 1, 0)]  # Red to Yellow to Green

    # Create the colormap
    cmap = LinearSegmentedColormap.from_list('green_to_red', colors, N=256)

    max_value_allowed_before_black = np.max(data_array)+1

    # Set the color for values below and above a threshold
    cmap.set_under(color='black')
    cmap.set_over(color='black')

    # Plotting
    fig, ax = plt.subplots(1, 1, figsize=(6, 2.5))

    im = ax.imshow(data_array[:,:,0], cmap=cmap, aspect='auto', vmin=0, vmax=max_value_allowed_before_black)

    # Add values and background color for each cell
    for i in range(data_array.shape[0]):
        for j in range(data_array.shape[1]):
            value = data_array[i, j,0]
            if value < max_value_allowed_before_black:
                textcolour = 'black'
            else:
                textcolour = 'white'
            if value>1.0:
                presicion = 1
            else:
                presicion = 4
            ax.text(j, i, f'{value:.{presicion}f}', ha="center", va="center", color=textcolour, weight='bold')

    # Set axis labels and ticks
    ax.set_xticks(np.arange(data_array[:,:,0].shape[1]))
    ax.set_yticks(np.arange(data_array[:,:,0].shape[0]))
    ax.set_xticklabels(["(ROM)", "1e-3", "1e-4", "1e-5", "1e-6"])
    ax.set_yticklabels(["1e-3", "1e-4", "1e-5", "1e-6"])

    # Set axis labels
    ax.set_xlabel(r'$\epsilon_{RES}$', fontsize=14)
    ax.set_ylabel(r'$\epsilon_{SOL}$',  fontsize=14)

    cbar = plt.colorbar(im, ax=ax)
    if not os.path.exists(store_path):
        os.makedirs(store_path)
    plt.savefig(store_path+f'{title}.pdf',bbox_inches='tight')
    #plt.show()




def plot_speeups():

    titles = ['Example_1_Affine', 'Example_1_Nonlinear', 'Example_2_Affine', 'Example_2_Nonlinear', 'Example_3_Affine', 'Example_3_Nonlinear']

    for title in titles:
        plot_speedups_in_loop(title, './SpeedUps/')



if __name__=='__main__':

    examples_to_plot = [1,2,3,4] #4 here is test for model with both trajectory 1 and 2 included

    models_to_plot = ['Affine', 'FFD_RBF']

    store_path = './'

    solution_svd = [1e-3,1e-4,1e-5,1e-6]

    residuals_svd = [1e-3,1e-4,1e-5,1e-6]

    plot_errors_ROM_vs_HROM(examples_to_plot, models_to_plot, './FOM_AND_ROM_VS_HROM/', solution_svd, residuals_svd)

    #plot_errors_FOM_vs_ROM(examples_to_plot, models_to_plot, './FOM_VS_ROM/', solution_svd)

    #plot_average_errors_FOM_ROM_HROM_QoI_and_Solution(examples_to_plot, models_to_plot, './EverageError_QoI_and_Solution/', solution_svd, residuals_svd)

    plot_residuals_singular_values(examples_to_plot, models_to_plot, './ResidualsSingularValues/', solution_svd, residuals_svd)

    #plot_solutions_singular_values(examples_to_plot, models_to_plot,'./SolutionSingularValues/',solution_svd, residuals_svd)

    plot_number_of_selected_elements()

    plot_speeups()