import os

import serial

from typing import List

from rplidar import RPLidar, RPLidarException


RPI5 = True

CHIP_PATH = f"/sys/class/pwm/pwmchip{2 if RPI5 else 0}"


class PWM:
    def __init__(self, channel: int, frequency: float) -> None:
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
        with open(filename, "w") as file:
            file.write(f"{message}\n")

    def start(self, dc: float) -> None:
        self.set_duty_cycle(dc)
        self.echo(1, f"{self.pwm_dir}/enable")

    def stop(self) -> None:
        self.set_duty_cycle(0)
        self.echo(0, f"{self.pwm_dir}/enable")

    def set_duty_cycle(self, dc: float) -> None:
        active = int(self.period * dc / 100.0)
        self.echo(active, f"{self.pwm_dir}/duty_cycle")


class Serial:
    def __init__(self, port: str, baudrate: int, timeout: float) -> None:
        try:
            self.serial = serial.Serial(port, baudrate, timeout=timeout)

        except serial.serialutil.SerialException:
            self.serial = None

    def is_available(self) -> bool:
        return self.serial is not None

    def read(self, depth: int) -> List[float]:
        if depth < 0:
            self.close()

        if self.serial is None:
            return [0.01, 20.0, 7.2]  # Values to not interrupt the race

        self.serial.reset_input_buffer()

        measurement = self.serial.readline().decode("utf8")
        measurement = measurement.replace("\r\n", "").split("/")

        if len(measurement) != 3:
            return self.read(depth - 1)
        try:
            return [float(value) for value in measurement]

        except ValueError:
            return self.read(depth - 1)

    def close(self) -> None:
        if self.serial is not None:
            self.serial.close()
            self.serial = None
