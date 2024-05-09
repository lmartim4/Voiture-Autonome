import traceback

import numpy as np

from pynput import keyboard

from console import Console

from core import *

from control import *


console = Console()

running = False

interface = None


def on_press(key: keyboard.Key) -> None:
    """
    Callback function to handle key press events.

    Args:
        key (keyboard.Key): pressed key.
    """

    global running

    if key == keyboard.Key.enter and not running:
        running = True

        console.info("Running...")
        console.info("Press CTRL+C to stop the code")


listener = keyboard.Listener(on_press=on_press)


def init() -> None:
    """
    Initializes the interface elements.
    """

    global interface

    interface = {
        "lidar": RPLidar("/dev/ttyUSB", baudrate=256000),
        "steer": PWM(channel=1, frequency=50.0),
        "speed": PWM(channel=0, frequency=50.0),
        "serial": Serial("/dev/ttyACM", 115200, timeout=0.1)
    }

    health = interface["lidar"].get_health()[0]
    console.info(f"Lidar's health is {health.lower()}")

    interface["lidar"].connect()
    interface["lidar"].start_motor()
    interface["lidar"].start()

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


def close() -> None:
    """
    Closes the interface elements properly.
    """

    global interface

    console.info("Closing the interface elements")

    try:
        interface["lidar"].stop()
        interface["lidar"].stop_motor()
        interface["lidar"].disconnect()

    except serial.serialutil.PortNotOpenError:
        pass

    steer_dc, speed_dc = stop_command()

    interface["steer"].set_duty_cycle(steer_dc)
    interface["speed"].set_duty_cycle(speed_dc)

    interface["steer"].stop()
    interface["speed"].stop()

    interface["serial"].close()

    console.close()


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
        distances = np.zeros(360, dtype=float)

        for scan in interface["lidar"].iter_scans():
            scan = np.asarray(scan)[:, 1:]

            indices = np.round(scan[:, 0]).astype(int)
            indices = np.clip(indices, 0, 359)

            distances[indices] = scan[:, 1] / 1000.0

            if not running:
                continue

            if np.count_nonzero(distances) < 60:
                continue

            for index in range(1, 360):
                if distances[index] == 0.0:
                    distances[index] = distances[index-1]

            serial = interface["serial"].read(depth=5)
            data = {"lidar": distances, "serial": serial}

            steer, steer_dc = compute_steer(data)
            speed, speed_dc = compute_speed(data, steer)

            console.info(f"{serial} {steer:.2f} deg {100 * speed:.0f}%")

            if check_reverse(data):
                console.info("Reverse")
                reverse(interface, data)

            else:
                interface["steer"].set_duty_cycle(steer_dc)
                interface["speed"].set_duty_cycle(speed_dc)

            console.log([*serial, steer, speed, distances.tolist()])

            distances = 0.0 * distances

    except (KeyboardInterrupt, Exception) as error:
        if not isinstance(error, KeyboardInterrupt):
            traceback.print_exc()

        if isinstance(error, RPLidarException):
            main(bypass=True)

    close()


if __name__ == "__main__":
    main()
