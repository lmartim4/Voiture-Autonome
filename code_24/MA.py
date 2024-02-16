from rpi_hardware_pwm import HardwarePWM
import time
##################################################
#Intialisation des moteurs
##################################################
stop_prop = 7.5
point_mort_prop = 0.5
vitesse_max_m_s = 8

angle_pwm_min = 6.3 #gauche
angle_pwm_max = 9 #droite
angle_degre_max = +30 #vers la gauche
angle_pwm_centre= 7.65
angle_degre=0

pwm_prop = HardwarePWM(pwm_channel=0, hz=50) #PWM pour la propulsion // pwm_channel coorespond au numéro du canal de module PWM intégré à la Raspberry Pi
pwm_dir = HardwarePWM(pwm_channel=1, hz=50) #PWM pour la direction
pwm_prop.start(0)
print("PWM désactivées")

##################################################
#Fonction de direction et de propulsion
##################################################

def set_direction_degre(angle_degre) :
    print(angle_degre)
    angle_pwm = angle_pwm_centre - (angle_pwm_max - angle_pwm_min) * angle_degre /(2 * angle_degre_max )
    if angle_pwm > angle_pwm_max : 
        angle_pwm = angle_pwm_max
    if angle_pwm < angle_pwm_min :
        angle_pwm = angle_pwm_min
    print(angle_pwm)
    pwm_dir.change_duty_cycle(angle_pwm)
    
def set_vitesse_m_s(vitesse_m_s):
    if vitesse_m_s > vitesse_max_m_s :
        vitesse_m_s = vitesse_max_m_s
    elif vitesse_m_s < -vitesse_max_m_s :
        vitesse_m_s = -vitesse_max_m_s
    if vitesse_m_s == 0 :
        pwm_prop.change_duty_cycle(stop_prop)
    elif vitesse_m_s > 0 :
        vitesse = vitesse_m_s * 1.5/8
        pwm_prop.change_duty_cycle(stop_prop + point_mort_prop + vitesse )
    elif vitesse_m_s < 0 :
        vitesse = vitesse_m_s * 1.5/8
        pwm_prop.change_duty_cycle(stop_prop - point_mort_prop + vitesse )

def recule():
    set_vitesse_m_s(-vitesse_max_m_s)
    time.sleep(0.1)
    # Si la MA ne fonctionne pas remplacer point_mort_prop par 0 ou l'inverse
    set_vitesse_m_s(0)
    time.sleep(0.1)
    # Diminuer la valeur ci-dessous pour augmenter la vitesse de marche arrière
    set_vitesse_m_s(-8)
    time.sleep(0.1)