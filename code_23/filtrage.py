def filtrage(map, largeur_convolution):
    n=len(map)
    mapt=[0 for i in range(n)]
    for i in range(n):
        for k in range(-largeur_convolution,largeur_convolution):
            mapt[i]+=map[(i+k)%n]
        mapt[i]=mapt[i]/(2*largeur_convolution+1)
    return mapt

def delta_angle(angle_consigne, donnees_lidar):
    
    angle_inf = -5
    angle_sup = 5
    
    for k in range(angle_inf,0):
        if donnees_lidar[angle_consigne + k] < 500:
            angle_inf = k
    
    for k in range(1,angle_sup):
        if donnees_lidar[angle_consigne + k] < 500:
            angle_sup = k
            
    delta_angle = angle_sup + angle_inf
    return delta_angle