from control import compute_pwm
from interfaces import SteerInterface
from core import PWM
import central_logger

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
        self.logger = central_logger.CentralLogger(sensor_name="RealSteer").get_logger()
        self._pwm = PWM(channel=channel, frequency=frequency)
        
        # Start the servo at neutral (7.5% duty cycle).
        # Adjust if your servo's "neutral" duty cycle is different.
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
        
        duty_cycle = compute_pwm(angle)
                
        # Send it to the PWM hardware
        self._pwm.set_duty_cycle(duty_cycle)
        self.logger.debug(f"Steering angle set to {angle}° => duty cycle: {duty_cycle}%")
