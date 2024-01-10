#importing PyGeM tools
from pygem import FFD, RBF

import numpy as np

def set_up_phi():
    #creating a free form deformation object for each control domain
    ffd_up = FFD([2,5,2])  #3D box of control points
    ffd_down = FFD([2,5,2])  #3D box of control points

    #setting the centre and size of the upper box of control points
    ffd_down.box_origin = np.array([1.25, 0, 0.5])
    ffd_down.box_length = np.array([1, 1.25, 1])

    #setting the centre and size of the lower box of control points
    ffd_up.box_origin = np.array([1.25, 1.75, 0.5])
    ffd_up.box_length = np.array([1, 1.25, 1])

    return ffd_up, ffd_down


def phi(up,down,ffd_down,ffd_up,deformation_multiplier,scale_of_deformation):

    ### moving down free-form-deformation ###

    ffd_down.array_mu_x[0, 0, 0] = deformation_multiplier*scale_of_deformation * 0.0
    ffd_down.array_mu_x[0, 1, 0] = deformation_multiplier*scale_of_deformation * 0.04
    ffd_down.array_mu_x[0, 2, 0] = deformation_multiplier*scale_of_deformation * 0.06
    ffd_down.array_mu_x[0, 3, 0] = deformation_multiplier*scale_of_deformation * 0.04
    ffd_down.array_mu_x[0, 4, 0] = deformation_multiplier*scale_of_deformation * 0.0
    ffd_down.array_mu_x[0, 0, 1] = deformation_multiplier*scale_of_deformation * 0.0
    ffd_down.array_mu_x[0, 1, 1] = deformation_multiplier*scale_of_deformation * 0.04
    ffd_down.array_mu_x[0, 2, 1] = deformation_multiplier*scale_of_deformation * 0.06
    ffd_down.array_mu_x[0, 3, 1] = deformation_multiplier*scale_of_deformation * 0.04
    ffd_down.array_mu_x[0, 4, 1] = deformation_multiplier*scale_of_deformation * 0.0

    ffd_down.array_mu_y[0, 0, 0] = deformation_multiplier*scale_of_deformation * 0.0
    ffd_down.array_mu_y[0, 1, 0] = deformation_multiplier*scale_of_deformation * 0.01
    ffd_down.array_mu_y[0, 2, 0] = deformation_multiplier*scale_of_deformation * 0.015
    ffd_down.array_mu_y[0, 3, 0] = deformation_multiplier*scale_of_deformation * 0.02
    ffd_down.array_mu_y[0, 4, 0] = deformation_multiplier*scale_of_deformation * 0.025
    ffd_down.array_mu_y[0, 0, 1] = deformation_multiplier*scale_of_deformation * 0.00
    ffd_down.array_mu_y[0, 1, 1] = deformation_multiplier*scale_of_deformation * 0.01
    ffd_down.array_mu_y[0, 2, 1] = deformation_multiplier*scale_of_deformation * 0.015
    ffd_down.array_mu_y[0, 3, 1] = deformation_multiplier*scale_of_deformation * 0.02
    ffd_down.array_mu_y[0, 4, 1] = deformation_multiplier*scale_of_deformation * 0.025

    ffd_down.array_mu_x[1, 0, 0] = deformation_multiplier*scale_of_deformation * 0.0
    ffd_down.array_mu_x[1, 1, 0] = deformation_multiplier*scale_of_deformation * 0.04
    ffd_down.array_mu_x[1, 2, 0] = deformation_multiplier*scale_of_deformation * 0.06
    ffd_down.array_mu_x[1, 3, 0] = deformation_multiplier*scale_of_deformation * 0.04
    ffd_down.array_mu_x[1, 4, 0] = deformation_multiplier*scale_of_deformation * 0.0
    ffd_down.array_mu_x[1, 0, 1] = deformation_multiplier*scale_of_deformation * 0.0
    ffd_down.array_mu_x[1, 1, 1] = deformation_multiplier*scale_of_deformation * 0.04
    ffd_down.array_mu_x[1, 2, 1] = deformation_multiplier*scale_of_deformation * 0.06
    ffd_down.array_mu_x[1, 3, 1] = deformation_multiplier*scale_of_deformation * 0.04
    ffd_down.array_mu_x[1, 4, 1] = deformation_multiplier*scale_of_deformation * 0.0

    ffd_down.array_mu_y[1, 0, 0] = deformation_multiplier*scale_of_deformation * 0.0
    ffd_down.array_mu_y[1, 1, 0] = deformation_multiplier*scale_of_deformation * 0.01
    ffd_down.array_mu_y[1, 2, 0] = deformation_multiplier*scale_of_deformation * 0.015
    ffd_down.array_mu_y[1, 3, 0] = deformation_multiplier*scale_of_deformation * 0.02
    ffd_down.array_mu_y[1, 4, 0] = deformation_multiplier*scale_of_deformation * 0.025
    ffd_down.array_mu_y[1, 0, 1] = deformation_multiplier*scale_of_deformation * 0.00
    ffd_down.array_mu_y[1, 1, 1] = deformation_multiplier*scale_of_deformation * 0.01
    ffd_down.array_mu_y[1, 2, 1] = deformation_multiplier*scale_of_deformation * 0.015
    ffd_down.array_mu_y[1, 3, 1] = deformation_multiplier*scale_of_deformation * 0.02
    ffd_down.array_mu_y[1, 4, 1] = deformation_multiplier*scale_of_deformation * 0.025


    ### moving up free-form-deformation ###

    ffd_up.array_mu_x[0, 0, 0] = deformation_multiplier*scale_of_deformation * 0.0
    ffd_up.array_mu_x[0, 1, 0] = deformation_multiplier*scale_of_deformation * 0.04
    ffd_up.array_mu_x[0, 2, 0] = deformation_multiplier*scale_of_deformation * 0.06
    ffd_up.array_mu_x[0, 3, 0] = deformation_multiplier*scale_of_deformation * 0.04
    ffd_up.array_mu_x[0, 4, 0] = deformation_multiplier*scale_of_deformation * 0.0
    ffd_up.array_mu_x[0, 0, 1] = deformation_multiplier*scale_of_deformation * 0.0
    ffd_up.array_mu_x[0, 1, 1] = deformation_multiplier*scale_of_deformation * 0.04
    ffd_up.array_mu_x[0, 2, 1] = deformation_multiplier*scale_of_deformation * 0.06
    ffd_up.array_mu_x[0, 3, 1] = deformation_multiplier*scale_of_deformation * 0.04
    ffd_up.array_mu_x[0, 4, 1] = deformation_multiplier*scale_of_deformation * 0.0

    ffd_up.array_mu_y[0, 0, 0] = -deformation_multiplier*scale_of_deformation * 0.025
    ffd_up.array_mu_y[0, 1, 0] = -deformation_multiplier*scale_of_deformation * 0.020
    ffd_up.array_mu_y[0, 2, 0] = -deformation_multiplier*scale_of_deformation * 0.015
    ffd_up.array_mu_y[0, 3, 0] = -deformation_multiplier*scale_of_deformation * 0.01
    ffd_up.array_mu_y[0, 4, 0] = -deformation_multiplier*scale_of_deformation * 0.00
    ffd_up.array_mu_y[0, 0, 1] = -deformation_multiplier*scale_of_deformation * 0.025
    ffd_up.array_mu_y[0, 1, 1] = -deformation_multiplier*scale_of_deformation * 0.020
    ffd_up.array_mu_y[0, 2, 1] = -deformation_multiplier*scale_of_deformation * 0.015
    ffd_up.array_mu_y[0, 3, 1] = -deformation_multiplier*scale_of_deformation * 0.01
    ffd_up.array_mu_y[0, 4, 1] = -deformation_multiplier*scale_of_deformation * 0.00

    ffd_up.array_mu_x[1, 0, 0] = deformation_multiplier*scale_of_deformation * 0.0
    ffd_up.array_mu_x[1, 1, 0] = deformation_multiplier*scale_of_deformation * 0.04
    ffd_up.array_mu_x[1, 2, 0] = deformation_multiplier*scale_of_deformation * 0.06
    ffd_up.array_mu_x[1, 3, 0] = deformation_multiplier*scale_of_deformation * 0.04
    ffd_up.array_mu_x[1, 4, 0] = deformation_multiplier*scale_of_deformation * 0.0
    ffd_up.array_mu_x[1, 0, 1] = deformation_multiplier*scale_of_deformation * 0.0
    ffd_up.array_mu_x[1, 1, 1] = deformation_multiplier*scale_of_deformation * 0.04
    ffd_up.array_mu_x[1, 2, 1] = deformation_multiplier*scale_of_deformation * 0.06
    ffd_up.array_mu_x[1, 3, 1] = deformation_multiplier*scale_of_deformation * 0.04
    ffd_up.array_mu_x[1, 4, 1] = deformation_multiplier*scale_of_deformation * 0.0

    ffd_up.array_mu_y[1, 0, 0] = -deformation_multiplier*scale_of_deformation * 0.025
    ffd_up.array_mu_y[1, 1, 0] = -deformation_multiplier*scale_of_deformation * 0.020
    ffd_up.array_mu_y[1, 2, 0] = -deformation_multiplier*scale_of_deformation * 0.015
    ffd_up.array_mu_y[1, 3, 0] = -deformation_multiplier*scale_of_deformation * 0.01
    ffd_up.array_mu_y[1, 4, 0] = -deformation_multiplier*scale_of_deformation * 0.00
    ffd_up.array_mu_y[1, 0, 1] = -deformation_multiplier*scale_of_deformation * 0.025
    ffd_up.array_mu_y[1, 1, 1] = -deformation_multiplier*scale_of_deformation * 0.020
    ffd_up.array_mu_y[1, 2, 1] = -deformation_multiplier*scale_of_deformation * 0.015
    ffd_up.array_mu_y[1, 3, 1] = -deformation_multiplier*scale_of_deformation * 0.01
    ffd_up.array_mu_y[1, 4, 1] = -deformation_multiplier*scale_of_deformation * 0.00


    moved_up = ffd_up(up)
    moved_down = ffd_down(down)

    return moved_up, moved_down, ffd_up , ffd_down

