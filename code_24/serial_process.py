import multiprocessing as mp
import time
from core import Serial

_last_serial_read = mp.Array('d', 3)  # [speed, ultrasonic, battery]
_last_serial_update = mp.Value('d', 0.0)
_stop_event = mp.Event()

_process = None

def _serial_process(port, baudrate, timeout):
    print("[Serial] Child Process started.")
    ser_conn = Serial(port, baudrate, timeout)

    try:
        while not _stop_event.is_set():
            speed, ultrasonic, battery = ser_conn.read(depth=5)

            with _last_serial_read.get_lock():
                _last_serial_read[0] = speed
                _last_serial_read[1] = ultrasonic
                _last_serial_read[2] = battery

            with _last_serial_update.get_lock():
                _last_serial_update.value = time.time()

            # A small sleep to avoid CPU hammering, it is now synchronous to main process
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

    _stop_event.clear()

    _process = mp.Process(target=_serial_process,
                          args=(port, baudrate, timeout),
                          daemon=True)
    _process.start()
    print("[Serial] Background process started.")


def shutdown_serial():
    global _process

    if _process is None:
        return

    print("[Serial] Shutting down background process...")
    _stop_event.set()
    _process.join()
    _process = None

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