import os
import serial
from typing import List
import central_logger

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
        self.logger = central_logger.CentralLogger(sensor_name="PWM").get_logger()
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


class Serial:
    def __init__(self, port: str, baudrate: int, timeout: float) -> None:
        """
        Initializes the Serial object.

        Args:
            port (str): serial port to be connected.
            baudrate (int): baudrate of the serial communication.
            timeout (float): timeout value in seconds.
        """
        self.logger = central_logger.CentralLogger(sensor_name="Serial").get_logger()   
        try:
            self.serial = serial.Serial(port, baudrate, timeout=timeout)
            self.logger.info(f"Serial connection established on port {port} at {baudrate} baud")

        except serial.serialutil.SerialException as e:
            self.serial = None
            self.logger.error(f"Failed to establish serial connection on port {port}: {e}")

    def is_available(self) -> bool:
        """
        Checks if the serial connection is available.

        Returns:
            bool: True if the serial connection is available, False otherwise.
        """

        return self.serial is not None

    def read(self, depth: int) -> List[float]:
        """
        Reads sensor data sent by Arduino through serial communication.

        Args:
            depth (int): maximum recursion depth for retrying on read failure.

        Returns:
            List[float]: list with the measurements of the speed sensor in
            m/s, the ultrasonic sensor in cm and the battery voltage in V.
        """

        if depth < 0:
            self.close()
            self.logger.error("Maximum recursion depth reached. Closing serial connection.")

        if self.serial is None:
            self.logger.warning("Serial connection is not available. Returning default values.")
            return [0.01, 20.0, 7.2]  # Values to not interrupt the race

        self.serial.reset_input_buffer()

        measurement = self.serial.readline().decode("utf8")
        measurement = measurement.replace("\r\n", "").split("/")

        if len(measurement) != 3:
            self.logger.warning(f"Invalid measurement format: {measurement}. Retrying...")
            return self.read(depth - 1)

        try:
            values = [float(value) for value in measurement]
            self.logger.debug(f"Read values: {values}")
            return values

        except ValueError as e:
            self.logger.error(f"ValueError: {e}. Invalid data received: {measurement}. Retrying...")
            return self.read(depth - 1)

    def close(self) -> None:
        """
        Closes the serial connection properly.
        """

        if self.serial is not None:
            self.serial.close()
            self.serial = None
            self.logger.info("Serial connection closed")
