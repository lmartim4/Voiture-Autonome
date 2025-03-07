# real_motor_interface.py

from interfaces import MotorInterface
from constants import DC_SPEED_MIN, DC_SPEED_MAX
from core import PWM
import central_logger

class RealMotorInterface(MotorInterface):
    """
    Real implementation of MotorInterface
    that uses hardware PWM to control an ESC or a continuous servo.
    """
    def __init__(self, channel: int = 0, frequency: float = 50.0):
        """
        Args:
            channel (int): PWM channel controlling the motor (ESC).
            frequency (float): ESC PWM frequency, typically 50 Hz.
        """
        self.logger = central_logger.CentralLogger(sensor_name="RealMotor").get_logger()
        self._pwm = PWM(channel=channel, frequency=frequency)
        
        # Start the ESC at neutral
        self._pwm.start(7.5)
        self.logger.info("Motor PWM initialized and set to neutral (7.5%)")

    def __del__(self):
        self._pwm.stop()
    
    def set_speed(self, speed: float):
        """
        Sets the target speed of the vehicle in m/s by mapping it to a PWM duty cycle.
        
        Args:
            speed (float): Desired speed in m/s.
        """
        # You will want a more realistic mapping for your setup.
        # For demonstration, let's assume:
        #   speed <= 0   -> 7.5% (neutral or slight reverse)
        #   speed = 1.0 -> 8.5% 
        #   speed = 2.0 -> 9.5% 
        #   speed >= 3.0 -> 10% (max throttle)
        
        # Clamp speed to [0, 3.0], for example
        speed = max(0.0, min(speed, 3.0))

        # Map to duty cycle
        #  0.0 -> 7.5%
        #  3.0 -> 10.0%
        min_speed, max_speed = 0.0, 3.0
        min_dc,    max_dc    = DC_SPEED_MIN, DC_SPEED_MAX

        duty_cycle = (speed - min_speed) / (max_speed - min_speed) * (max_dc - min_dc) + min_dc
        
        # Send it to the PWM hardware
        self._pwm.set_duty_cycle(duty_cycle)
        self.logger.debug(f"Speed set to {speed} m/s => duty cycle: {duty_cycle}%")
