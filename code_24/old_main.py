import traceback
import time
import numpy as np
import multiprocessing as mp
from rplidar import RPLidarException
from pynput import keyboard
from core import *
from control import *
import code_24.old_lidar_interface as old_lidar_interface
from central_logger import CentralLogger

interface = None
lidar_proc = None
stop_event = mp.Event()
running_loop = True

logger_instance = CentralLogger(sensor_name="main")
logger = logger_instance.get_logger()

old_multiplot = CentralLogger(sensor_name="old").get_logger()

def keyboard_listener(key: keyboard.Key) -> None:
    """
    Callback function to handle key press events.

    Args:
        key (keyboard.Key): pressed key.
    """

    if key == keyboard.Key.enter:
        logger.info("Running...")
        logger.info("Press CTRL+C to stop the code")

listener = keyboard.Listener(on_press=keyboard_listener)


def init():
    global interface, lidar_proc
    
    interface = {
        "steer": PWM(channel=1, frequency=50.0),
        "speed": PWM(channel=0, frequency=50.0),
        "serial": Serial("/dev/ttyACM", 9600, timeout=0.1)
    }
    
    lidar_proc = mp.Process(target=old_lidar_interface.lidar_process, args=(old_lidar_interface.last_lidar_read, stop_event))
    lidar_proc.start()
    
    # Start live plotting (may slow things down)
    old_lidar_interface.start_live_plot(old_lidar_interface.last_lidar_read)
    
    interface["steer"].start(7.5)
    interface["speed"].start(7.5)

    time.sleep(0.5)

    steer_dc, speed_dc = stop_command()

    interface["steer"].set_duty_cycle(steer_dc)
    interface["speed"].set_duty_cycle(speed_dc)

    interface["serial"].read(depth=5)

    if interface["serial"].is_available():
        logger.info("Serial comm is stable and working")
    else:
        logger.info("Serial comm is not responding, so closing it")

    logger.info("Press ENTER to start the code")
    
    # Checking for Ctrl + C to end program
    try:
        listener.start()
    except RuntimeError:
        pass


def loop():
    try:
        raw_lidar = np.zeros(360, dtype=float)
        last_process_time = 0.0
        
        while not stop_event.is_set():
            start_time = time.time()  # Start timing
            with old_lidar_interface.last_lidar_update.get_lock():
                if old_lidar_interface.last_lidar_update.value > last_process_time:
                    last_process_time = old_lidar_interface.last_lidar_update.value
                else:
                    #print("No new lidar readings")
                    continue
                
            with old_lidar_interface.last_lidar_read.get_lock():
                raw_lidar[:] = np.array([old_lidar_interface.last_lidar_read[i] for i in range(360)])
            
            serial = interface["serial"].read(depth=5)
            data = {"serial": serial}
            
            shrinked = shrink_space(raw_lidar)
            
            steer, steer_dc, target_angle = compute_steer_from_lidar(shrinked)
            speed, speed_dc = compute_speed(shrinked, steer)

            end_time = time.time()  # End timing
            elapsed_time = end_time - start_time
            print(f"Loop time: {elapsed_time*1000000:.2f} us")

            speed_m_per_s = serial[0]/213
            logger_instance.logConsole(f"{serial} \t target={target_angle:.2f}deg \t Speed={speed_m_per_s:.2f}m/s")
            
            if check_reverse(shrinked):
                logger.info("Reverse")
                reverse(interface, shrinked)
            else:
                interface["steer"].set_duty_cycle(steer_dc)
                interface["speed"].set_duty_cycle(8.1)

            old_multiplot.debug(f"{[*serial, steer, speed, raw_lidar.tolist()]}")

        running_loop = False
        
    except (KeyboardInterrupt, Exception) as error:
        if not isinstance(error, KeyboardInterrupt):
            logger.info(f"Exception: {error}")
            traceback.print_exc()

        if isinstance(error, RPLidarException):
                logger.info(f"RPLidarException: {error}")

def close_interfaces():
    global interface, lidar_proc, stop_event

    logger.info("Closing the interface elements")

    steer_dc, speed_dc = stop_command()

    interface["steer"].set_duty_cycle(steer_dc)
    interface["speed"].set_duty_cycle(0)

    interface["steer"].stop()
    interface["speed"].stop()
    interface["serial"].close()
            
    if lidar_proc is not None:
        stop_event.set()
        lidar_proc.join()

def main():
    logger.info(f"Starting Voiture {NOM_VOITURE}")
    
    init()
    
    
    while running_loop and not stop_event.is_set():
        loop()

    close_interfaces()

if __name__ == "__main__":
    main()
