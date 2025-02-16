import traceback
import time
import numpy as np
import threading

from pynput import keyboard
from console import Console
from core import RPLidar, Serial, PWM, RPLidarException
from control import compute_speed, stop_command, filter, transform_back, compute_steer, compute_speed, check_reverse, get_nonzero_points_in_hitbox
from constants import *

console = Console()

lidarGlobal = None
running = False
interface = None

# Global variable to store the last serial data read.
last_serial_data = None

# We'll create these as globals so we can reinitialize them on restart.
stop_serial_task = None
serial_thread = None

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
        scan = np.asarray(scan)[:, 1:]
        
        # Get indices from the first column (angles)
        indices = np.round(scan[:, 0]).astype(int)
        indices = np.clip(indices, 0, 359)
        
        # Exclude angles from 0 to 90 and from 270 to 360 (here using 0-180 as in your code)
        valid_indices = (indices > 0) & (indices < 180)
        scan = scan[valid_indices]
        indices = indices[valid_indices]
        
        # Update distances (convert mm to meters)
        self.distances[indices] = scan[:, 1] / 1000.0
        
        # (The loop below doesn’t really fill any gap; you might want to improve this if needed)
        for index in range(1, 360):
            if self.distances[index] == 0.0:
                self.distances[index] = 0.0
        
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
        except RPLidarException:
            self.lidar.clean_input()
            pass

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
                # Return steering to neutral
                self.interface["steer"].set_duty_cycle((DC_STEER_MAX + DC_STEER_MIN)/2)
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
        reverse(self.interface)
        
    def left(self):
        self.console.info("Turning left!")
        self.interface["steer"].set_duty_cycle(DC_STEER_MIN)

    def right(self):
        self.console.info("Turning right!")
        self.interface["steer"].set_duty_cycle(DC_STEER_MAX)
        
last_reverse = 0.0

def reverse(interface):
    global last_reverse, last_serial_data

    if time.time() - last_reverse < 1:
        return

    last_reverse = time.time()
    distanca_do_sensor = None
    
    # Minor adjustments before reversing
    interface["speed"].set_duty_cycle(7.0)
    time.sleep(0.03)
    interface["speed"].set_duty_cycle(7.5)
    time.sleep(0.03)

    # Try reading serial data
    for _ in range(10):
        if last_serial_data is not None:
            # Assuming sensor distance is at position 1.
            distanca_do_sensor = last_serial_data[1]
            interface["speed"].set_duty_cycle(PWM_REVERSE)
            if distanca_do_sensor < distancia_maxima_re and (distanca_do_sensor not in (20.0, 0.0)):                
                break
        time.sleep(0.1)

    interface["speed"].set_duty_cycle(7.5)

def serial_reader_task(interface):
    """
    Continuously reads from the serial port and updates the global last_serial_data variable.
    """
    global last_serial_data, stop_serial_task
    while not stop_serial_task.is_set():
        data = interface["serial"].read(depth=5)
        if data:
            last_serial_data = data
        time.sleep(0.05)
    
    console.info("Serial reader task exiting...")
    interface["serial"].close()

def init():
    global interface, lidarGlobal, stop_serial_task, serial_thread

    console.info(f"Initializing Voiture '{NOM_VOITURE}'")
    
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

    # Prime the serial communication
    interface["serial"].read(depth=5)
    if interface["serial"].is_available():
        console.info("Serial comm is stable and working")
    else:
        console.info("Serial comm is not responding, closing it")
    
    console.info("Press ENTER to start measurements and logs")

    # Start a fresh keyboard listener if needed
    try:
        keyboard.Listener(on_press=lambda key: None).start()
    except RuntimeError:
        pass
    
    # IMPORTANT: Reinitialize the stop event and serial thread on each init.
    stop_serial_task = threading.Event()
    serial_thread = threading.Thread(target=serial_reader_task, args=(interface,), daemon=True)
    serial_thread.start()

def close():
    global interface, lidarGlobal, stop_serial_task, serial_thread

    console.info("Closing the interface elements")

    steer_dc, speed_dc = stop_command()
    interface["steer"].set_duty_cycle(steer_dc)
    interface["speed"].set_duty_cycle(speed_dc)

    interface["steer"].stop()
    interface["speed"].stop()

    # Signal the serial reader thread to stop and wait for it.
    if stop_serial_task is not None:
        stop_serial_task.set()
    if serial_thread is not None:
        serial_thread.join()

    lidarGlobal.shutdown()
        

RUN_VOITURE = True 

def run_main(bypass: bool = False):
    global interface, running, last_serial_data
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
            
            if RUN_VOITURE:
                data = {"lidar": distances, "serial": last_serial_data}
                steer, steer_dc = compute_steer(data)
                speed, speed_dc = compute_speed(data, steer)

                hitsx, hitsy = get_nonzero_points_in_hitbox(distances)
                
                console.info(f"hitbox: {np.count_nonzero(hitsx)} {last_serial_data} {steer:.2f} deg {100 * speed:.0f}%")
                
                if check_reverse(distances):
                    console.info("Reverse")
                    reverse(interface)
                else:
                    interface["steer"].set_duty_cycle(steer_dc)
                    interface["speed"].set_duty_cycle(speed_dc)

            console.log([*last_serial_data, steer, speed, distances.tolist()])
            distances = np.zeros_like(distances)

    except (KeyboardInterrupt, Exception) as error:
        if not isinstance(error, KeyboardInterrupt, RPLidarException):
            traceback.print_exc()

        if isinstance(error, RPLidarException):
            run_main(True)


def main():
    while True:
        try:
            run_main(running)
            break
        except RPLidarException:
            lidarGlobal.lidar.clean_input()
            console.info("Lidar exception occurred. Restarting the main loop...")
            #time.sleep(1)
        except KeyboardInterrupt:
            console.info("KeyboardInterrupt received. Exiting.")
            console.close()
            break

if __name__ == "__main__":
    main()
