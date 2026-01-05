import logging
import sys
import os
from datetime import datetime
from typing import Optional
from enum import Enum

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils import config


class LogLevel(Enum):
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL


_logger: Optional[logging.Logger] = None
_file_handler: Optional[logging.FileHandler] = None


def setup_logger(name: str = "tcp_server", log_level: Optional[str] = None):
    global _logger, _file_handler
    
    if _logger is not None:
        return _logger
    
    if log_level is None:
        log_level = config.get_log_level()
    
    level_map = {
        "DEBUG": LogLevel.DEBUG.value,
        "INFO": LogLevel.INFO.value,
        "WARNING": LogLevel.WARNING.value,
        "ERROR": LogLevel.ERROR.value,
        "CRITICAL": LogLevel.CRITICAL.value
    }
    
    level = level_map.get(log_level.upper(), LogLevel.INFO.value)
    
    _logger = logging.getLogger(name)
    _logger.setLevel(level)
    
    if _logger.handlers:
        return _logger
    
    formatter = logging.Formatter(
        '[%(asctime)s] [%(levelname)s] %(message)s',
        datefmt='%H:%M:%S'
    )
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(formatter)
    _logger.addHandler(console_handler)
    
    if config.get_log_to_file():
        try:
            log_file = config.get_log_file()
            _file_handler = logging.FileHandler(log_file, encoding='utf-8')
            _file_handler.setLevel(level)
            _file_handler.setFormatter(formatter)
            _logger.addHandler(_file_handler)
        except Exception as e:
            _logger.warning(f"Could not setup file logging: {e}")
    
    return _logger


def get_logger(name: str = "tcp_server") -> logging.Logger:
    if _logger is None:
        return setup_logger(name)
    return _logger


def debug(message: str):
    get_logger().debug(message)


def info(message: str):
    get_logger().info(message)


def warning(message: str):
    get_logger().warning(message)


def error(message: str):
    get_logger().error(message)


def critical(message: str):
    get_logger().critical(message)

