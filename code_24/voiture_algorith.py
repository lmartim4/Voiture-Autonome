from interfaces import LiDarInterface, UltrasonicInterface, SpeedInterface, BatteryInterface, CameraInterface, SteerInterface, MotorInterface, ConsoleInterface

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
        """Runs a single step of the algorithm."""
        # Example logic
        lidar_data = self.lidar.get_lidar_data()
        ultrasonic_data = self.ultrasonic.get_ultrasonic_data()
        current_speed = self.speed.get_speed()
        battery_level = self.battery.get_battery_voltage()
        camera_frame = self.camera.get_camera_frame()

        self.console.print_to_console(f"Lidar: {lidar_data}")
        self.console.print_to_console(f"Ultrasonic: {ultrasonic_data}")
        self.console.print_to_console(f"Speed: {current_speed} km/h")
        self.console.print_to_console(f"Battery: {battery_level}%")
        self.console.print_to_console("Processing...")

        # Dummy decisions
        if lidar_data and min(d[1] for d in lidar_data) < 1.0:
            self.console.print_to_console("Obstacle detected! Turning left.")
            self.steer.set_steering_angle(-30)
        else:
            self.steer.set_steering_angle(0)
        
        self.motor.set_speed(max(0, current_speed - 0.1))  # Slight slowdown
        self.console.print_to_console("Step completed.")