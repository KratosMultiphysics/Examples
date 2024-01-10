import numpy as np
from matplotlib import pyplot as plt



if __name__=='__main__':
    #library for passing arguments to the script from bash
    from sys import argv


    tol_svd= argv[1]
    to_svd_res= argv[2]

    print(tol_svd)
    print(to_svd_res)


    tol_svd = [1e-3]
    to_svd_res = [1e-4,1e-5,1e-6]#1e-3,





    #plt.title(r'Singular Values for matrix $ S^{(2)} $', fontsize=15, fontweight='bold')
    #plt.title(r'$\alpha $ \textbf{AA}!', fontsize=16, color='r')
    #plt.title(f'ROM VS FOM')


    plt.rc('text', usetex=True)
    plt.rc('font', family='serif')


    vy = np.load('Results/Velocity_y.npy')
    w = np.load('Results/narrowing.npy')
    plt.plot(vy, w, 'b', label = 'FOM', linewidth = 1.5 ) #linewidth = 3, alpha=0.5
    markers=['s','^','+','H','*']
    counter = 0
    for svd in tol_svd:
        vy_rom = np.load(f'Results/y_velocity_ROM_{svd}.npy')
        w_rom = np.load(f'Results/narrowing_ROM_{svd}.npy')
        plt.plot(vy_rom, w_rom, label = f"ROM\_{svd}", linewidth = 1.5) #alpha=0.5
        for res in to_svd_res:
            vy_rom = np.load(f'Results/y_velocity_HROM_{svd}_{res}.npy')
            w_rom = np.load(f'Results/narrowing_HROM_{svd}_{res}.npy')
            plt.plot(vy_rom, w_rom, marker=markers[counter],markevery=50,label = f"HROM\_{svd}\_{res}", linewidth = 1.5) #alpha=0.5
            counter+=1

    #plt.title(r'FOM vs ROM', fontsize=20, fontweight='bold')
    plt.legend()
    plt.grid()
    # plt.xticks(np.arange(-3.5,0.25,0.25))  #TODO the ticks are not easily beautyfied, do it later :)
    # plt.yticks(np.arange(0,3.1,0.25))
    plt.xlabel(r'$v_y^*$', size=15, fontweight='bold')
    plt.ylabel(r'$w_c$',size=15,fontweight='bold')

    plt.savefig('Results/fom_vs_rom')
    plt.show()




    # import numpy as np
    # import matplotlib.pyplot as plt


    # # Example data
    # t = np.arange(0.0, 1.0 + 0.01, 0.01)
    # s = np.cos(4 * np.pi * t) + 2

    # plt.rc('text', usetex=True)
    # plt.rc('font', family='serif')
    # plt.plot(t, s)

    # plt.xlabel(r'\textbf{time} (s)')
    # plt.ylabel(r'\textit{voltage} (mV)',fontsize=16)
    # plt.title(r"\TeX\ is Number "
    #         r"$\displaystyle\sum_{n=1}^\infty\frac{-e^{i\pi}}{2^n}$!",
    #         fontsize=16, color='gray')
    # # Make room for the ridiculously large title.
    # plt.subplots_adjust(top=0.8)

    # plt.savefig('tex_demo')
    # plt.show()