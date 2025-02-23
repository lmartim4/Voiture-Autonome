import time
import traceback
from central_logger import CentralLogger
from datetime import datetime
from core import Serial

class SerialReader:
    def __init__(self, logger, port="/dev/ttyACM", baudrate=115200, timeout=0.1):
        """
        Initializes the SerialReader with a given Logger instance.

        Args:
            logger: An instance of a Logger that has at least an 'info' and 'error' method.
            port (str): Serial port to connect to.
            baudrate (int): Baud rate for the serial communication.
            timeout (float): Timeout value for the serial connection.
        """
        # Get the central logger instance
        logger_instance = CentralLogger(sensor_name="SerialReader")
        logger = logger_instance.get_logger()
        self.comm = Serial(port, baudrate, timeout)

    def start(self):
        """
        Starts the serial reading loop, logging each line read using the provided logger.
        """
        try:
            while self.comm.is_available():
                self.comm.serial.reset_input_buffer()
                line = self.comm.serial.readline()
                self.logger.info(line)
                self.logger.logSensorData(line)
                time.sleep(0.2)

            self.logger.info("Serial comm is not available")
        except KeyboardInterrupt:
            # Allow graceful exit on keyboard interruption.
            pass
        except Exception:
            self.logger.error(traceback.format_exc())
        finally:
            self.comm.close()

def main():
	l = log.Logger()
	reader = SerialReader(logger=l)
	reader.start()

if __name__ == "__main__":
    main()    
