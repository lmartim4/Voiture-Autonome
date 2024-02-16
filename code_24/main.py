
#########################################

# Allow to control & monitor input devices (mouse & keyboard)
from pynput.keyboard import Key, Listener

# Allow to process .json files
import json

# Hardware PWM
from rpi_hardware_pwm import HardwarePWM

# Allow to control Lidar
from RPLidarRoboticia import rplidar

import time
from datetime import datetime
import numpy as np
from math import *

# Allow to manage files
import os

# Importations of our fonctions
from configuration import *
from data_acquisition import *
from RAZ_Lidar import *
from Motors import *
from filtrage import *
from interpolations import *
from planning import *
from MA import *

###########################
## MANAGE PROGRAM LAUNCH ##
###########################

# Press 'Key.right' (->) to start 
go = 0
setup = 0

def on_press(key):
    try:
        global go
        global setup
        
        if key == Key.right:
            # Launch the program
            go = 1
            print('{0} enfoncée'.format(key))
            print("Lancement du programme\n")
            print("Appuyez sur 'CNTRL+C' pour arrêter le programme\n")
            return False
        
        elif key == Key.left:
            # Launch the initialization
            setup = 1
            print('{0} enfoncée'.format(key))
            print("Lancement de l'initialisation\n")
            return False
        
    except AttributeError:
        pass
    
def on_release(key):
    
    if key == Key.esc:
        # Stop listener
        print('{0} relâchée'.format(key))
        return False

# Collect events until released
    # Launching initialization
listener1 = Listener(on_press=on_press,on_release=on_release)
    # Launchning program
listener2 = Listener(on_press=on_press,on_release=on_release) 

listener1.start()

#########
## END ##
#########

while setup != 1:
    
    print("Appuyez sur 'Key.left' (<-) pour lancer l'initialisation")
    time.sleep(5)

try:
    
    if setup == 1:
        
        ###################
        ## CONFIGURATION ##
        ###################
        
        filename = "config.json"
        CONFIG = configuration(filename)
        speed_strategy = CONFIG[0]
        v_cste = CONFIG[1]
        vmin = CONFIG[2]
        vmax = CONFIG[3]
        cone_detect = CONFIG[4]
        largeur_convolution = CONFIG[5]
        f = CONFIG[6]
        
        THETA = CONFIG[7:13]
        ALPHA = np.linspace(0,50,6)
        D = CONFIG[13:22]
        D_VAL = np.linspace(0,200,9)
        
        interpolation_order = CONFIG[22]
        alpha0 = CONFIG[23]
        inv_alpha0 = 1./alpha0
        MA_strategy = CONFIG[24]
        
        #########
        ## END ##
        #########     
        
        ########################
        ## VARIABLES GLOBALES ##
        ######### ##############
        
        angle_cible=0
        angle_consigne=0
        dmax=0
        
        #########
        ## END ##
        #########
        
        ######################
        ## DATA ACQUISITION ##
        ######################
        
        print("Initialisation de l'acquisition de données")

        now = datetime.now().strftime("%Y_%m_%d_%H:%M:%S")
        folder = f"/home/pi/Desktop/PIE/log/v23_{now}"

        os.mkdir(folder)

        filename1 = f"{folder}/output.txt"
        filename2 = f"{folder}/output_raw_map.txt"
        filename3 = f"{folder}/output_filtered_map.txt"

        Pfiles = data_acquisition(filename1, filename2, filename3)
        
        print("Fin de l'initialisation de l'acquisition de données\n")

        #########
        ## END ##
        #########
        
        ##########################
        ## LIDAR INITIALIZATION ##
        ##########################
        
        print("Initialisation du Lidar")
        
        LIDAR_DEVICE = "/dev/ttyUSB0"
        
        # Connect to Lidar unit
        lidar = rplidar.RPLidar(LIDAR_DEVICE,baudrate=115200)
        
        # RAZ
        RAZ_Lidar(lidar)
        
        # Connect to the serial port with the name self.port : if it was connected to another serial port, disconnect form it first
        lidar.connect()
        # Start sensor motor
        lidar.start_motor()
        time.sleep(1)
        
        # Creation of 360 zeros tabs
        environnement = [0]*360 
            
        print("Fin de l'initialisation du Lidar\n")

        #########
        ## END ##
        #########
            
        ########################### 
        ## MOTORS INITIALIZATION ##
        ###########################
        
        print("Initialisation de la propulsion et de la direction")
        
        pwm_prop,pwm_dir = Motors(f)
        
        print("Fin de l'initialisation de la propulsion et de la direction\n")
        
        #########
        ## END ##
        #########
        
        print("Fin de l'initialisation\n")
        
        ###############
        ## MAIN LOOP ##
        ###############
        
        listener2.start()
        
        print("Appuyez sur la touche 'Key.right' (->) pour lancer le programme\n")
        
        # The tab is filling continuously so the loop if infinite
        for scan in lidar.iter_scans() : 
            
            for i in range(len(scan)) :
                #[1] : angle et [2] : distance (pour scan)
                environnement[max(0,min(359,int(360-scan[i][1])))]=scan[i][2]
            
            if interpolation_order == 0:
                
                environnement = interpolation(environnement)
            
            elif interpolation_order == 1:
                
                environnement = interpolation_lin(environnement)
            
            # Put a convolution filter on the map
            mapt = filtrage(environnement, largeur_convolution)
            
            if go == 1:
                
                ######################
                ## LOI DE DIRECTION ##
                ######################
                
                collision, cyclerate_dir, steering = Direction_Law(environnement)
                pwm_dir.change_duty_cycle(cyclerate_dir)
                
                #########
                ## END ##
                #########
                
                ####################
                ## LOI DE VITESSE ##
                ####################
                
                cyclerate_prop = Speed_Law(steering)
                pwm_prop.change_duty_cycle(cyclerate_prop)
                
                #########
                ## END ##
                #########
                
                ###############################
                ## DATA ACQUISITION, WRITING ##
                ###############################
                
                t = time.time()
                
                GENERAL_LIST = [t, 0, cyclerate_prop, 0, cyclerate_dir]
            
                data_writing(Pfiles, GENERAL_LIST, environnement, mapt)
                
                #########
                ## END ##
                #########
                
                ####################
                ## MARCHE ARRIERE ##
                ####################
                
                angle_min = 0
                dmin = mapt[0]
                for i in range(-30, 30):
                    if mapt[i] < dmin:
                        dmin = mapt[i]
                        angle_min = i
                        
                if dmin < 150:
                    
                    lidar.stop()
                    # Reversed wheels orientation
                    if MA_strategy == 0:
                        
                       pwm_dir.change_duty_cycle(a*theta + b)
                       
                    # Straight wheels
                    elif MA_strategy == 1:
                        
                        pwm_dir.change_duty_cycle(8.1)
                        
                    recule()
                    lidar.start()
                
                #########
                ## END ##
                #########
                    
                dmin = mapt[0]
                angle_min = 0
                environnement = [0]*360
                mapt = []
                
                #########
                ## END ##
                #########
        
        #########
        ## END ##
        #########
                
            
# Recover of CTRL+C
except KeyboardInterrupt: 
    # Stop the program
    go = 0
    setup = 0
    print("Arrêt propulsion et direction")
    pwm_dir.change_duty_cycle(8)
    pwm_prop.change_duty_cycle(0)
    time.sleep(2)
    pwm_prop.stop()
    pwm_dir.stop()
    print("Fermeture fichiers")
    close_files(Pfiles)
    print("Arrêt Lidar")
    lidar.stop_motor()
    lidar.reset()
    lidar.disconnect()
    print("Arrêt du programme")