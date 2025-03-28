import os
import algorithm.voiture_logger as voiture_logger

RPI5 = True
CHIP_PATH = f"/sys/class/pwm/pwmchip{2 if RPI5 else 0}"

class PWM:
    def __init__(self, channel: int, frequency: float) -> None:
        """
        Initializes the PWM object.

        Args:
            channel (int): PWM channel number (0 or 1).
            frequency (float): frequency of the PWM signal in Hz.
        """
        self.logger = voiture_logger.CentralLogger(sensor_name="PWM").get_logger()
        self.pwm_dir = f"{CHIP_PATH}/pwm{channel}"

        if not os.path.isdir(self.pwm_dir):
            self.echo(channel, f"{CHIP_PATH}/export")

        self.period = 1.0e9 / frequency

        while True:
            try:
                self.echo(int(self.period), f"{self.pwm_dir}/period")
                break

            except PermissionError:
                continue

    def echo(self, message: int, filename: str) -> None:
        """
        Writes a message to a specified file.

        Args:
            message (int): message to write.
            filename (str): path to the file to be written
        """

        with open(filename, "w") as file:
            file.write(f"{message}\n")
            self.logger.debug(f"Wrote '{message}' to '{filename}'")

    def start(self, dc: float) -> None:
        """
        Starts the PWM signal with the specified duty cycle.

        Args:
            dc (float): duty cycle percentage.
        """

        self.set_duty_cycle(dc)
        self.echo(1, f"{self.pwm_dir}/enable")
        self.logger.info(f"PWM started with duty cycle: {dc}%")

    def stop(self) -> None:
        """
        Stops the PWM signal.
        """

        self.set_duty_cycle(0)
        self.echo(0, f"{self.pwm_dir}/enable")
        self.logger.info("PWM stopped")

    def set_duty_cycle(self, dc: float) -> None:
        """
        Sets the duty cycle of the PWM signal.

        Args:
            dc (float): duty cycle percentage.
            dc usually in this range: [5.0, 10.0]
        """

        active = int(self.period * dc / 100.0)
        self.echo(active, f"{self.pwm_dir}/duty_cycle")
        self.logger.debug(f"Duty cycle set to: {dc}% (active={active})")