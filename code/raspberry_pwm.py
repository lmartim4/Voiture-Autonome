import os
import time
import glob
import algorithm.voiture_logger as voiture_logger

class PWM:
    def __init__(self, channel: int, frequency: float) -> None:
        """
        Initializes the PWM object with automatic chip detection.

        Args:
            channel (int): PWM channel number (0 or 1).
            frequency (float): frequency of the PWM signal in Hz.
        """
        self.logger = voiture_logger.CentralLogger(sensor_name="PWM").get_logger()
        self.channel = channel
        self.chip_path = self._find_pwm_chip()
        self.pwm_dir = f"{self.chip_path}/pwm{channel}"
        
        # Make sure the PWM channel is available
        self._ensure_pwm_channel()
        
        # Configure PWM frequency
        self.period = 1.0e9 / frequency
        self._setup_period()
        
        self.logger.info(f"PWM initialized on {self.pwm_dir} with frequency {frequency} Hz")
        
    def _find_pwm_chip(self) -> str:
        """
        Automatically detects available PWM chip.
        
        Returns:
            str: Path to the PWM chip
        """
        # Look for available PWM chips
        pwm_chips = sorted(glob.glob("/sys/class/pwm/pwmchip*"))
        
        if not pwm_chips:
            self.logger.error("No PWM chips found in /sys/class/pwm/")
            raise FileNotFoundError("No PWM chips found")
            
        # Try each chip until we find one that works
        for chip in pwm_chips:
            self.logger.debug(f"Found PWM chip: {chip}")
            return chip
            
        # Fallback to default if nothing works
        self.logger.warning("Using default pwmchip path")
        return "/sys/class/pwm/pwmchip0"
    
    def _ensure_pwm_channel(self) -> None:
        """
        Makes sure the PWM channel exists and is accessible.
        """
        if not os.path.isdir(self.pwm_dir):
            try:
                self.echo(self.channel, f"{self.chip_path}/export")
                # Wait for the directory to be created
                timeout = 5  # seconds
                start_time = time.time()
                while not os.path.isdir(self.pwm_dir):
                    if time.time() - start_time > timeout:
                        raise TimeoutError(f"Timed out waiting for {self.pwm_dir} to be created")
                    time.sleep(0.1)
            except Exception as e:
                self.logger.error(f"Failed to export PWM channel: {e}")
                raise
    
    def _setup_period(self) -> None:
        """
        Sets up the PWM period with retry logic.
        """
        max_retries = 5
        retry_count = 0
        retry_delay = 0.1  # seconds
        
        while retry_count < max_retries:
            try:
                self.echo(int(self.period), f"{self.pwm_dir}/period")
                return
            except PermissionError as e:
                retry_count += 1
                self.logger.warning(f"Permission error ({retry_count}/{max_retries}), retrying...")
                time.sleep(retry_delay)
            except Exception as e:
                self.logger.error(f"Failed to set period: {e}")
                raise
                
        self.logger.error(f"Failed to set period after {max_retries} retries")
        raise PermissionError(f"Cannot access {self.pwm_dir}/period after multiple attempts")

    def echo(self, message: int, filename: str) -> None:
        """
        Writes a message to a specified file with error handling.

        Args:
            message (int): message to write.
            filename (str): path to the file to be written
        """
        try:
            with open(filename, "w") as file:
                file.write(f"{message}\n")
                self.logger.debug(f"Wrote '{message}' to '{filename}'")
        except FileNotFoundError:
            self.logger.error(f"File not found: {filename}")
            raise
        except PermissionError:
            self.logger.error(f"Permission denied: {filename}")
            raise
        except Exception as e:
            self.logger.error(f"Error writing to {filename}: {e}")
            raise

    def start(self, dc: float) -> None:
        """
        Starts the PWM signal with the specified duty cycle.

        Args:
            dc (float): duty cycle percentage.
        """
        try:
            self.set_duty_cycle(dc)
            self.echo(1, f"{self.pwm_dir}/enable")
            self.logger.info(f"PWM started with duty cycle: {dc}%")
        except Exception as e:
            self.logger.error(f"Failed to start PWM: {e}")
            raise

    def stop(self) -> None:
        """
        Stops the PWM signal.
        """
        try:
            self.set_duty_cycle(0)
            self.echo(0, f"{self.pwm_dir}/enable")
            self.logger.info("PWM stopped")
        except Exception as e:
            self.logger.error(f"Failed to stop PWM: {e}")
            # Don't raise here to allow cleanup to continue

    def set_duty_cycle(self, dc: float) -> None:
        """
        Sets the duty cycle of the PWM signal.

        Args:
            dc (float): duty cycle percentage (typically in range [5.0, 10.0]).
        """
        # Clamp duty cycle to valid range
        dc = max(0.0, min(100.0, dc))
        active = int(self.period * dc / 100.0)
        
        try:
            self.echo(active, f"{self.pwm_dir}/duty_cycle")
            self.logger.debug(f"Duty cycle set to: {dc}% (active={active})")
        except Exception as e:
            self.logger.error(f"Failed to set duty cycle: {e}")
            raise