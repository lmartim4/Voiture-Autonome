from algorithm.constants import STEER_VARIATION_RATE, STEER_CENTER
from algorithm.interfaces import SteerInterface
from raspberry_pwm import PWM
import algorithm.voiture_logger as voiture_logger
import time
import signal

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
    
def handle_sigint(sig, frame):
    print("\nTest interrupted by user")
    if 'steering' in globals():
        steering.stop()
    print("Steering servo stopped and PWM cleaned up")
    sys.exit(0)


if __name__ == "__main__":
    # Register signal handler for clean shutdown on Ctrl+C
    signal.signal(signal.SIGINT, handle_sigint)
    
    # Test sequence: (angle_in_degrees, duration_in_seconds)
    test_sequence = [
        (0.0, 1.0),      # Start at center for 1 second
        (10.0, 2.0),     # Small right turn for 2 seconds
        (20.0, 1.5),     # Medium right turn for 1.5 seconds
        (30.0, 1.0),     # Full right turn for 1 second
        (0.0, 2.0),      # Back to center for 2 seconds
        (-10.0, 2.0),    # Small left turn for 2 seconds
        (-20.0, 1.5),    # Medium left turn for 1.5 seconds
        (-30.0, 1.0),    # Full left turn for 1 second
        (0.0, 2.0),      # Back to center for 2 seconds
        (25.0, 1.0),     # Right turn for 1 second
        (-25.0, 1.0),    # Left turn for 1 second
        (15.0, 1.0),     # Slight right for 1 second
        (-15.0, 1.0),    # Slight left for 1 second
        (0.0, 1.0),      # End at center for 1 second
    ]
    
    steering = RealSteerInterface()
    
    try:
        print("Starting steering test sequence...")
        print("-" * 50)
        
        for i, (angle, duration) in enumerate(test_sequence):
            direction = "CENTER" if abs(angle) < 0.1 else "RIGHT" if angle > 0 else "LEFT"
            print(f"Step {i+1}/{len(test_sequence)}: Turn {direction} at {abs(angle):.1f}° for {duration:.1f}s")
            
            # Set the steering angle
            steering.set_steering_angle(angle)
            
            # Display the calculated PWM duty cycle
            duty_cycle = steering.compute_pwm(angle)
            print(f"  PWM duty cycle: {duty_cycle:.2f}%")
            
            # Wait for the specified duration
            time.sleep(duration)
            
        print("-" * 50)
        print("Steering test sequence completed successfully!")
        
    except Exception as e:
        print(f"\nError during test: {e}")
    finally:
        # Clean up PWM resources
        steering.stop()
        print("Steering servo stopped and PWM cleaned up")