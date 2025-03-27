import time
import numpy as np
import cv2
import os
import datetime
from algorithm.interfaces import *
from algorithm.constants import HITBOX_H1, HITBOX_H2, HITBOX_W
from algorithm.control_camera import check_reversed_camera, reversing_direction
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
                self.on_detect_colision_wheel_stopped()
                self.console.print_to_console(f"COLLISION DETECTED - Wheels stopped for {COLLISION_TIME_THRESHOLD*1000:.0f}ms while motor running")
        else:
            # Reset the timer if wheels are moving or motor is stopped
            if hasattr(self, '_wheel_stopped_start_time'):
                delattr(self, '_wheel_stopped_start_time')
                self._collision_detected = False
    
    def on_detect_colision_wheel_stopped(self):
        fator_de_giro = 30 # graus
        cor_da_foto = -1 # 1 = FOTO VERDE, -1 = FOTO VERMELHA
        
        self.steer.set_steering_angle(cor_da_foto*fator_de_giro)
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
            self.on_blocked_by_wheel()
            
        
        
        if check_reversed_camera(self.camera):
            self.console.print_to_console("Inversion d'orientation détectée !")
            # Captura o frame atual
            frame = self.camera.get_camera_frame()

            if frame is not None:
                # Criar pasta se não existir
                save_dir = "imagens_reverso"
                if not os.path.exists(save_dir):
                    os.makedirs(save_dir)

                # Salvar imagem com timestamp
                timestamp = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                filename = os.path.join(save_dir, f"reversed_{timestamp}.jpg")

                # Converte para BGR antes de salvar (OpenCV usa BGR)
                frame_bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                cv2.imwrite(filename, frame_bgr)
                print(f"Imagem salva: {filename}")
            
            reversing_direction(self.steer, self.motor, self.ultrasonic, raw_lidar)
            return

        shrinked = shrink_space(raw_lidar)
        steer, target_angle = compute_steer_from_lidar(shrinked)

        self.steer.set_steering_angle(steer)
        self.motor.set_speed(1)
        
        end_time = time.time()
        loop_time = end_time - start_time
        loop_time *= 1000000

        self.console.print_to_console(f"Angle: {target_angle} Velocity: {self.motor.get_speed()} SPD: {current_speed:.2f} m/s BAT: {battery_level}V Loop: {loop_time:.0f} us")               
            