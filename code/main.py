import time
import numpy as np
import algorithm.interfaces as interfaces

from interface_serial import SharedMemBatteryInterface, SharedMemUltrasonicInterface, SharedMemSpeedInterface, start_serial_monitor
from interface_lidar import RPLidarReader
from interface_motor import RealMotorInterface
from interface_steer import RealSteerInterface
from interface_camera import RealCameraInterface
from interface_console import ColorConsoleInterface

from algorithm.voiture_logger import CentralLogger
from algorithm.constants import LIDAR_BAUDRATE, FIELD_OF_VIEW_DEG
from algorithm.voiture_algorithm import VoitureAlgorithm
 

logger_instance = CentralLogger(sensor_name="main")
logger = logger_instance.get_logger()

def main():
    try:
        I_Console = ColorConsoleInterface()
        I_Lidar = RPLidarReader(port="/dev/ttyUSB0", baudrate=LIDAR_BAUDRATE)        
        I_Steer = RealSteerInterface(channel=1, frequency=50.0)
        I_Motor = RealMotorInterface(channel=0, frequency=50.0)

        start_serial_monitor(port='/dev/ttyACM0', baudrate=115200)
                
        I_SpeedReading = SharedMemSpeedInterface()
        I_back_wall_distance_reading = SharedMemUltrasonicInterface()
        I_BatteryReading = SharedMemBatteryInterface()
        I_Camera = RealCameraInterface()
        
        nonzero_count = np.count_nonzero(I_Lidar.get_lidar_data())
        
        while(nonzero_count < FIELD_OF_VIEW_DEG/2):
            print("[Main] Waiting for lidar readings before start.")
            nonzero_count = np.count_nonzero(I_Lidar.get_lidar_data())
            time.sleep(0.1)
        
        I_Lidar.start_live_plot()
        
        algorithm = VoitureAlgorithm(
                        lidar=I_Lidar,
                        ultrasonic=I_back_wall_distance_reading,
                        speed=I_SpeedReading,
                        battery=I_BatteryReading, 
                        camera=I_Camera,
                        steer=I_Steer,
                        motor=I_Motor,
                        console=I_Console)

        input("Press ENTER to start the code...\n")
        print("Running...")
            
        while(True):
            loop(algorithm)
            
    except KeyboardInterrupt:
        print("[Main] Interrupted by user.")
    finally:
        I_Motor.stop()
        I_Steer.stop()
        I_Lidar.stop()


def loop(algorithm: VoitureAlgorithm):
    algorithm.run_step()
    time.sleep(0.05)


if __name__ == "__main__":
    main()