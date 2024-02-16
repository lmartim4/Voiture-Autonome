from rpi_hardware_pwm import HardwarePWM
import time

def Motors(f):
    
    # Define the PWM command by frequency f for the DC motor
    pwm_prop = HardwarePWM(pwm_channel=0, hz=f)

    # Define the PWM command by frequency f for the servo motor
    pwm_dir = HardwarePWM(pwm_channel=1, hz=f)
        
    # Define cycle rate of the PWM command for the servomotor (straight wheels)
    cyclerate_dir = 8
        
    # Define cycle rate of the PWM command for the DC motor (minimum power)
    cyclerate_prop = 7.5
        
    # Launch the PWM command
    pwm_dir.start(cyclerate_dir)
    time.sleep(1)
    pwm_prop.start(cyclerate_prop)
    time.sleep(1)
    pwm_prop.start(0)
    
    return(pwm_prop,pwm_dir)