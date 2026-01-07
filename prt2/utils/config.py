import json
import os
from typing import Dict, Any

DEFAULT_CONFIG = {
    "server": {
        "host": "0.0.0.0",
        "port": 10000
    },
    "client": {
        "host": "192.168.0.106",
        "port": 10000
    },
    "limits": {
        "max_message_size": 4096,
        "read_timeout": 30.0,
        "max_name_length": 50,
        "rate_limit_messages_per_second": 10,
        "rate_limit_window_seconds": 1.0
    },
    "logging": {
        "level": "INFO",
        "log_to_file": False,
        "log_file": "server.log"
    }
}

_config: Dict[str, Any] = None


def load_config(config_file: str = "config.json") -> Dict[str, Any]:
    global _config
    if _config is not None:
        return _config
    
    config_path = os.path.join(os.path.dirname(__file__), config_file)
    
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                _config = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load config file: {e}. Using defaults.")
            _config = DEFAULT_CONFIG.copy()
    else:
        _config = DEFAULT_CONFIG.copy()
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(DEFAULT_CONFIG, f, indent=2, ensure_ascii=False)
            print(f"Created default config file: {config_path}")
        except Exception as e:
            print(f"Warning: Could not create config file: {e}")
    
    return _config


def get_config() -> Dict[str, Any]:
    if _config is None:
        return load_config()
    return _config


def get_server_host() -> str:
    return get_config()["server"]["host"]


def get_server_port() -> int:
    return get_config()["server"]["port"]


def get_client_host() -> str:
    return get_config()["client"]["host"]


def get_client_port() -> int:
    return get_config()["client"]["port"]


def get_max_message_size() -> int:
    return get_config()["limits"]["max_message_size"]


def get_read_timeout() -> float:
    return get_config()["limits"]["read_timeout"]


def get_max_name_length() -> int:
    return get_config()["limits"]["max_name_length"]


def get_rate_limit() -> tuple:
    config = get_config()["limits"]
    return (config["rate_limit_messages_per_second"], config["rate_limit_window_seconds"])


def get_log_level() -> str:
    return get_config()["logging"]["level"]


def get_log_to_file() -> bool:
    return get_config()["logging"]["log_to_file"]


def get_log_file() -> str:
    return get_config()["logging"]["log_file"]

