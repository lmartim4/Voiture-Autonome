# Allow to process .json files
import json

########################################

# Allows to extract information from .json file
# Inputs : .json file's name
# Outputs : list of information contained in .json file

########################################

def configuration(filename):
    
    # Opening and parsing the json file
    with open(filename, "r") as config_file:
        config_string = config_file.read()
    config = json.loads(config_string)
    
    speed_strategy = config['speed_strategy']
    
    # When we want a constant speed :
    v_cste = config['v_cste']
    
    # When we want an exponential law of command :
    
    vmin  = config['vmin']
    vmax  = config['vmax']
    
    #The angle of opening of the detection code :
    cone_detect = config['cone_detect']
    largeur_convolution = config['largeur_convolution']
   

    # Frequency needed for the PWM command
    f = config['f']
    period = 1000/f
    
    # Direction tab
    theta0 = config['theta0']
    theta10 = config['theta10']
    theta20 = config['theta20']
    theta30 = config['theta30']
    theta40 = config['theta40']
    theta50 = config['theta50']
    
    # C tab
    d0 = config['d0']
    d25 = config['d25']
    d50 = config['d50']
    d75 = config['d75']
    d100 = config['d100']
    d125 = config['d125']
    d150 = config['d150']
    d175 = config['d175']
    d200 = config['d200']
    
    interpolation_order = config['interpolation_order']
    alpha0 = config['alpha0']
    MA_strategy = config['MA_strategy']
    
    L = [speed_strategy, v_cste, vmin, vmax, cone_detect, largeur_convolution, f, theta0, theta10, theta20, theta30, theta40, theta50,d0,d25,d50,d75,d100,d125,d150,d175,d200,interpolation_order,alpha0,MA_strategy]
    
    return(L)

