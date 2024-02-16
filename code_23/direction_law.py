import time

from filtrage import *

def Direction_Law(cone_detect,environnement,mapt,ALPHA,THETA):
    
    dmax = 0
    for i in range(-cone_detect, cone_detect):
        if mapt[i] > dmax:
            dmax = mapt[i]
            angle_cible = i
                
    # Acquisition matter
    delta = 0
    delta = delta_angle(angle_cible,environnement)
    alpha = angle_cible + delta

    j = 0
    
    while alpha > ALPHA[j] and j < 5:
        
        j += 1
        
    alphainf = ALPHA[j-1]
    
    if j < 5:
        
        alphasup = ALPHA[j]
        theta = THETA[j-1] + (THETA[j] - THETA[j-1])*(alpha - alphainf)/(alphasup - alphainf)
        
    else:
        
        theta = THETA[j]
        
    
    # Conversion de la valeur angulaire (degrés) en duty cycle
    a = 0.06 #0.044
    b = 8.1 #8.1
    cyclerate_dir = -a*theta + b

    return cyclerate_dir, angle_cible