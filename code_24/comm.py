import time
import traceback
from datetime import datetime
from core import *


NORMAL = "\33[0m"
GREEN = "\33[32m"
BLUE  = "\33[34m"


def info(message: str) -> None:
    timestamp = datetime.now().strftime("%H:%M:%S")

    print(f"\r{GREEN}{timestamp} {BLUE}[INFO]{NORMAL} {message}")


def main() -> None:
	comm = Serial("/dev/ttyACM", 115200, 0.1)

	try:
		while comm.is_available():
			comm.serial.reset_input_buffer()
			info(comm.serial.readline())

			time.sleep(0.2)

		info("Serial comm is not available")

	except (KeyboardInterrupt, Exception) as error:
		if not isinstance(error, KeyboardInterrupt):
			traceback.print_exc()

	comm.close()


if __name__ == "__main__":
	main()
