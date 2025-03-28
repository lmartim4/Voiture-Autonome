from algorithm.interfaces import MotorInterface
from algorithm.constants import ESC_DC_MIN, ESC_DC_MAX
from raspberry_pwm import PWM
import algorithm.voiture_logger as voiture_logger
import time

NEUTRAL_DC = (ESC_DC_MIN + ESC_DC_MAX)/2
MIN_DC = ESC_DC_MIN # Full reverse
MAX_DC = ESC_DC_MAX # Full forward


class RealMotorInterface(MotorInterface):
    def __init__(self, channel: int = 0, frequency: float = 50.0):
        self.logger = voiture_logger.CentralLogger(sensor_name="RealMotor").get_logger()
        self._pwm = PWM(channel=channel, frequency=frequency)
        self._pwm.start(NEUTRAL_DC) # Start at neutral position (7.5% for Maverick msc-30BR-WP)
        self._in_reverse_mode = False
        self.logger.info("Motor PWM initialized and set to neutral (7.5%)")
        self.speed = 0
    
    def stop(self):
        """Stops the ESC and PWM"""
        self._pwm.set_duty_cycle(NEUTRAL_DC)  # Return to neutral for Maverick ESC
        self._in_reverse_mode = False
        self._pwm.stop()
        self.speed = 0
        self.logger.info("Motor stopped")
    
    def _enter_reverse_mode(self):
        """
        Special sequence to enter reverse mode on the Maverick msc-30BR-WP ESC
        Most brushed ESCs need a quick brake-neutral-reverse sequence
        """
        
        self._pwm.set_duty_cycle(7.0)  # Brake position
        time.sleep(0.03)
        
        self._pwm.set_duty_cycle(NEUTRAL_DC)  # Neutral position for Maverick ESC
        time.sleep(0.03)
        
        # Now ESC should be ready to accept reverse commands
        self._in_reverse_mode = True
        self.logger.debug("Entered reverse mode with Maverick ESC sequence")
    
    def _exit_reverse_mode(self):
        """Exit reverse mode and go back to neutral for Maverick ESC"""
        self._pwm.set_duty_cycle(7.5)  # Neutral duty cycle for Maverick ESC
        time.sleep(0.1)  # Give ESC time to recognize the neutral position
        self._in_reverse_mode = False
        self.logger.debug("Exited reverse mode")

    def set_speed(self, s: float):
        """
        Sets the motor speed from -3.0 (full reverse) to 3.0 (full forward)
        0.0 is neutral position
        
        For Maverick msc-30BR-WP Brushed ESC:
        - Full reverse (-3.0) = 5% duty cycle
        - Neutral (0.0) = 7.5% duty cycle
        - Full forward (3.0) = 10% duty cycle
        """

        MAX_SPEED = 3 # 3.0
        self.speed = max(-MAX_SPEED, min(s, MAX_SPEED))
        
        if self.speed < 0 and not self._in_reverse_mode:
            self._enter_reverse_mode()
        elif self.speed >= 0 and self._in_reverse_mode:
            self._exit_reverse_mode()
        
        if abs(self.speed) < 0.1:
            duty_cycle = NEUTRAL_DC
        elif self.speed >= 0:
            duty_cycle = NEUTRAL_DC + (self.speed / 3.0) * (MAX_DC - NEUTRAL_DC)
        else:
            duty_cycle = MIN_DC + ((self.speed + 3.0) / 3.0) * (NEUTRAL_DC - MIN_DC)
        
        self._pwm.set_duty_cycle(duty_cycle)
        self.logger.debug(f"Speed set to {self.speed} m/s => duty cycle: {duty_cycle}%")

    def get_speed(self) -> float:
        return self.speed

    def set_duty_cycle(self, duty_cycle: float):
        """Direct control of PWM duty cycle for debugging or manual control"""
        self._pwm.set_duty_cycle(duty_cycle)
        self.logger.debug(f"Duty cycle directly set to {duty_cycle}%")

if __name__ == "__main__":
    test_sequence = [
        (0.0, 1.0),     # Start at neutral for 1 second
        (0.5, 2.0),     # Low forward speed for 2 seconds
        (1.5, 2.0),     # Medium forward speed for 2 seconds
        (3.0, 1.5),     # Full forward for 1.5 seconds
        (0.0, 2.0),     # Back to neutral for 2 seconds
        (-0.5, 2.0),    # Low reverse speed for 2 seconds
        (-1.5, 2.0),    # Medium reverse speed for 2 seconds
        (-3.0, 1.5),    # Full reverse for 1.5 seconds
        (0.0, 2.0),     # Back to neutral for 2 seconds
        (2.0, 1.5),     # Higher forward speed for 1.5 seconds
        (-2.0, 1.5),    # Higher reverse speed for 1.5 seconds
        (1.0, 3.0),     # Low forward for 3 seconds
        (0.0, 1.0),     # End at neutral for 1 second
    ]
    
    motor = RealMotorInterface()
    
    try:
        print("Starting motor test sequence...")
        print("-" * 40)
        
        for i, (speed, duration) in enumerate(test_sequence):
            direction = "NEUTRAL" if abs(speed) < 0.1 else "FORWARD" if speed > 0 else "REVERSE"
            print(f"Step {i+1}/{len(test_sequence)}: {direction} speed at {abs(speed):.1f} for {duration:.1f}s")
            
            motor.set_speed(speed)
            
            time.sleep(duration)
            
        print("-" * 40)
        print("Test sequence completed successfully!")
        
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"\nError during test: {e}")
    finally:
        motor.stop()
        print("Motor stopped and PWM cleaned up")