import traceback
import time
import numpy as np
import threading

from pynput import keyboard
from console import Console
from core import RPLidar, Serial, PWM, RPLidarException
from control import compute_speed, stop_command
from constants import *

console = Console()

lidarGlobal = None

running = False
interface = None

# Global variable to store the last serial data read.
last_serial_data = None

# Event to signal the serial reader thread to stop.
stop_serial_task = threading.Event()

distancia_maxima_re = 30

class LidarInterface:
    def __init__(self, port="/dev/ttyUSB", baudrate=LIDAR_BAUDRATE):
        self.lidar = RPLidar(port, baudrate=baudrate)
        self.distances = np.zeros(360, dtype=float)

    def initialize(self):
        health = self.lidar.get_health()[0]
        console.info(f"Lidar's health is {health.lower()}")
        self.lidar.connect()
        self.lidar.start_motor()
        self.lidar.start()

    def process_scan(self, scan):
        """Process a single lidar scan and update distances."""
        # Convert scan to a NumPy array and ignore the first column (angle)
        scan = np.asarray(scan)[:, 1:]
        
        # Get indices from the first column (angles)
        indices = np.round(scan[:, 0]).astype(int)
        indices = np.clip(indices, 0, 359)
        
        # Update distances (convert mm to meters)
        self.distances[indices] = scan[:, 1] / 1000.0
        
        # Fill in gaps: if a distance is zero, use the previous valid reading
        for index in range(1, 360):
            if self.distances[index] == 0.0:
                self.distances[index] = self.distances[index - 1]

        return self.distances.copy()

    def iter_processed_scans(self):
        """Generator that yields processed scan data."""
        for scan in self.lidar.iter_scans():
            yield self.process_scan(scan)

    def shutdown(self):
        try:
            self.lidar.stop()
            self.lidar.stop_motor()
            self.lidar.disconnect()
        except Exception as e:
            console.error(f"Error shutting down Lidar: {e}")

class KeyboardController:
    def __init__(self, console, interface):
        self.console = console
        self.interface = interface
        self.listener = keyboard.Listener(
            on_press=self.on_press,
            on_release=self.on_release
        )
    
    def start(self):
        self.listener.start()

    def on_press(self, key):
        global running
        
        try:
            if key.char == 'w':
                self.forward()
            elif key.char == 's':
                self.backward()
            elif key.char == 'a':
                self.left()
            elif key.char == 'd':
                self.right()

        except AttributeError:
            if key == keyboard.Key.enter and not running:
                running = True
                self.console.info("Running...")
                self.console.info("Press CTRL+C to stop the code")

    def on_release(self, key):
        try:
            if key.char in ['a', 'd']:
                self.interface["steer"].set_duty_cycle((DC_STEER_MAX + DC_STEER_MIN)/2)  # Volta para frente ao soltar a ou d
        except AttributeError:
            pass

        try:
            if key.char == 'w':
                self.interface["speed"].set_duty_cycle(7.5)
        except AttributeError:
            pass

        if key == keyboard.Key.esc:
            return False

    def forward(self):
        self.console.info("Going forward!")
        self.interface["speed"].set_duty_cycle(DC_SPEED_MAX)
    
    def backward(self):
        reverse(interface)
        
    def left(self):
        self.console.info("Turning left!")
        self.interface["steer"].set_duty_cycle(DC_STEER_MIN)

    def right(self):
        self.console.info("Turning right!")
        self.interface["steer"].set_duty_cycle(DC_STEER_MAX)
        
def on_press(key: keyboard.Key):
    global running

    if key == keyboard.Key.enter and not running:
        running = True
        console.info("Running...")
        console.info("Press CTRL+C to stop the code")

listener = keyboard.Listener(on_press=on_press)

last_reverse = 0.0

def reverse(interface):
    global last_reverse

    if time.time() - last_reverse < 1:
        return

    last_reverse = time.time()
    distanca_do_sensor = None
    
    #interface["lidar"].stop()

    # Nao tocar: perform minor adjustments before reversing
    interface["speed"].set_duty_cycle(7.0)
    time.sleep(0.03)
    interface["speed"].set_duty_cycle(7.5)
    time.sleep(0.03)
    # fim do nao tocar

    # Try reading serial data from the global variable updated by the reader thread.
    for _ in range(10):
        if last_serial_data is not None:
            # Assuming that the sensor distance is in position 1.
            distanca_do_sensor = last_serial_data[1]
            #print(f"Dist = {distanca_do_sensor}")
            interface["speed"].set_duty_cycle(PWM_REVERSE)
            if distanca_do_sensor < distancia_maxima_re and (not distanca_do_sensor == 20.0 and not distanca_do_sensor == 0.0):                
                break
        time.sleep(0.1)

    interface["speed"].set_duty_cycle(7.5)
    #for _ in range(10):
    #    if distanca_do_sensor > distancia_maxima_re:
    #        print(f"Dando ré porque: dist = {distanca_do_sensor}")
    #        interface["speed"].set_duty_cycle(PWM_REVERSE)
    #        time.sleep(0.1)
    #    else:
    #        print(f"Nao vou dar ré dist = {distanca_do_sensor}")
    #
    #interface["speed"].set_duty_cycle(7.5)
    
    ## Signal the serial reader thread to stop and wait for it to finish.
    #stop_serial_reader.set()
    #reader_thread.join()
    ##interface["lidar"].start()

def serial_reader_task(interface):
    """
    Continuously reads from the serial port and updates the global last_serial_data variable.
    """
    global last_serial_data
    while not stop_serial_task.is_set():
        data = interface["serial"].read(depth=5)
        if data:
            last_serial_data = data
            #print(last_serial_data)
        # Adjust the sleep interval based on your application's needs.
        time.sleep(0.05)
    
    print("OUT OF LOOP")
    print("OUT OF LOOP")
    print("OUT OF LOOP")
    print("OUT OF LOOP")
    print("OUT OF LOOP")
    print("OUT OF LOOP")
    print("OUT OF LOOP")

def init(): 
    console.info(f"Initializing Voiture '{NOM_VOITURE}'")
    
    global interface, lidarGlobal

    lidarGlobal = LidarInterface()

    interface = {
        "steer": PWM(channel=1, frequency=50.0),
        "speed": PWM(channel=0, frequency=50.0),
        "serial": Serial("/dev/ttyACM", 115200, timeout=0.1)
    }

    lidarGlobal.initialize()

    interface["steer"].start(7.5)
    interface["speed"].start(7.5)

    time.sleep(0.5)

    steer_dc, speed_dc = stop_command()

    interface["steer"].set_duty_cycle(steer_dc)
    interface["speed"].set_duty_cycle(speed_dc)

    interface["serial"].read(depth=5)

    if interface["serial"].is_available():
        console.info("Serial comm is stable and working")
    else:
        console.info("Serial comm is not responding, so closing it")

    console.info("Press ENTER to start the code")

    try:
        listener.start()
    except RuntimeError:
        pass
    
    # Start the serial reader thread.
    serial_thread = threading.Thread(target=serial_reader_task, args=(interface,), daemon=True)
    serial_thread.start()

def close():
    global interface

    console.info("Closing the interface elements")

    steer_dc, speed_dc = stop_command()

    interface["steer"].set_duty_cycle(steer_dc)
    interface["speed"].set_duty_cycle(speed_dc)

    interface["steer"].stop()
    interface["speed"].stop()
    interface["serial"].close()
    
    lidarGlobal.shutdown()
    
    # Signal the serial reader thread to stop.
    stop_serial_task.set()

    console.close()

def main(bypass: bool = False):
    global interface, running

    if bypass:
        running = True

    init()

    controller = KeyboardController(console, interface)
    controller.start()

    try:
        for distances in lidarGlobal.iter_processed_scans():
            if not running:
                continue

            if np.count_nonzero(distances) < 60:
                continue

            data = {"lidar": distances, "serial": last_serial_data}
            console.log([*last_serial_data, -1, -1, distances.tolist()])
            
            distances = 0.0 * distances

    except (KeyboardInterrupt, Exception) as error:
        if not isinstance(error, KeyboardInterrupt):
            traceback.print_exc()
        
        if isinstance(error, RPLidarException):
            main(bypass=True)
    finally:
        close()

if __name__ == "__main__":
    main()