import logging
import datetime
import os
import shutil

NORMAL = "\33[0m"
GREEN = "\33[32m"
BLUE  = "\33[34m"
GRAY  = "\33[90m"
UNDERLINE = "\33[4m"

class CentralLogger:
    _instance = None
    _sensor_name = None
    _initial_timestamp = None
    _date_str = None
    _time_str = None
    _log_dir = None
    _main_logger = None
    
    def __new__(cls, sensor_name=None):
        if sensor_name is None:
            raise ValueError("A sensor name must be provided")
        
        if cls._instance is None:
            cls._instance = super(CentralLogger, cls).__new__(cls)
            
            cls._initial_timestamp = datetime.datetime.now()
            cls._date_str = cls._initial_timestamp.strftime("%Y-%m-%d")
            cls._time_str = cls._initial_timestamp.strftime("%H-%M-%S")
            cls._log_dir = os.path.join("../logs", cls._date_str, cls._time_str)

            os.makedirs(cls._log_dir, exist_ok=True)
            
            cls._instance._initialize_base_logger()
            cls._instance._initialize_main_logger()
            
            cls._instance._backup_config_file()

        cls._sensor_name = sensor_name
        cls._instance._setup_sensor_file_handler(sensor_name)
        
        return cls._instance

    def _backup_config_file(self):
        """
        Check for the existence of a config file in the current working directory.
        If it exists, copy it into the log directory as config.json.
        """
        config_source = "config.json"
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
        
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.DEBUG)
        stream_format = logging.Formatter(
            '%(asctime)s, %(name)s, %(levelname)s, %(message)s'
        )
        stream_handler.setFormatter(stream_format)
        self.logger.addHandler(stream_handler)
    
    def _initialize_main_logger(self):
        self._main_logger = logging.getLogger("MainLogger")
        self._main_logger.setLevel(logging.DEBUG)
               
        main_log_file = os.path.join(self._log_dir, "main.log")
        main_file_handler = logging.FileHandler(main_log_file, mode='a')
        main_file_handler.setLevel(logging.DEBUG)
        
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.DEBUG)
        
        main_file_format = logging.Formatter(
            '%(asctime)s, %(name)s, %(levelname)s, %(message)s'
        )
        main_file_handler.setFormatter(main_file_format)
        
        if not self._main_logger.handlers:
            self._main_logger.addHandler(main_file_handler)
            self._main_logger.addHandler(console_handler) 
       
    def _setup_sensor_file_handler(self, sensor_name):
        file_path = os.path.join(self._log_dir, f"{sensor_name}.log")
        
        sensor_logger = logging.getLogger(f"{sensor_name}")
        sensor_logger.setLevel(logging.DEBUG)
        
        sensor_logger.handlers.clear()

        file_handler = logging.FileHandler(file_path, mode='a')
        file_handler.setLevel(logging.DEBUG)

        file_format = logging.Formatter(
            '%(relativeCreated).3f\t%(message)s'
        )
        file_handler.setFormatter(file_format)

        sensor_logger.addHandler(file_handler)

        setattr(self, f"{sensor_name}", sensor_logger)

    def get_logger(self):
        if self._sensor_name and hasattr(self, f"{self._sensor_name}"):
            return getattr(self, f"{self._sensor_name}")
        
        return self._main_logger
    
    def get_logger_by_name(self, logger_name: str):
        return logging.getLogger(logger_name)

    def logConsole(self, message: str) -> None:
        timestamp_str = datetime.datetime.now().strftime("%H:%M:%S")
        self._main_logger.log(logging.INFO, f"{GREEN}{timestamp_str} {BLUE}[INFO]{NORMAL} {message}")
