import time
import cv2
import os
import datetime
from algorithm.interfaces import *
from algorithm.constants import HITBOX_H1, HITBOX_H2, HITBOX_W
from algorithm.control_camera import extract_info, DetectionStatus
from algorithm.control_direction import compute_steer_from_lidar, shrink_space
from algorithm.control_speed import compute_speed

back_dist = 30.0

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

        avg_r, avg_g, ratio_r, ratio_g, detection_status, processing_results = extract_info(self.camera.get_camera_frame(), *self.camera.get_resolution())
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
        STOPPED_THRESHOLD = 0.02  # m/s
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
                self.console.print_to_console(f"&c&l[COLLISION DETECTED] &e- Wheels stopped for &f{COLLISION_TIME_THRESHOLD*1000:.0f}ms &ewhile motor running")
                self.simple_marche_arrire()
        else:
            # Reset the timer if wheels are moving or motor is stopped
            if hasattr(self, '_wheel_stopped_start_time'):
                delattr(self, '_wheel_stopped_start_time')
                self._collision_detected = False
    
    def simple_marche_arrire(self):        
        avg_r, avg_g, ratio_r, ratio_g, detection_status, processing_results = extract_info(self.camera.get_camera_frame(), *self.camera.get_resolution())

        match (detection_status):
            case DetectionStatus.ONLY_GREEN:
                if  ratio_g > 0.10:
                    self.steer.set_steering_angle(25)
                    self.motor.set_speed(-1.5)
                    #time.sleep(1.5)
                    
                    for _ in range(15):
                        ultrasonic_read = self.ultrasonic.get_ultrasonic_data()  
                        if (ultrasonic_read <= back_dist and ultrasonic_read != -1.0): 
                            break
                        time.sleep(0.1)

                    self.motor.set_speed(0)
                    self.steer.set_steering_angle(-25)
                    self.motor.set_speed(0.7)
                    time.sleep(0.1)
                    print("GIRANDO")
                else:
                    self.voltando()
            case DetectionStatus.ONLY_RED:
                if  ratio_r > 0.10:
                    self.steer.set_steering_angle(-25)
                    self.motor.set_speed(-1.5)
                    #time.sleep(1.5)

                    for _ in range(15):
                        ultrasonic_read = self.ultrasonic.get_ultrasonic_data()  
                        if (ultrasonic_read <= back_dist and ultrasonic_read != -1.0): 
                            break
                        time.sleep(0.1)

                    self.motor.set_speed(0)
                    self.steer.set_steering_angle(25)
                    self.motor.set_speed(0.7)
                    time.sleep(0.1)
                    print("GIRANDO")
                else:
                    self.voltando()
            case _:
                self.voltando()

    def voltando(self):
        self.steer.set_steering_angle(0)
        self.motor.set_speed(-1.2)
        #time.sleep(1.5)

        for _ in range(15):
            ultrasonic_read = self.ultrasonic.get_ultrasonic_data()  
            if (ultrasonic_read <= back_dist and ultrasonic_read != -1.0): 
                print(f"Sai pelo break!!! {ultrasonic_read}")
                break
            time.sleep(0.1)

        self.motor.set_speed(0)
        self.motor.set_speed(0.7)
        print("VOLTANDO")
    
    def reversing_direction(self):
        l_side = self.lidar.get_lidar_data()[60:120]   # Região à esquerda do carrinho
        r_side = self.lidar.get_lidar_data()[240:300]  # Região à direita do carrinho
                    
        avg_left = np.mean(l_side[l_side > 0])
        avg_right = np.mean(r_side[r_side > 0]) 

        if avg_left > avg_right:
            print("Espace libre à gauche, rotation vers la gauche...")
            self.steer.set_steering_angle(+25)
            self.motor.set_speed(-2.0)
            print("Rodou esquerda...")
            
            for _ in range(20):
                ultrasonic_read = self.ultrasonic.get_ultrasonic_data()  
                if (ultrasonic_read <= back_dist and ultrasonic_read != -1.0): 
                    break
                time.sleep(0.1)

            self.motor.set_speed(0)
            self.steer.set_steering_angle(-25)
            self.motor.set_speed(0.7)
            time.sleep(1.0)
            return
        else:
            print("Espace libre à droite, rotation vers la droite...")
            self.steer.set_steering_angle(-25)
            self.motor.set_speed(-2.0)
            print("Rodou direita...")

            for _ in range(20):
                ultrasonic_read = self.ultrasonic.get_ultrasonic_data()  
                if (ultrasonic_read <= back_dist and ultrasonic_read != -1.0):
                    break
                time.sleep(0.1)

            self.motor.set_speed(0)
            self.steer.set_steering_angle(+25)
            self.motor.set_speed(0.7)
            time.sleep(1.0)
            return
        
    def print_detection(self,detection, ratio_r, ratio_g):
        match (detection):
            case DetectionStatus.ONLY_RED:
                self.console.print_to_console(f"&4&lo &4&lo &4&lo &4&lo &4&lo &4&lo {ratio_r}, {ratio_g}")    
            case DetectionStatus.ONLY_GREEN:
                self.console.print_to_console(f"&2&lo &2&lo &2&lo &2&lo &2&lo &2&lo {ratio_r}, {ratio_g}")    
            case DetectionStatus.RED_LEFT_GREEN_RIGHT:
                self.console.print_to_console(f"&4&lo &4&lo &4&lo &2&lo &2&lo &2&lo {ratio_r}, {ratio_g}")    
            case DetectionStatus.GREEN_LEFT_RED_RIGHT:
                self.console.print_to_console(f"&2&lo &2&lo &2&lo &4&lo &4&lo &4&lo {ratio_r}, {ratio_g}")    
        return

    def demi_tour(self): 
        frame = self.camera.get_camera_frame()
        
        avg_r, avg_g, ratio_r, ratio_g, detection_status, processing_results = extract_info(frame, *self.camera.get_resolution()) 
        
        self.print_detection(detection_status, ratio_r, ratio_g)
        
        match (detection_status):
            case DetectionStatus.RED_LEFT_GREEN_RIGHT:
                return False
            case DetectionStatus.GREEN_LEFT_RED_RIGHT:
                return True

        return False

    
    def check_too_close_to_mur(self):
        lidar_data = self.lidar.get_lidar_data()
        
        # Assuming lidar_data is a 360-degree array where indices 350-359 and 0-10 
        # represent the front of the vehicle (approximately 20 degrees field of view)
        front_indices = list(range(350, 360)) + list(range(0, 11))
        front_data = [lidar_data[i] for i in front_indices if lidar_data[i] > 0]  # Filter out zero/invalid readings
        
        # Calculate average distance in front if we have valid readings
        if len(front_data) > 0:
            dist_front_moyene = sum(front_data) / len(front_data)
        else:
            dist_front_moyene = float('inf')  # No valid readings means no obstacles detected
        
        # Print the front distance
        self.console.print_to_console(f"&e&lDistance frontale: &f{dist_front_moyene:.2f} cm")
        
        # Define minimum safe distance threshold (in same units as lidar data)
        min_front_lidar = 0.30  # 40 cm, adjust as needed
        
        # Check if we're too close to a wall and trigger reverse maneuver
        if dist_front_moyene < min_front_lidar:
            self.console.print_to_console(f"&c&l[WARNING] &eTrop proche du mur: &f{dist_front_moyene:.2f} cm")
            self.voltando()
        
    
    def run_step(self):
        """Runs a single step of the algorithm and measures execution time."""
        start_time = time.time()
        raw_lidar = self.lidar.get_lidar_data()
        ultrasonic_data = self.ultrasonic.get_ultrasonic_data()
        current_speed = self.speed.get_speed()
        battery_level = self.battery.get_battery_voltage()
        
        self.detect_wheel_stopped_collision()
        
        if self.demi_tour():
           print("Reversed direction! reversing..")
           self.reversing_direction()

        shrinked = shrink_space(raw_lidar)
        steer, target_angle = compute_steer_from_lidar(shrinked)
        target_speed = compute_speed(shrinked, target_angle)
        
        self.check_too_close_to_mur()
        
        self.steer.set_steering_angle(steer)
        self.motor.set_speed(target_speed)
        
        end_time = time.time()
        loop_time = end_time - start_time
        loop_time *= 1000000

        self.console.print_to_console(f"&b&lAngle: &f{target_angle:.1f}\t&a&lVelocity: &f{self.motor.get_speed()} &6&lSPD: &f{current_speed:.2f} m/s Dist: {self.ultrasonic.get_ultrasonic_data()} &e&lBAT: &f{battery_level}V &d&lLoop: &f{loop_time:.0f} us")    