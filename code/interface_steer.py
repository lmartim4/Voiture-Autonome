from algorithm.constants import STEER_VARIATION_RATE, STEER_CENTER
from algorithm.interfaces import SteerInterface
from raspberry_utils import PWM
import algorithm.voiture_logger as voiture_logger

class RealSteerInterface(SteerInterface):
    """
    Real implementation of SteerInterface
    that uses hardware PWM to control a servo.
    """
    def __init__(self, channel: int = 1, frequency: float = 50.0):
        """
        Args:
            channel (int): PWM channel controlling the steering servo (typically 1).
            frequency (float): Servo PWM frequency, typically 50 Hz.
        """
        self.logger = voiture_logger.CentralLogger(sensor_name="RealSteer").get_logger()
        self._pwm = PWM(channel=channel, frequency=frequency)
        
        # Start the servo at neutral (7.5% duty cycle).
        self._pwm.start(7.5)
        self.logger.info("Steering PWM initialized and set to neutral (7.5%)")

    def stop(self):
        self._pwm.stop()
    
    def set_steering_angle(self, angle: float):
        """
        Sets the steering angle in degrees.
        
        Args:
            angle (float): Steering angle in degrees. 
                           For many hobby servos:
                             - ~ -30 degrees => 5% duty cycle
                             - ~   0 degrees => 7.5% duty cycle (center)
                             - ~ +30 degrees => 10% duty cycle
        """
        
        duty_cycle = self.compute_pwm(angle)
                
        self._pwm.set_duty_cycle(duty_cycle)
        self.logger.debug(f"Steering angle set to {angle}° => duty cycle: {duty_cycle}%")

    def compute_pwm(self, steer):
        return steer * STEER_VARIATION_RATE + STEER_CENTER