from voiture_algorith import VoitureAlgorithm
import interfaces

#Real
from lidar_interface2 import RPLidarReader

USE_SIMULATION = False

if USE_SIMULATION:
    print("Need to implement simulation")
    #lidar = SimulatedLiDar(num_points=20)
else:
    lidar = RPLidarReader()

algo = VoitureAlgorithm(lidar=interfaces.MockLiDarInterface(),
                        ultrasonic=interfaces.MockUltrasonicInterface(),
                        speed=interfaces.MockSpeedInterface(),
                        battery=interfaces.MockBatteryInterface(), 
                        camera=interfaces.MockCameraInterface(),
                        steer=interfaces.MockSteerInterface(),
                        motor=interfaces.MockMotorInterface(),
                        console=interfaces.MockConsoleInterface())

algo.run_step()
