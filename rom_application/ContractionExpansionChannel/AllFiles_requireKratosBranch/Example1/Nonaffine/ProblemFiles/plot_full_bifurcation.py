import numpy as np
from matplotlib import pyplot as plt



if __name__=='__main__':


    vy = np.load('Results/Velocity_y.npy')
    w = np.load('Results/narrowing.npy')
    vy_rom = np.load(f'Results/y_velocity_ROM.npy')
    w_rom = np.load(f'Results/narrowing_ROM.npy')
    vy_hrom = np.load(f'Results/y_velocity_HROM.npy')
    w_hrom = np.load(f'Results/narrowing_HROM.npy')

    plt.rc('text', usetex=True)
    plt.rc('font', family='serif')

    plt.plot(vy, w, 'b', label = 'FOM', linewidth = 3, alpha=0.5) #linewidth = 3
    plt.plot(vy_rom, w_rom, 'r', label = 'ROM',  linewidth = 3, alpha=0.5)
    plt.plot(vy_hrom, w_hrom, 'm', label = 'HROM',  linewidth = 3, alpha=0.5)

    plt.legend()
    #plt.grid()
    # plt.xticks(np.arange(-3.5,0.25,0.25))  #TODO the ticks are not easily beautyfied, do it later :)
    # plt.yticks(np.arange(0,3.1,0.25))
    plt.xlabel(r'$v_y^*$', size=15, fontweight='bold')
    plt.ylabel(r'$w_c$',size=15,fontweight='bold')

    plt.savefig('Results/fom_vs_rom_vs_hrom')
    plt.show()