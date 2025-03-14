import numpy as np
import cv2
from picamera2 import Picamera2
from abc import ABC, abstractmethod
from typing import List, Tuple

# -------------------------------------------------------------------------------
# Input Interfaces (same as before)
# -------------------------------------------------------------------------------
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
        """Returns the latest camera frame as a NumPy array."""
        pass

# -------------------------------------------------------------------------------
# Camera Interface
# -------------------------------------------------------------------------------
class RealCamera(CameraInterface):
    def __init__(self, width=640, height=480):
        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration(
            main={"size": (width, height)},
            lores={"size": (width, height)}
        )
        self.picam2.configure(config)

        try:
            self.picam2.start()
            print("Initialisation réussie de la caméra")
        except Exception as e:
            print(f"Erreur d'initialisation de la caméra: {e}")
            raise

        self.width = width
        self.height = height

    def get_camera_frame(self) -> np.ndarray:
        frame = self.picam2.capture_array()
        if frame is None:
            print("Le cadre de la caméra n'a pas pu être capturé")
            return None
        return frame

    def process_stream(self):
        frame = self.get_camera_frame()
        if frame is None:
            return None, None, 0, 0

        frame_hsv = cv2.cvtColor(frame, cv2.COLOR_RGB2HSV)

        # Faixas de cor para detecção
        red_lower, red_upper = np.array([0, 150, 150]), np.array([10, 255, 255])
        green_lower, green_upper = np.array([50, 100, 100]), np.array([70, 255, 255])

        mask_r = cv2.inRange(frame_hsv, red_lower, red_upper)
        mask_g = cv2.inRange(frame_hsv, green_lower, green_upper)

        stack_r = np.column_stack(np.where(mask_r > 0))
        avg_r = np.mean(stack_r[:, 1]) if stack_r.size > 0 else -1

        stack_g = np.column_stack(np.where(mask_g > 0))
        avg_g = np.mean(stack_g[:, 1]) if stack_g.size > 0 else -1

        count_r = np.count_nonzero(mask_r) / (self.width * self.height)
        count_g = np.count_nonzero(mask_g) / (self.width * self.height)

        return avg_r, avg_g, count_r, count_g

# -------------------------------------------------------------------------------
# Output Interfaces (same as before)
# -------------------------------------------------------------------------------
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
        """Sets the target speed of the vehicle (in m/s)"""
        pass
    
    @abstractmethod
    def stop():
        pass

# -------------------------------------------------------------------------------
# Console Interface
# -------------------------------------------------------------------------------
class ConsoleInterface(ABC):
    @abstractmethod
    def print_to_console(self, message: str):
        """Prints a info message to console."""
        pass

# -------------------------------------------------------------------------------
# Mock Implementations
# -------------------------------------------------------------------------------
class MockLiDarInterface(LiDarInterface):
    def get_lidar_data(self) -> np.array:
        """
        Returns a NumPy array of 360 constant values
        for quick testing. You could also randomize these
        values if you want to simulate changing distances.
        """
        return np.ones(360)  # All angles have distance=1.0 (meter/centimeter/whatever your unit is)

class MockUltrasonicInterface(UltrasonicInterface):
    def get_ultrasonic_data(self) -> float:
        """
        Returns a constant distance value (in cm).
        """
        return 100.0  # e.g., 100 cm

class MockSpeedInterface(SpeedInterface):
    def get_speed(self) -> float:
        """
        Returns a constant speed value (in m/s).
        """
        return 1.5  # e.g., 1.5 m/s

class MockBatteryInterface(BatteryInterface):
    def get_battery_voltage(self) -> float:
        """
        Returns a constant battery voltage.
        """
        return 12.3  # e.g., 12.3 V

class MockCameraInterface(CameraInterface):
    def get_camera_frame(self):
        """
        Returns a mock camera frame.
        Could be None or a placeholder array.
        """
        # Return None or a dummy NumPy array to simulate a frame.
        return np.zeros((480, 640, 3), dtype=np.uint8)

class MockSteerInterface(SteerInterface):
    def set_steering_angle(self, angle: float):
        """
        Mock implementation that just prints the angle.
        """
        print(f"[MockSteerInterface] Steering angle set to: {angle}°")

class MockMotorInterface(MotorInterface):
    def set_speed(self, speed: float):
        """
        Mock implementation that just prints the speed.
        """
        print(f"[MockMotorInterface] Speed set to: {speed} m/s")

class MockConsoleInterface(ConsoleInterface):
    def print_to_console(self, message: str):
        """
        Mock implementation that just prints to standard output.
        """
        print(f"[MockConsole] {message}")

# -------------------------------------------------------------------------------
# Example usage
# -------------------------------------------------------------------------------
if __name__ == "__main__":
    # Create mock instances
    lidar_mock = MockLiDarInterface()
    ultrasonic_mock = MockUltrasonicInterface()
    speed_mock = MockSpeedInterface()
    battery_mock = MockBatteryInterface()
    camera_mock = MockCameraInterface()
    steer_mock = MockSteerInterface()
    motor_mock = MockMotorInterface()
    console_mock = MockConsoleInterface()

    # Use them as if they were real
    console_mock.print_to_console("Testing Mock Interfaces...")
    lidar_data = lidar_mock.get_lidar_data()
    console_mock.print_to_console(f"LiDAR mock data (first 10 angles): {lidar_data[:10]}")
    console_mock.print_to_console(f"Ultrasonic mock data: {ultrasonic_mock.get_ultrasonic_data()} cm")
    console_mock.print_to_console(f"Speed mock data: {speed_mock.get_speed()} m/s")
    console_mock.print_to_console(f"Battery mock data: {battery_mock.get_battery_voltage()} V")

    # Steering and speed commands
    steer_mock.set_steering_angle(15.0)
    motor_mock.set_speed(2.0)

    # Camera
    frame = camera_mock.get_camera_frame()
    console_mock.print_to_console(f"Camera mock frame shape: {frame.shape if frame is not None else 'None'}")
