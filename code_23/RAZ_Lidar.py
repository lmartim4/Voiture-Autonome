from RPLidarRoboticia import rplidar
import time

def RAZ_Lidar(lidar):
    
    lidar.disconnect()
    time.sleep(1)
    lidar.connect()
    try :
        print(lidar.get_info())
    except :
        print("la communication ne s'est pas établie correctement")
    lidar.start_motor()
    time.sleep(1)
    lidar.stop_motor()
    lidar.stop()
    time.sleep(1)
    lidar.disconnect()
    time.sleep(1)
