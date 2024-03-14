import numpy as np

from typing import List

from serial import Serial

from rplidar import RPLidar

from rpi_hardware_pwm import HardwarePWM

from console import Console

from control import stop_command
from control import compute_steer
from control import compute_speed


MIN_NEW_POINTS = 200

console = Console()

interface = None


def init() -> bool:
    """
    Initializes the elements that interface between the
    code and the vehicle, i.e. the sensors and actuators.

    Returns:
        bool: indicates whether the code has been initialized.
    """

    global interface

    console.info("Initializing sensors and actuators")

    interface = {
        "lidar": RPLidar("/dev/ttyUSB0", baudrate=256000),
        "steer": HardwarePWM(pwm_channel=1, hz=50),
        "speed": HardwarePWM(pwm_channel=0, hz=50),
        "serial": Serial("/dev/ttyACM0", 1152000, timeout=1)
    }

    health = interface["lidar"].get_health()[0]
    console.info(f"Lidar's health is {health.lower()}")

    interface["lidar"].stop()
    interface["lidar"].stop_motor()
    interface["lidar"].disconnect()

    steer_pwm, speed_pwm = stop_command()

    interface["steer"].start(steer_pwm)
    interface["speed"].start(speed_pwm)

    try:
        console.info("Press ENTER to start the code")
        input()

        interface["lidar"].connect()
        interface["lidar"].start()

        console.info("Running...")
        console.info("Press CTRL+C to stop the code")

        return True

    except KeyboardInterrupt:
        return False


def close() -> None:
    """
    Properly closes interface elements.
    """

    global interface

    console.info("Closing the interface elements")

    interface["lidar"].stop()
    interface["lidar"].stop_motor()
    interface["lidar"].disconnect()

    steer_pwm, speed_pwm = stop_command()

    interface["steer"].change_duty_cycle(steer_pwm)
    interface["speed"].change_duty_cycle(speed_pwm)

    console.close()


def read_serial() -> List[float]:
    # Speed, rear distance and battery voltage
    interface["serial"].reset_input_buffer()

    serial = interface["serial"].readline().decode("utf8")
    serial = serial.replace("\r\n", "").split("/")

    if len(serial) != 3:
        return read_serial()

    return [float(value) for value in serial]


def main() -> None:
    """
    Function to handle with different vehicle state.
    """

    global interface

    if not init():
        return close()

    try:
        updated = np.zeros(360, dtype=bool)
        distances = np.zeros(360, dtype=float)

        for scan in interface["lidar"].iter_scans():
            scan = np.asarray(scan)[:, 1:]

            indices = np.round(scan[:, 0]).astype(int)
            indices = np.clip(indices, 0, 359)

            updated[indices] = True
            distances[indices] = scan[:, 1] / 1000.0

            if np.count_nonzero(updated) < MIN_NEW_POINTS:
                continue

            data = {"lidar": distances, "serial": read_serial()}

            steer, steer_pwm = compute_steer(data)
            speed, speed_pwm = compute_speed(data)

            console.info(f"{steer:.2f} deg {100 * speed:.0f}%")
            console.info(data["serial"])

            interface["steer"].change_duty_cycle(steer_pwm)
            interface["speed"].change_duty_cycle(speed_pwm)

            console.log(
                [*data["serial"], steer, speed, distances.tolist()])

            updated[:] = False

    except (KeyboardInterrupt) as error:
        console.info(error)

    close()


if __name__ == "__main__":
    main()
