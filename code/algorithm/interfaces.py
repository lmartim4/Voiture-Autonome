import numpy as np
import cv2
from picamera2 import Picamera2
from abc import ABC, abstractmethod
from typing import List, Tuple
from enum import Enum

class LiDarInterface(ABC):
    @abstractmethod
    def get_lidar_data(self) -> np.array:
        """Returns a NumPy array of shape(360,) where index encodes angle and value encodes distance."""
        pass

class UltrasonicInterface(ABC):
    @abstractmethod
    def get_ultrasonic_data(self) -> float:
        """Returns the distances (in cm) from ultrasonic back sensor."""
        pass

class SpeedInterface(ABC):
    @abstractmethod
    def get_speed(self) -> float:
        """Returns the current speed of the vehicle (in m/s)."""
        pass

class BatteryInterface(ABC):
    @abstractmethod
    def get_battery_voltage(self) -> float:
        """Returns the current battery voltage."""
        pass

class CameraInterface(ABC):
    @abstractmethod
    def get_camera_frame(self) -> np.ndarray:
        """Returns the current camera frame as a numpy array."""
        pass
    
    @abstractmethod
    def get_resolution(self) -> tuple[int, int]:
        """Returns the camera resolution as (width, height)."""
        pass

class SteerInterface(ABC):
    @abstractmethod
    def set_steering_angle(self, angle: float):
        """Sets the steering angle in degrees."""
        pass
    
    @abstractmethod
    def stop():
        pass

class MotorInterface(ABC):
    @abstractmethod
    def set_speed(self, speed: float):
        """Sets the target speed of the vehicle (in absolute from -3 to 3)"""
        pass
    
    def get_speed(self) -> float:
        """Returns the current target speed of the vehicle (in absolute from -3 to 3)"""
        pass
    
    @abstractmethod
    def stop():
        pass

class ConsoleInterface(ABC):
    @abstractmethod
    def print_to_console(self, message: str):
        """Prints a info message to console."""
        pass

class MockLiDarInterface(LiDarInterface):
    def get_lidar_data(self) -> np.array:
        """
        Returns a NumPy array of 360 constant values
        for quick testing. You could also randomize these
        values if you want to simulate changing distances.
        """
        return np.ones(360)

class MockUltrasonicInterface(UltrasonicInterface):
    def get_ultrasonic_data(self) -> float:
        """
        Returns a constant distance value (in cm).
        """
        return 100.0

class MockSpeedInterface(SpeedInterface):
    def get_speed(self) -> float:
        """
        Returns a constant speed value (in m/s).
        """
        return 1.5

class MockBatteryInterface(BatteryInterface):
    def get_battery_voltage(self) -> float:
        """
        Returns a constant battery voltage.
        """
        return 1.2345
    
class MockCameraInterface(CameraInterface):
    def __init__(self, width=640, height=480):
        """
        Initialize a mock camera interface for testing.
        
        Args:
            width (int): Width of the mock frame
            height (int): Height of the mock frame
        """
        self.width = width
        self.height = height
        print("[MockCameraInterface] Initialized")
    
    def get_camera_frame(self) -> np.ndarray:
        """
        Returns a mock camera frame.
        
        Returns:
            np.ndarray: A black frame with the specified dimensions
        """
        return np.zeros((self.height, self.width, 3), dtype=np.uint8)
    
    def process_stream(self):
        """
        Returns mock stream processing results.
        
        Returns:
            tuple: Mock values for (avg_red_x, avg_green_x, red_ratio, green_ratio)
        """
        # Mock values that could be returned in a real scenario
        # -1 means no detection, positive values represent positions
        avg_r = 150  # Mock red object position (left side)
        avg_g = 450  # Mock green object position (right side)
        
        # Mock detection ratios (percentage of frame covered)
        ratio_r = 0.05  # 5% of frame is red
        ratio_g = 0.08  # 8% of frame is green
        
        return avg_r, avg_g, ratio_r, ratio_g
    
    def cleanup(self):
        """Mock cleanup method"""
        print("[MockCameraInterface] Resources cleaned up")

class MockSteerInterface(SteerInterface):
    def set_steering_angle(self, angle: float):
        """
        Mock implementation that just prints the angle.
        """
        print(f"[MockSteerInterface] Steering angle set to: {angle}°")

class MockMotorInterface(MotorInterface):
    current_speed = 0
    
    def set_speed(self, speed: float):
        self.current_speed = speed
        print(f"[MockMotorInterface] Speed set to: {self.current_speed} m/s")
    
    def get_speed(self):
        return self.current_speed

class MockConsoleInterface(ConsoleInterface):
    def print_to_console(self, message: str):
        """
        Mock implementation that just prints to standard output.
        """
        print(f"[MockConsole] {message}")

if __name__ == "__main__":
    lidar_mock = MockLiDarInterface()
    ultrasonic_mock = MockUltrasonicInterface()
    speed_mock = MockSpeedInterface()
    battery_mock = MockBatteryInterface()
    camera_mock = MockCameraInterface()
    steer_mock = MockSteerInterface()
    motor_mock = MockMotorInterface()
    console_mock = MockConsoleInterface()

    console_mock.print_to_console("Testing Mock Interfaces...")
    lidar_data = lidar_mock.get_lidar_data()
    console_mock.print_to_console(f"LiDAR mock data (first 10 angles): {lidar_data[:10]}")
    console_mock.print_to_console(f"Ultrasonic mock data: {ultrasonic_mock.get_ultrasonic_data()} cm")
    console_mock.print_to_console(f"Speed mock data: {speed_mock.get_speed()} m/s")
    console_mock.print_to_console(f"Battery mock data: {battery_mock.get_battery_voltage()} V")

    # Steering and speed commands
    steer_mock.set_steering_angle(15.0)
    motor_mock.set_speed(1.0)

    # Camera
    frame = camera_mock.get_camera_frame()
    console_mock.print_to_console(f"Camera mock frame shape: {frame.shape if frame is not None else 'None'}")
