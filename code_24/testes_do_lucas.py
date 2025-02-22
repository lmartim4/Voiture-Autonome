import traceback
import threading
import numpy as np
import multiprocessing as mp
from pynput import keyboard
import logger
from core import *
from control import *
import lidar_interface

running = False
interface = None
lidar_queue = mp.Queue(maxsize=1)
lidar_proc = None
stop_event = mp.Event()

logger = logger.Logger()

def on_press(key: keyboard.Key) -> None:
    """
    Callback function to handle key press events.

    Args:
        key (keyboard.Key): pressed key.
    """

    global running

    if key == keyboard.Key.enter and not running:
        running = True

        logger.info("Running...")
        logger.info("Press CTRL+C to stop the code")

listener = keyboard.Listener(on_press=on_press)


def init() -> None:
    """
    Initializes the interface elements.
    """

    global interface, lidar_queue, lidar_proc
    
    interface = {
        "steer": PWM(channel=1, frequency=50.0),
        "speed": PWM(channel=0, frequency=50.0),
        "serial": Serial("/dev/ttyACM", 115200, timeout=0.1)
    }

    # Start LIDAR process
    lidar_proc = mp.Process(target=lidar_interface.lidar_process, args=(lidar_queue, stop_event))
    lidar_proc.start()

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
    
    #Checking for Ctrl + C to end program
    try:
        listener.start()
    except RuntimeError:
        pass


def close() -> None:
    """
    Closes the interface elements properly.
    """

    global interface, lidar_proc, stop_event

    logger.info("Closing the interface elements")

    steer_dc, speed_dc = stop_command()

    interface["steer"].set_duty_cycle(steer_dc)
    interface["speed"].set_duty_cycle(speed_dc)

    interface["steer"].stop()
    interface["speed"].stop()
    interface["serial"].close()

    # Stop the keyboard listener (new fix)
    if listener is not None and listener.running:
        logger.info("Stopping keyboard listener...")
        listener.stop()
        listener.join()
            
    # Ensure LIDAR process is stopped properly
    if lidar_proc is not None:
        logger.info("Stopping LIDAR process...")
        stop_event.set()  # Notify the lidar process to stop
        lidar_proc.join(timeout = 0.1)  # Give it time to exit
        
        if lidar_proc.is_alive():
            logger.info("LIDAR process did not exit cleanly, forcing termination.")
            lidar_proc.terminate()
            lidar_proc.join(timeout = 0.1)
        else:
            logger.info("LIDAR process exited cleanly.")

    logger.close()

def main(bypass: bool = False) -> None:
    """
    Main function to run the vehicle control logic.

    Args:
        bypass (bool, optional): bypass key press. Defaults to False.
    """

    global interface, running

    if bypass:
        running = True

    init()

    try:
        lidar_read = np.zeros(360, dtype=float)

        while not stop_event.is_set():  # Stop if lidar_process stops
            if not lidar_queue.empty():
                lidar_read = lidar_queue.get()

                if not running:
                    continue

                if np.count_nonzero(lidar_read) < 60:
                    continue

                # for index in range(1, 360):
                #     if distances[index] == 0.0:
                #         distances[index] = distances[index - 1]

                serial = interface["serial"].read(depth=5)
                data = {"lidar": lidar_read, "serial": serial}

                steer, steer_dc, target_angle = compute_steer_from_lidar(lidar_read)
                speed, speed_dc = compute_speed(data, steer)

                logger.info(f"{serial} {steer:.2f} deg {100 * speed:.0f}%")
                
                if check_reverse(data):
                    logger.info("Reverse")
                    reverse(interface, data)
                else:
                    interface["steer"].set_duty_cycle(steer_dc)
                    interface["speed"].set_duty_cycle(speed_dc)

                logger.log([*serial, steer, speed, lidar_read.tolist()])

                lidar_read = 0.0 * lidar_read

    except (KeyboardInterrupt, Exception) as error:
        if not isinstance(error, KeyboardInterrupt):
            traceback.print_exc()
        
        if isinstance(error, RPLidarException):
            main(bypass=True)
    
    close()


if __name__ == "__main__":
    main()