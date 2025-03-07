# serial_singleton.py
import multiprocessing as mp
import time
from core import Serial  # Your original Serial class


# Shared memory that any process can read
# NOTE: We store [speed, ultrasonic, battery] in that order
_last_serial_read = mp.Array('d', 3)  # [speed, ultrasonic, battery]

# Optional: store a "last update time" too
_last_serial_update = mp.Value('d', 0.0)

# We’ll use an Event to signal the reader process to stop
_stop_event = mp.Event()

# We’ll keep a reference to the background process here
_process = None


def _serial_process(port, baudrate, timeout):
    """
    Target function that runs in the background, continuously reading
    from the serial port and updating our shared Array/Value.
    """
    print("[Serial] Child Process started.")
    ser_conn = Serial(port, baudrate, timeout)

    try:
        while not _stop_event.is_set():
            # Read data
            speed, ultrasonic, battery = ser_conn.read(depth=5)

            # Update shared memory
            with _last_serial_read.get_lock():
                _last_serial_read[0] = speed
                _last_serial_read[1] = ultrasonic
                _last_serial_read[2] = battery

            # Update last_serial_update time
            with _last_serial_update.get_lock():
                _last_serial_update.value = time.time()

            # A small sleep to avoid CPU hammering
            time.sleep(0.05)
    except KeyboardInterrupt as eint:
        _stop_event.set()
    except Exception as e:
        print(f"[Serial] Exception in background process: {e}")

    finally:
        ser_conn.close()
        print("[Serial] Child Process exiting.")


def init_serial(port="/dev/ttyACM0", baudrate=9600, timeout=1.0):
    """
    Starts the background process if not already started.
    You can call this once in your main program.
    """
    global _process

    if _process is not None and _process.is_alive():
        print("[Serial] Background process is already running.")
        return

    # Reset the stop event in case it was set before
    _stop_event.clear()

    # Create and start the background process
    _process = mp.Process(target=_serial_process,
                          args=(port, baudrate, timeout),
                          daemon=True)  # daemon=True often helpful
    _process.start()
    print("[Serial] Background process started.")


def shutdown_serial():
    """
    Gracefully shuts down the background process.
    """
    global _process

    if _process is None:
        return

    print("[Serial] Shutting down background process...")
    _stop_event.set()
    _process.join()
    _process = None


#
# Expose "getter" functions so we don't ever pass the shared Array around.
#
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
