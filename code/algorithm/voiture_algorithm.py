import time
import cv2
import os
import datetime
from algorithm.interfaces import *
from algorithm.constants import HITBOX_H1, HITBOX_H2, HITBOX_W
from algorithm.control_camera import extract_info, DetectionStatus
from algorithm.control_direction import compute_steer_from_lidar, shrink_space
    
class VoitureAlgorithm:
    def __init__(self, 
                 lidar: LiDarInterface, 
                 ultrasonic: UltrasonicInterface, 
                 speed: SpeedInterface, 
                 battery: BatteryInterface, 
                 camera: CameraInterface, 
                 steer: SteerInterface, 
                 motor: MotorInterface,
                 console: ConsoleInterface):
        
        # Ensure all inputs implement the expected interfaces
        if not isinstance(lidar, LiDarInterface):
            raise TypeError("lidar must implement LiDarInterface")
        if not isinstance(ultrasonic, UltrasonicInterface):
            raise TypeError("ultrasonic must implement UltrasonicInterface")
        if not isinstance(speed, SpeedInterface):
            raise TypeError("speed must implement SpeedInterface")
        if not isinstance(battery, BatteryInterface):
            raise TypeError("battery must implement BatteryInterface")
        if not isinstance(camera, CameraInterface):
            raise TypeError("camera must implement CameraInterface")
        if not isinstance(steer, SteerInterface):
            raise TypeError("steer must implement SteerInterface")
        if not isinstance(motor, MotorInterface):
            raise TypeError("motor must implement MotorInterface")
        if not isinstance(console, ConsoleInterface):
            raise TypeError("console must be an instance of ConsoleInterface")
        
        self.lidar = lidar
        self.ultrasonic = ultrasonic
        self.speed = speed
        self.battery = battery
        self.camera = camera
        self.steer = steer
        self.motor = motor
        self.console = console

        avg_r, avg_g, count_r, count_g, detection_status, processing_results = extract_info(self.camera.get_camera_frame(), *self.camera.get_resolution())
        print(detection_status)
            
    def detect_wheel_stopped_collision(self):
        """
        Monitors for wheel stoppage while motor is running, indicating a collision.
        Triggers collision response after X milliseconds of detected stoppage.
        """
        current_time = time.time()
        current_speed = self.speed.get_speed()
        motor_speed = self.motor.get_speed()
        
        # Define the threshold for stopped wheels (near zero velocity)
        STOPPED_THRESHOLD = 0.1  # m/s
        # Define time threshold for collision detection (in seconds)
        COLLISION_TIME_THRESHOLD = 0.5  # 500 milliseconds
        
        # Check if wheels are stopped but motor is running
        if current_speed < STOPPED_THRESHOLD and motor_speed > 0:
            # If this is the first detection of stoppage, record the time
            if not hasattr(self, '_wheel_stopped_start_time'):
                self._wheel_stopped_start_time = current_time
                self._collision_detected = False
            # If wheels have been stopped for longer than the threshold
            elif (current_time - self._wheel_stopped_start_time) > COLLISION_TIME_THRESHOLD and not self._collision_detected:
                self._collision_detected = True
                self.simple_marche_arrire(DetectionStatus.ONLY_GREEN)
                self.console.print_to_console(f"&c&l[COLLISION DETECTED] &e- Wheels stopped for &f{COLLISION_TIME_THRESHOLD*1000:.0f}ms &ewhile motor running")
        else:
            # Reset the timer if wheels are moving or motor is stopped
            if hasattr(self, '_wheel_stopped_start_time'):
                delattr(self, '_wheel_stopped_start_time')
                self._collision_detected = False
    
    def simple_marche_arrire(self, detection):        
        match (detection):
            case DetectionStatus.ONLY_GREEN:
                self.steer.set_steering_angle(-30)
            case DetectionStatus.ONLY_RED:
                self.steer.set_steering_angle(30)
        
        self.motor.set_speed(-1.2)
        time.sleep(1)
        self.motor.set_speed(0)
        
        
    def run_step(self):
        """Runs a single step of the algorithm and measures execution time."""
        start_time = time.time()
        raw_lidar = self.lidar.get_lidar_data()
        ultrasonic_data = self.ultrasonic.get_ultrasonic_data()
        current_speed = self.speed.get_speed()
        battery_level = self.battery.get_battery_voltage()
        
        if self.detect_wheel_stopped_collision() :
            print("Detectado")
            #self.on_blocked_by_wheel()
            
        shrinked = shrink_space(raw_lidar)
        steer, target_angle = compute_steer_from_lidar(shrinked)

        self.steer.set_steering_angle(steer)
        self.motor.set_speed(1)
        
        end_time = time.time()
        loop_time = end_time - start_time
        loop_time *= 1000000

        self.console.print_to_console(f"&b&lAngle: &f{target_angle:.1f}\t&a&lVelocity: &f{self.motor.get_speed()} &6&lSPD: &f{current_speed:.2f} m/s &e&lBAT: &f{battery_level}V &d&lLoop: &f{loop_time:.0f} us")    