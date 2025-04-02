import serial
import threading
import time
import multiprocessing

from algorithm.constants import TICKS_TO_METER
from algorithm.interfaces import SpeedInterface, UltrasonicInterface, BatteryInterface

_last_serial_read = multiprocessing.Array('d', [0.0, 0.0, 0.0])  # [speed, ultrasonic, battery]
_last_serial_update = multiprocessing.Value('d', 0.0)

def get_speed() -> float:
    with _last_serial_read.get_lock():
        return _last_serial_read[0]

def get_ultrasonic() -> float:
    with _last_serial_read.get_lock():
        return _last_serial_read[1]

def get_battery() -> float:
    with _last_serial_read.get_lock():
        return _last_serial_read[2]

def get_last_update() -> float:
    with _last_serial_update.get_lock():
        return _last_serial_update.value

class SharedMemSpeedInterface(SpeedInterface):
    def get_speed(self) -> float:
        return (get_speed()/TICKS_TO_METER)

class SharedMemUltrasonicInterface(UltrasonicInterface):
    def get_ultrasonic_data(self) -> float:
        return get_ultrasonic()

class SharedMemBatteryInterface(BatteryInterface):
    def get_battery_voltage(self) -> float:
        return get_battery()

def start_serial_monitor(port='/dev/ttyACM0', baudrate=9600):
    """Start the serial monitor in a separate thread"""
    thread = threading.Thread(target=run_serial_monitor, args=(port, baudrate))
    thread.daemon = True
    thread.start()
    return thread

def run_serial_monitor(port, baudrate):
    """Run the serial monitor and update shared memory with parsed data"""
    try:
        ser = serial.Serial(port, baudrate, timeout=1)
        print(f"Connected to {port} at {baudrate} baud")
        
        while True:
            if ser.in_waiting > 0:
                line = ser.readline().decode('utf-8', errors='replace').strip()
                if line:
                    # Parse the data (format: "speed/ultrasonic/battery")
                    try:
                        parts = line.split('/')
                        if len(parts) == 3:
                            speed = float(parts[0])
                            ultrasonic = float(parts[1])
                            battery = float(parts[2])
                            
                            # Update shared memory
                            with _last_serial_read.get_lock():
                                _last_serial_read[0] = speed
                                _last_serial_read[1] = ultrasonic
                                _last_serial_read[2] = battery
                            
                            with _last_serial_update.get_lock():
                                _last_serial_update.value = time.time()
                            
                            # print(f"Updated: Speed={speed}, Ultrasonic={ultrasonic}, Battery={battery}")
                    except ValueError:
                        print(f"Failed to parse: {line}")
            
            time.sleep(0.01)
    
    except Exception as e:
        print(f"Serial monitor error: {e}")
    finally:
        if 'ser' in locals() and ser.is_open:
            ser.close()
            print("Serial connection closed")

# Example usage
if __name__ == "__main__":
    # Start the serial monitor
    monitor_thread = start_serial_monitor(port='/dev/ttyACM0', baudrate=9600)
    
    # Create interface instances
    speed_interface = SharedMemSpeedInterface()
    ultrasonic_interface = SharedMemUltrasonicInterface()
    battery_interface = SharedMemBatteryInterface()
    
    try:
        while True:
            print(f"Speed: {speed_interface.get_speed():.2f} m/s")
            print(f"Distance: {ultrasonic_interface.get_ultrasonic_data():.1f} cm")
            print(f"Battery: {battery_interface.get_battery_voltage():.2f} V")
            print(f"Last update: {time.time() - get_last_update():.2f} seconds ago")
            print("-" * 30)
            time.sleep(0.5)
    
    except KeyboardInterrupt:
        print("\nExiting...")