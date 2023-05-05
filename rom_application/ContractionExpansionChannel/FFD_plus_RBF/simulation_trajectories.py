

def training_trajectory(time, deformation_multiplier, delta_deformation, maximum, minimum):
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


def testing_trajectory(time, deformation_multiplier, delta_deformation, maximum, minimum):
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