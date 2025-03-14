from voiture_algorithm import VoitureAlgorithm
from constants import LIDAR_BAUDRATE, FIELD_OF_VIEW_DEG
from central_logger import CentralLogger
import interfaces
import time
import numpy as np
from shared_mem_interfaces import *
from lidar_interface import RPLidarReader
from motor_interface import RealMotorInterface
from steer_interface import RealSteerInterface

logger_instance = CentralLogger(sensor_name="main")
logger = logger_instance.get_logger()

USE_SIMULATION = False

def main():
    try:
        lidar_reader = RPLidarReader(port="/dev/ttyUSB0", baudrate=LIDAR_BAUDRATE)
        lidar_reader.get_lidar_data()
        
        
        nonzero_count = np.count_nonzero(lidar_reader.get_lidar_data())
        while(nonzero_count < FIELD_OF_VIEW_DEG/2):
            nonzero_count = np.count_nonzero(lidar_reader.get_lidar_data())
            time.sleep(0.1)
        
        #lidar_reader.start_live_plot()
        
        steer_interface = RealSteerInterface(channel=1, frequency=50.0)  
        motor_interface = RealMotorInterface(channel=0, frequency=50.0)
        init_serial(port="/dev/ttyACM0", baudrate=9600, timeout=1.0)
        speed_interface = SharedMemSpeedInterface()
        ultra_interface = SharedMemUltrasonicInterface()
        battery_interface = SharedMemBatteryInterface()
        camera_interface = interfaces.RealCamera()
        
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
        motor_interface.stop()
        steer_interface.stop()
                
        shutdown_serial()
        lidar_reader.stop()

def loop(algorithm: VoitureAlgorithm):
    algorithm.run_step()
    time.sleep(0.05)


if __name__ == "__main__":
    main()