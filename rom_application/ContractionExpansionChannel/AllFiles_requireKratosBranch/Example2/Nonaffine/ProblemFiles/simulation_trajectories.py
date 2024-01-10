import numpy as np

def training_trajectory(time, deformation_multiplier, delta_deformation, maximum, minimum):
    #THIS IS INVERTED W.R.T. THE FIRST EXAMPLE IN THE PAPER
    #### Test trajectory####
    if time>10.0 and time<=31.0: # start modifying narrowing from 10 seconds onwards
        deformation_multiplier-= delta_deformation
        if deformation_multiplier < minimum:
            deformation_multiplier = minimum
    elif time>31.0:
        deformation_multiplier+= delta_deformation
        if deformation_multiplier > maximum:
            deformation_multiplier = maximum
    return deformation_multiplier


def testing_trajectory(time, deformation_multiplier, delta_deformation, maximum, minimum):
    #THIS IS INVERTED W.R.T. THE FIRST EXAMPLE IN THE PAPER
    ####Train trajectory####
    if time>10.0 and time<=31.0: # start modifying narrowing from 10 seconds onwards
        deformation_multiplier+=delta_deformation
        if deformation_multiplier > maximum:
            deformation_multiplier = maximum
    elif time>31.0:
        deformation_multiplier-=delta_deformation
        if deformation_multiplier < minimum:
            deformation_multiplier = minimum
    return deformation_multiplier


def second_testing_trajectory(t, T=100):
    """
    A further adjusted time-dependent function using trigonometric functions.
    This function starts at 1 when t=0, reaches 0 several times in the range t ∈ [0, 100],
    and includes more ups and downs without being noisy.
    The function takes a time parameter 't' and a period 'T'.
    """
    # Normalizing time t to the range [0, 2*pi]
    fixed_deformation_factor = 11
    normalized_t = (2 * np.pi * t) / T

    # Defining the function using a combination of sine and cosine functions
    # with a phase shift and frequency adjustments for more variations
    return (1 - (0.5 * (1 + np.sin(normalized_t - np.pi/2) * np.cos(3 * normalized_t)))) * fixed_deformation_factor
