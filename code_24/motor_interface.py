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
        self._pwm.start(DC_SPEED_MIN)
        self.logger.info("Motor PWM initialized and set to neutral (7.5%)")

    def stop(self):
        self._pwm.stop()
    
    def set_speed(self, speed: float):
        """
        Sets the target speed of the vehicle in m/s by mapping it to a PWM duty cycle.
        
        Args:
            speed (float): Desired speed in m/s.
        """
        
        speed = max(0.0, min(speed, 3.0))
        min_speed, max_speed = 0.0, 3.0
        min_dc,    max_dc    = DC_SPEED_MIN, DC_SPEED_MAX

        duty_cycle = (speed - min_speed) / (max_speed - min_speed) * (max_dc - min_dc) + min_dc
        
        self._pwm.set_duty_cycle(8.0)
        self.logger.debug(f"Speed set to {speed} m/s => duty cycle: {duty_cycle}%")
