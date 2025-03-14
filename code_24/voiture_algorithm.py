import time
import numpy as np
from interfaces import LiDarInterface, UltrasonicInterface, SpeedInterface, BatteryInterface, CameraInterface, SteerInterface, MotorInterface, ConsoleInterface
from constants import HITBOX_H1, HITBOX_H2, HITBOX_W
from control import compute_steer_from_lidar, check_reversed_camera, reversing_direction

def calculate_hitbox_polar(w, h1, h2):
    """
    Return an array of radial distances for angles -pi..pi (360 steps),
    giving the intersection of a ray at angle theta with the rectangle
    [-w, w] x [-h2, h1].
    """
    print("CALCULATING HITBOX")
    
    # Angles from -pi to pi in 360 increments
    rad_raw_angles = np.linspace(0, 2*np.pi, num=360, endpoint=False)
    
    polar_coords = []
    polar_angles = []
    
    for theta in rad_raw_angles:
        c = np.cos(theta)
        s = np.sin(theta)
        
        # We use t >= 0 in the parametric form:
        #   X(t) = t*cos(theta)
        #   Y(t) = t*sin(theta)
        #
        # We'll collect all valid positive 't' that hits the rectangle
        # boundary, then take the smallest positive.
        candidates = []
        
        # 1) Intersection with the vertical sides x = +/- w (if cos(theta) != 0)
        if abs(c) > 1e-14:
            # Decide which vertical side we actually hit (depending on sign of cos)
            # If cos > 0, we expect x=+w. If cos < 0, x=-w.
            x_side = w if c > 0 else -w
            t_x = x_side / c  # solve t for x_side = t*cos(theta)
            if t_x >= 0:
                y_at_x = s * t_x
                # Check if that y lies within the rectangle's vertical span
                if -h2 <= y_at_x <= h1:
                    candidates.append(t_x)
        
        # 2) Intersection with the horizontal sides y = +h1 or y = -h2 (if sin(theta) != 0)
        if abs(s) > 1e-14:
            # If sin>0, we expect y=+h1. If sin<0, y=-h2.
            y_side = h1 if s > 0 else -h2
            t_y = y_side / s  # solve t for y_side = t*sin(theta)
            if t_y >= 0:
                x_at_y = c * t_y
                # Check if that x lies within the rectangle's horizontal span
                if -w <= x_at_y <= w:
                    candidates.append(t_y)
        
        # If for some reason no valid intersection was found, set distance=0
        # (or you might choose np.nan if you prefer).
        if len(candidates) == 0:
            d = 0.0
        else:
            # We want the FIRST intersection => smallest positive t
            t = min(candidates)
            d = t  # Because distance = sqrt((t*c)^2 + (t*s)^2) = t
        
        polar_coords.append(d)
        polar_angles.append(theta - np.pi/2)
    
    # Map each angle to an integer bin in [0..359]
    angle_indices = np.round(
        np.array(polar_angles) / (2 * np.pi / 360)
    ).astype(int) % 360
    
    # Create final 1D array, indexed by angle
    new_d_linha = np.zeros_like(polar_coords)
    new_d_linha[angle_indices] = polar_coords
    
    return new_d_linha

hitbox = calculate_hitbox_polar(HITBOX_W, HITBOX_H1, HITBOX_H2)

def shrink_space(raw_lidar):
    free_space_shrink_mask = raw_lidar > 0
    shrink_space_lidar = np.copy(raw_lidar)
    shrink_space_lidar[free_space_shrink_mask] -= hitbox[free_space_shrink_mask]
    
    return shrink_space_lidar

# Main Algorithm Blackbox
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
        
        start_time = time.time()  # Start timing
        
        lidar_data = self.lidar.get_lidar_data()
        ultrasonic_data = self.ultrasonic.get_ultrasonic_data()
        current_speed = self.speed.get_speed()
        battery_level = self.battery.get_battery_voltage()

        self.console.print_to_console(f"Lidar: {lidar_data[:10]}")
        self.console.print_to_console(f"Ultrasonic: {ultrasonic_data}")
        self.console.print_to_console(f"Speed: {current_speed:.2f} m/s")
        self.console.print_to_console(f"Battery: {battery_level}V")   
        
        #camera_frame = self.camera.get_camera_frame()

        if check_reversed_camera(self.camera):
            self.console.print_to_console("Inversion d'orientation détectée !")
            reversing_direction(
            {"steer": self.steer, "speed": self.motor},  # Interface
            {"lidar": lidar_data}  # Dados do LiDAR
            )
            return

        
        shrinked = shrink_space(lidar_data)
        steer, steer_dc, target_angle = compute_steer_from_lidar(shrinked)

        self.steer.set_steering_angle(steer)
        self.motor.set_speed(2)

        end_time = time.time()  # End timing
        loop_time = end_time - start_time  # Calculate elapsed time
        loop_time *= 1000000

        self.console.print_to_console(f"Ultrasonic: {ultrasonic_data} Speed: {current_speed:.2f} m/s Battery: {battery_level}V Loop Time: {loop_time:.4f} us")        
