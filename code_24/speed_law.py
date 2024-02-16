import time
from math import *

def Speed_Law(mapt,D,D_VAL,speed_strategy,v_cste,vmin,vmax,angle_cible,inv_alpha0):
    
    # Acquisition matter
    dfront = mapt[0]/10 # en cm
    j = 0
    
    while dfront > D_VAL[j] and j < 8:
        
        j += 1
        
    d_valinf = D_VAL[j-1]
    
    if j < 8:
        
        d_valsup = D_VAL[j]
        C = D[j-1] + (D[j] - D[j-1])*(dfront - d_valinf)/(d_valsup - d_valinf)
        
    else:
        
        C = D[j]
    
    
    if speed_strategy == 1:
        
        # Consistance
        if C >= 0 and C <= 1:
            
            v = vmin + (vmax - vmin)*exp(-abs(angle_cible)*inv_alpha0)*C
    
    elif speed_strategy == 2:
        
        v = v_cste
        
    cyclerate_prop = v
    return cyclerate_prop, dfront*10