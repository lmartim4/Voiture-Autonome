import time
import numpy as np
import cv2
import os
import datetime
from interfaces import *
from constants import HITBOX_H1, HITBOX_H2, HITBOX_W
from control import compute_steer_from_lidar, check_reversed_camera, reversing_direction

def calculate_hitbox_polar(w, h1, h2):
    rad_raw_angles = np.linspace(0, 2*np.pi, num=360, endpoint=False)
    
    polar_coords = []
    polar_angles = []
    
    for theta in rad_raw_angles:
        c = np.cos(theta)
        s = np.sin(theta)
        
        candidates = []
        
        if abs(c) > 1e-14:
            x_side = w if c > 0 else -w
            t_x = x_side / c
            if t_x >= 0:
                y_at_x = s * t_x
                if -h2 <= y_at_x <= h1:
                    candidates.append(t_x)
        
        if abs(s) > 1e-14:
            y_side = h1 if s > 0 else -h2
            t_y = y_side / s
            if t_y >= 0:
                x_at_y = c * t_y
                
                if -w <= x_at_y <= w:
                    candidates.append(t_y)
        
        if len(candidates) == 0:
            d = 0.0
        else:
            t = min(candidates)
            d = t
        
        polar_coords.append(d)
        polar_angles.append(theta - np.pi/2)
    
    angle_indices = np.round(
        np.array(polar_angles) / (2 * np.pi / 360)
    ).astype(int) % 360
    
    new_d_linha = np.zeros_like(polar_coords)
    new_d_linha[angle_indices] = polar_coords
    
    return new_d_linha

hitbox = calculate_hitbox_polar(HITBOX_W, HITBOX_H1, HITBOX_H2)

def shrink_space(raw_lidar):
    free_space_shrink_mask = raw_lidar > 0
    shrink_space_lidar = np.copy(raw_lidar)
    shrink_space_lidar[free_space_shrink_mask] -= hitbox[free_space_shrink_mask]
    
    return shrink_space_lidar

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
    
    def run_step(self):
        """Runs a single step of the algorithm and measures execution time."""
        start_time = time.time()
        
        lidar_data = self.lidar.get_lidar_data()
        ultrasonic_data = self.ultrasonic.get_ultrasonic_data()
        current_speed = self.speed.get_speed()
        battery_level = self.battery.get_battery_voltage()
        
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

            reversing_direction(
            {"steer": self.steer, "speed": self.motor},  # Interface
            {"lidar": lidar_data}  # Dados do LiDAR
            )
            return

        shrinked = shrink_space(lidar_data)
        steer, steer_dc, target_angle = compute_steer_from_lidar(shrinked)

        self.steer.set_steering_angle(steer)
        self.motor.set_speed(0.7)

        end_time = time.time()  # End timing
        loop_time = end_time - start_time  # Calculate elapsed time
        loop_time *= 1000000

        self.console.print_to_console(f"Back_Dist: {ultrasonic_data} Speed: {current_speed:.2f} m/s Battery: {battery_level}V Loop Time: {loop_time:.4f} us")        
