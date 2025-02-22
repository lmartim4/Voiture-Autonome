import json
import os

CONFIG_PATH = "./config.json"

def get_config_value(cfg, key, default_value):
    """
    Retrieve a config value by `key`.
    If `key` is missing, store `default_value` in config and return it.
    """

    if key not in cfg:
        cfg[key] = default_value
        save_config(cfg)
        return default_value

    return cfg[key]


def load_config():
    # Load the JSON config into a dictionary
    print(f"Loading Config from {CONFIG_PATH}")
    
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, 'r') as f:
            return json.load(f)
    
    return {}

def save_config(config_data):
    with open(CONFIG_PATH, 'w') as f:
        json.dump(config_data, f, indent=4)