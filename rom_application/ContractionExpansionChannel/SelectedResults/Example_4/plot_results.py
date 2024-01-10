import numpy as np
from matplotlib import pyplot as plt
plt.rc('text', usetex=True)
plt.rc('font', family='serif')





def update_plot_ranges(min_x, min_y, max_x, max_y, v,w):

    if np.max(v)>max_x and np.max(v)<4:
        max_x = np.max(v)

    if np.max(w)>max_y:
        max_y = np.max(w)

    if np.min(v)<min_x and np.min(v)>-4:
        min_x = np.min(v)

    if np.min(w)<min_y:
        min_y =np.min(w)


    return min_x, min_y, max_x, max_y




def load_rom_data(resuts_path, add_to_name, svd):


    if resuts_path=='./Affine/':
        vy_rom = np.load(resuts_path+f'y_velocity_ROM_{svd}{add_to_name}.npy')
        w_rom = np.load(resuts_path+f'narrowing_ROM_{svd}{add_to_name}.npy')
    elif resuts_path=='./Nonlinear/':
        vy_rom = np.load(resuts_path+f'y_velocity_ROM{add_to_name}_{svd}.npy')
        w_rom = np.load(resuts_path+f'narrowing_ROM{add_to_name}_{svd}.npy')
    else:
        error

    return vy_rom,w_rom



def load_hrom_data(resuts_path, add_to_name, svd, res):


    if resuts_path=='./Affine/':
        vy_rom = np.load(resuts_path+f'y_velocity_HROM{add_to_name}_{svd}_{res}.npy')
        w_rom =  np.load(resuts_path+f'narrowing_HROM{add_to_name}_{svd}_{res}.npy')
    elif resuts_path=='./Nonlinear/':
        vy_rom =  np.load(resuts_path+f'y_velocity_HROM{add_to_name}_{svd}_{res}.npy')
        w_rom = np.load(resuts_path+f'narrowing_HROM{add_to_name}_{svd}_{res}.npy')
    else:
        error

    return vy_rom,w_rom






def reviewed_plot_hysteresis_rom_hrom(tol_svd,to_svd_res,resuts_path, trajectory):

    if trajectory == "train":
        add_to_name = ''
    elif trajectory == "test":
        add_to_name = '_test'

    colours = ['k','m','g','b','c','r','y']
    markers=['X','<','^','*','v','P','>','d','8','H']




    for svd in tol_svd:

        vy_FOM = np.load(resuts_path+f'Velocity_y{add_to_name}.npy')
        w_FOM = np.load(resuts_path+f'narrowing{add_to_name}.npy')

        min_x = 0
        max_x = 0
        min_y=0.7
        max_y=0.7

        min_x, min_y, max_x, max_y = update_plot_ranges(min_x, min_y, max_x, max_y, vy_FOM,w_FOM)

        vy_rom, w_rom = load_rom_data(resuts_path, add_to_name, svd)

        min_x, min_y, max_x, max_y = update_plot_ranges(min_x, min_y, max_x, max_y, vy_rom,w_rom)
        counter=0
        plt.plot(vy_FOM, w_FOM, 'k', label = 'FOM', linewidth = 5, alpha=0.4) #linewidth = 3, alpha=0.5
        plt.plot(vy_rom, w_rom, colours[counter], marker=markers[counter], markevery=50,label = r"$ROM \ \epsilon_{SOL}=$" + "{:.0e}".format(svd), alpha=0.9) #alpha=0.5, #alpha=0.5
        for res in to_svd_res:
            vy_rom,w_rom =  load_hrom_data(resuts_path, add_to_name, svd, res)
            # vy_rom = np.load(resuts_path+f'y_velocity_HROM{add_to_name}_{svd}_{res}.npy')
            # w_rom = np.load(resuts_path+f'narrowing_HROM{add_to_name}_{svd}_{res}.npy')
            min_x, min_y, max_x, max_y = update_plot_ranges(min_x, min_y, max_x, max_y, vy_rom,w_rom) #do not consider the HROM for the ranges, as some of them explote
            if np.max(np.abs(vy_rom))>10:
                alpha = 0.4
            else:
                alpha = 1
            plt.plot(vy_rom, w_rom, markevery=80+counter*15,
            label = r"$HROM \ \epsilon_{SOL}=$ " + "{:.0e}".format(svd) + r" ; $\epsilon_{RES}=$ "+"{:.0e}".format(res),
            linewidth = 1.5, marker=markers[counter], alpha=alpha) #alpha=0.5 marker=markers[counter]
            counter+=1
        counter+=1
        plt.xlabel(r'$v_y^*$', size=15)
        plt.ylabel(r'$w_c$',size=15)
        plt.xlim([min_x-0.05,max_x+0.05])
        plt.ylim([min_y-0.05,max_y+0.05])
        plt.grid()
        plt.legend(loc='upper left')
        plt.savefig(f'hysteresis_rom_vs_hrom_{svd}_{trajectory}.pdf')
        plt.show()



if __name__=='__main__':

    resuts_path = './Affine/' #'./Nonlinear/'  './Affine/'
    trajectory = "test" # test only

    tol_svd = [1e-3, 1e-4, 1e-5, 1e-6]
    to_svd_res = [1e-3, 1e-4, 1e-5, 1e-6]


    reviewed_plot_hysteresis_rom_hrom(tol_svd,to_svd_res,resuts_path, trajectory)


