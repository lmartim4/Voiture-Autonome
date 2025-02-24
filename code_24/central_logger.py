import logging
import datetime
import os
import pyperclip
import shutil  # Added for file copying

NORMAL = "\33[0m"
GREEN = "\33[32m"
BLUE  = "\33[34m"
GRAY  = "\33[90m"
UNDERLINE = "\33[4m"

class CentralLogger:
    _instance = None
    _sensor_name = None
    _initial_timestamp = None  # Store the initial timestamp
    _date_str = None
    _time_str = None
    _log_dir = None
    _main_logger = None  # Dedicated logger for main.log
    
    def __new__(cls, sensor_name=None):
        if sensor_name is None:
            raise ValueError("A sensor name must be provided")
        
        # If it's the very first time, create the instance and set up folders
        if cls._instance is None:
            cls._instance = super(CentralLogger, cls).__new__(cls)
            
            # Capture the initial timestamp, date, and time
            cls._initial_timestamp = datetime.datetime.now()
            cls._date_str = cls._initial_timestamp.strftime("%Y-%m-%d")
            cls._time_str = cls._initial_timestamp.strftime("%H-%M-%S")
            
            # Create directory structure: logs/YYYY-MM-DD/HH-MM-SS
            cls._log_dir = os.path.join("../logs", cls._date_str, cls._time_str)
            os.makedirs(cls._log_dir, exist_ok=True)
            
            # Initialize both the main logger and the general logger
            cls._instance._initialize_base_logger()
            cls._instance._initialize_main_logger()
            
            # Backup the config file (if it exists)
            cls._instance._backup_config_file()

        # Each time, set the sensor name and ensure the sensor has its own FileHandler
        cls._sensor_name = sensor_name
        cls._instance._setup_sensor_file_handler(sensor_name)
        
        return cls._instance

    def _backup_config_file(self):
        """
        Check for the existence of a config file in the current working directory.
        If it exists, copy it into the log directory as config.json.
        """
        config_source = "config.json"  # adjust the path if your config is located elsewhere
        backup_destination = os.path.join(self._log_dir, "config.json")
        if os.path.exists(config_source):
            try:
                shutil.copyfile(config_source, backup_destination)
                self.logConsole("Config file backed up successfully.")
            except Exception as e:
                self.logConsole(f"Failed to backup config file: {e}")
        else:
            self.logConsole("Config file not found. No backup created.")

    def _initialize_base_logger(self):
        """Initialize a base logger for all logs, including sensor-specific logs."""
        self.logger = logging.getLogger("CentralLogger")
        self.logger.setLevel(logging.DEBUG)
        
        # Console stream handler
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.DEBUG)
        stream_format = logging.Formatter(
            '%(asctime)s, %(name)s, %(levelname)s, %(message)s'
        )
        stream_handler.setFormatter(stream_format)
        self.logger.addHandler(stream_handler)
    
    def _initialize_main_logger(self):
        """Create a dedicated logger for the main log file."""
        self._main_logger = logging.getLogger("MainLogger")
        self._main_logger.setLevel(logging.DEBUG)
               
        # File handler for main.log
        main_log_file = os.path.join(self._log_dir, "main.log")
        main_file_handler = logging.FileHandler(main_log_file, mode='a')
        main_file_handler.setLevel(logging.DEBUG)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        
        # Formatter
        main_file_format = logging.Formatter(
            '%(asctime)s, %(name)s, %(levelname)s, %(message)s'
        )
        main_file_handler.setFormatter(main_file_format)
        
        # Add handler only if it’s not already attached
        if not self._main_logger.handlers:
            self._main_logger.addHandler(main_file_handler)
            self._main_logger.addHandler(console_handler) 
       
    def _setup_sensor_file_handler(self, sensor_name):
        """Create a dedicated file handler for each sensor's logs without printing to console."""
        if sensor_name == "old":
            pyperclip.copy(f"python old_multiplot.py \"{self._log_dir}/old.log\"")
            self.logConsole("Multiplot command copied to clipboard\n")
        
        file_path = os.path.join(self._log_dir, f"{sensor_name}.log")
        
        # Get a dedicated logger for the sensor
        sensor_logger = logging.getLogger(f"{sensor_name}")
        sensor_logger.setLevel(logging.DEBUG)
        
        # Remove existing handlers to prevent duplicate logging
        sensor_logger.handlers.clear()

        # Create a file handler for the sensor
        file_handler = logging.FileHandler(file_path, mode='a')
        file_handler.setLevel(logging.DEBUG)

        # CSV-like formatter
        file_format = logging.Formatter(
            '%(relativeCreated).3f\t%(message)s'
        )
        file_handler.setFormatter(file_format)

        # Attach only the file handler (NO console handler!)
        sensor_logger.addHandler(file_handler)

        # Store the sensor logger so it doesn't use the main logger
        setattr(self, f"{sensor_name}", sensor_logger)

    def get_logger(self):
        """
        Return the appropriate logger.
        - If it's the main logger, return `_main_logger`.
        - If it's a sensor logger, return its dedicated logger.
        """
        if self._sensor_name and hasattr(self, f"{self._sensor_name}"):
            return getattr(self, f"{self._sensor_name}")
        
        return self._main_logger  # Default to main logger
    
    def get_logger_by_name(self, logger_name: str):
        """
        Return a specific logger by its name.
        """
        return logging.getLogger(logger_name)

    def logConsole(self, message: str) -> None:
        """
        Log a message exclusively to the main log file and prints a colored message to the console.
        """
        # Format a timestamp for display
        timestamp_str = datetime.datetime.now().strftime("%H:%M:%S")

        # Log the message to the main log file
        self._main_logger.log(logging.INFO, f"{GREEN}{timestamp_str} {BLUE}[INFO]{NORMAL} {message}")
