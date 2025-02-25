import cProfile
import pstats
import traceback
import threading
import time
import numpy as np
import multiprocessing as mp
from pynput import keyboard
from core import *
from control import *
import lidar_interface
from central_logger import CentralLogger, logging

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
        "serial": Serial("/dev/ttyACM", 115200, timeout=0.1)
    }

    # Start LIDAR process
    lidar_proc = mp.Process(target=lidar_interface.lidar_process, args=(lidar_interface.last_lidar_read, stop_event))
    lidar_proc.start()
    
    # Start live plotting (may slow things down)
    lidar_interface.start_live_plot(lidar_interface.last_lidar_read)

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
    with cProfile.Profile() as pr:
        try:
            lidar_read = np.zeros(360, dtype=float)
            last_process_time = 0.0
            
            while not stop_event.is_set():
                # Start measuring performance here
                start_time = time.time()
                
                with lidar_interface.last_lidar_update.get_lock():
                    if lidar_interface.last_lidar_update.value > last_process_time:
                        last_process_time = lidar_interface.last_lidar_update.value
                    else:
                        continue
                    
                with lidar_interface.last_lidar_read.get_lock():
                    lidar_read[:] = np.array([lidar_interface.last_lidar_read[i] for i in range(360)])
                
                serial = interface["serial"].read(depth=5)
                data = {"serial": serial}

                steer, steer_dc, target_angle = compute_steer_from_lidar(lidar_read)
                speed, speed_dc = compute_speed(lidar_read, steer)

                logger_instance.logConsole(f"{serial} target={target_angle:.2f} deg Speed = {100 * speed:.0f}%")
                
                if check_reverse(lidar_read):
                    logger.info("Reverse")
                    reverse(interface, data)
                else:
                    # If you want to send normal speed, replace the 0 below with speed_dc
                    interface["steer"].set_duty_cycle(steer_dc)
                    interface["speed"].set_duty_cycle(0)

                old_multiplot.debug(f"{[*serial, steer, speed, lidar_read.tolist()]}")
                
                # End measuring performance
                end_time = time.time()
                loop_time = end_time - start_time  # time in seconds
                logger.debug(f"Loop execution time: {loop_time * 1000:.2f} ms")

                time.sleep(0.1)
                
            running_loop = False
            
        except (KeyboardInterrupt, Exception) as error:
            if not isinstance(error, KeyboardInterrupt):
                logger.info(f"Exception: {error}")
                traceback.print_exc()

            if isinstance(error, RPLidarException):
                logger.info(f"RPLidarException: {error}")
                
    pr.dump_stats("profile_results.prof")

def close_interfaces():
    global interface, lidar_proc, stop_event

    logger.info("Closing the interface elements")

    steer_dc, speed_dc = stop_command()

    interface["steer"].set_duty_cycle(steer_dc)
    interface["speed"].set_duty_cycle(speed_dc)

    interface["steer"].stop()
    interface["speed"].stop()
    interface["serial"].close()
            
    if lidar_proc is not None:
        stop_event.set()
        lidar_proc.join()

def main():
    logger.info(f"Starting Voiture {NOM_VOITURE}")
    
    init()
    
    while(running_loop and not stop_event.is_set()):
        loop()

    close_interfaces()

if __name__ == "__main__":
    main()
