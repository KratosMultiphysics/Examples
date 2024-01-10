import numpy as np
from matplotlib import pyplot as plt



if __name__=='__main__':


    vy = np.load('Results/Velocity_y.npy')
    w = np.load('Results/narrowing.npy')
    vy_rom = np.load(f'Results/y_velocity_ROM.npy')
    w_rom = np.load(f'Results/narrowing_ROM.npy')
    vy_hrom = np.load(f'Results/y_velocity_HROM.npy')
    w_hrom = np.load(f'Results/narrowing_HROM.npy')


    plt.plot(vy, w, 'k*-', label = 'FOM', linewidth = 3)
    plt.plot(vy_rom, w_rom, 'b*-', label = 'ROM')
    plt.plot(vy_hrom, w_hrom, 'r*-', label = 'HROM')
    plt.title(f'ROMs VS FOM')
    plt.legend()
    plt.xlabel('velocity y', size=20)
    plt.ylabel('narrowing w',size=20)
    plt.show()
