import time

import numpy as np

import RPi.GPIO as GPIO

from rpi_hardware_pwm import HardwarePWM


GPIO.setwarnings(False)
GPIO.setmode(GPIO.BOARD)


STEERING_CHANNEL = 33
STEERING_FREQUENCY = 50.0

STEERING_LOWER = -18.0
STEERING_UPPER =  18.0

STEERING_CONV_A = -0.0775
STEERING_CONV_B =  8.0000

#STEERING_CONV_A = -0.0556
#STEERING_CONV_B =  7.8000


class PWM:
    def __init__(self, pin: int, frequency: float) -> None:
        GPIO.setup(pin, GPIO.OUT)
        #self.pwm = GPIO.PWM(pin, STEERING_FREQUENCY)
        self.pwm = HardwarePWM(pwm_channel=1, hz=frequency)

        self.pwm.start(STEERING_CONV_B)

    def define_bounds(self, lower: float, upper: float) -> None:
        self.lower = lower
        self.upper = upper

    def define_conversion(self, a: float, b: float) -> None:
        self.a = a
        self.b = b

    def set_value(self, value: float) -> None:
        value = np.clip(value, self.lower, self.upper)

        #self.pwm.ChangeDutyCycle(self.a * value + self.b)
        self.pwm.change_duty_cycle(self.a * value + self.b)


def init_steering() -> PWM:
    steering = PWM(STEERING_CHANNEL, STEERING_FREQUENCY)

    steering.define_bounds(STEERING_LOWER, STEERING_UPPER)
    steering.define_conversion(STEERING_CONV_A, STEERING_CONV_B)

    steering.set_value(0.0)

    return steering


if __name__ == "__main__":
    steering = init_steering()

    while True:
        try:
            for value in range(-18, 19, 1):
                print(value)
                steering.set_value(value)
                time.sleep(0.2)

        except KeyboardInterrupt:
            break
    
    #steering.pwm.stop()
