from voiture_algorith import VoitureAlgorithm
from constants import LIDAR_BAUDRATE

import interfaces
import time


#Real
import real_inputs.serial_singleton
from real_inputs.shared_mem_interfaces import *
from real_inputs.lidar_interface2 import RPLidarReader
from real_outputs.motor_interface import RealMotorInterface
from real_outputs.steer_interface import RealSteerInterface

USE_SIMULATION = False

def main():
    try:
        lidar_reader = RPLidarReader(port="/dev/ttyUSB0", baudrate=LIDAR_BAUDRATE)
        steer_interface = RealSteerInterface(channel=1, frequency=50.0)  
        motor_interface = RealMotorInterface(channel=0, frequency=50.0)
        init_serial(port="/dev/ttyACM0", baudrate=9600, timeout=1.0)
        speed_interface = SharedMemSpeedInterface()
        ultra_interface = SharedMemUltrasonicInterface()
        battery_interface = SharedMemBatteryInterface()
        
        algorithm = VoitureAlgorithm(
                        lidar=lidar_reader,
                        ultrasonic=ultra_interface,
                        speed=speed_interface,
                        battery=battery_interface, 
                        camera=interfaces.MockCameraInterface(),
                        steer=steer_interface,
                        motor=motor_interface,
                        console=interfaces.MockConsoleInterface())
        
        while(True):
            loop(algorithm)
            
    except KeyboardInterrupt:
        print("[Main] Interrupted by user.")
    finally:
        motor_interface.set_speed(0)
        steer_interface.set_steering_angle(0)
        lidar_reader.stop()
        shutdown_serial()

def loop(algorithm: VoitureAlgorithm):
    algorithm.run_step()
    time.sleep(0.05)


if __name__ == "__main__":
    main()