import numpy as np
import sympy
from sympy import *

def get_mean_velocity_logarithm_law():
    y  = symbols('y')
    y_0_mean = 0.02 # corresponds to "open country terrain," M. Andre's dissertation, p30 laso needs to be considered as uncertain ?
    sy_0 = 0.002 # a standard deviation of 10 % is considered
    y_0 = np.random.normal(y_0_mean, sy_0)

    kappa = 0.4 # Von Karman constant
    u0_bar = 10 # wind speed of 10 m/s
    su = 1.0 # a standard deviation of 10 % of the wind speed is considered
    u_bar = np.random.normal(u0_bar,su)
    # logarithmic profile featured in M. Andre's dissertation, p6.
    epsilon = 1e-6
    mean_velocity = (u_bar/kappa) * np.log(y/y_0 + epsilon)
    # mean_velocity = (u_bar/kappa) * np.log(y/y_0)

    return str(mean_velocity)

def get_mean_velocity_power_law(u_bar,alpha):
    y  = symbols('y')
    yref = 10.0 # M. Andre's dissertation, p30
    uref = 10 # wind speed of 10 m/s
    su = 1.0 #  a standard deviation of 10 % of the wind speed is considered
    # u_bar = np.random.normal(uref,su)

    alpha0 = 0.12 # corresponds to open terrain from annexure to Euro Code DIN EN 1991-1-4 NA
    salpha = 0.012 # a standard deviation of 10 % is considered
    # alpha = np.random.normal(alpha0,salpha)

    # power law profile featured in M. Andre's dissertation, p6.
    mean_velocity = uref * np.power(y/yref,alpha)

    return str(mean_velocity)
