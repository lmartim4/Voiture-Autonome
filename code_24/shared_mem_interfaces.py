from interfaces import SpeedInterface, UltrasonicInterface, BatteryInterface
from serial_singleton import *
from constants import TICKS_TO_METER

class SharedMemSpeedInterface(SpeedInterface):
    def get_speed(self) -> float:
        return (get_speed()/TICKS_TO_METER)


class SharedMemUltrasonicInterface(UltrasonicInterface):
    def get_ultrasonic_data(self) -> float:
        return get_ultrasonic()


class SharedMemBatteryInterface(BatteryInterface):
    def get_battery_voltage(self) -> float:
        return get_battery()
