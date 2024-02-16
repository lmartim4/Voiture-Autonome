import matplotlib.pyplot as plt
import numpy as np
import time

# Interpolation de degré 0
def interpolation(L):
    
    n = len(L)
    ref = 0
    k = 0
    
    while L[k] == 0:
        
        k += 1
        
    ref = L[k]
    
    for i in range(0,k):
        
        L[i] = ref
        
    for i in range(k+1,n):
        
        if L[i] == 0:
            
            k = i
            
            while L[k] == 0:
                
                k -= 1
                
            L[i] = L[k]       
            
    return(L)       

# Interpolation de degré 1
def interpolation_lin(L):
    
    n = len(L)
    val_sup = 0
    ind_sup = 0
    val_inf = 0
    ind_inf = 0
    k = 0
    warning_sup = False
    warning_inf = False
    a = 0
    b = 0
    
    for i in range(0,n):
        
        if L[i] == 0:
            
            isup = i
            iinf = i
            
            while isup < n and L[isup] == 0:
                
                isup += 1
                
            if isup != n:
                
                val_sup = L[isup]
                ind_sup = isup
                
            else:
                
                warning_sup = True
                
            
            while iinf > -1 and L[iinf] == 0:
                
                iinf -= 1
                
            if iinf != -1:
                
                val_inf = L[iinf]
                ind_inf = iinf
                
            else:
                
                warning_inf = True
            
            # Si on veut définir une autre valeur de référence
            if warning_sup and warning_inf:
                
                L[i] = 0
                
            else:
                
                a = (val_sup - val_inf)/(ind_sup - ind_inf)
                b = (val_inf*ind_sup - val_sup*ind_inf)/(ind_sup - ind_inf)
                
                L[i] = a * i + b
                
        val_sup = 0
        ind_sup = 0
        val_inf = 0
        ind_inf = 0    
        warning_sup = False
        warning_inf = False
        a = 0
        b = 0
        
            
    return(L)
                     
#L = [0, 0, 1409.0, 0, 1344.25, 0, 1289.5, 0, 0, 1237.5, 0, 1190.0, 0, 1149.75, 0, 0, 1115.0, 0, 1083.5, 0, 1055.0, 0, 0, 1028.25, 0, 1007.25, 0, 987.25, 0, 0, 969.75, 0, 954.25, 0, 942.5, 0, 0, 934.5, 0, 924.5, 0, 0, 918.0, 0, 912.25, 0, 907.25, 0, 0, 905.5, 0, 903.5, 0, 904.75, 0, 0, 907.0, 0, 910.75, 0, 916.5, 0, 0, 924.25, 0, 934.0, 0, 0, 943.25, 0, 953.75, 0, 969.75, 0, 0, 985.25, 0, 1006.25, 0, 1024.75, 0, 0, 1049.25, 0, 1076.25, 0, 0, 1109.75, 0, 1145.0, 0, 0, 1185.75, 0, 1227.2]               
#L = interpolation_lin(L)
#print(L)
                