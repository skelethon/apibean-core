import sys
from contextvars import ContextVar

DEFAULT_LOG_LEVEL = "DEBUG"
DEFAULT_STR_SINKS = "stdout"

# --- ContextVars ---
request_log_level: ContextVar[str] = ContextVar("request_log_level", default=DEFAULT_LOG_LEVEL)
default_log_level: ContextVar[str] = ContextVar("default_log_level", default=DEFAULT_LOG_LEVEL)

request_set_sinks: ContextVar[set] = ContextVar("request_set_sinks", default={DEFAULT_STR_SINKS})
default_set_sinks: ContextVar[set] = ContextVar("default_set_sinks", default={DEFAULT_STR_SINKS})
default_str_sinks: ContextVar[str] = ContextVar("default_str_sinks", default=DEFAULT_STR_SINKS)

def set_default_sinks(new_str_sinks: str):
    pass

# --- Sink registry ---
AVAILABLE_SINKS = {
    "stdout": {
        "enabled": True,
        "target": sys.stdout,
        "format": "<green>{time:HH:mm:ss}</green> | <level>{level}</level> | <cyan>{message}</cyan>",
    },
    "file": {
        "enabled": True,
        "type": "file",
        "target": "/tmp/log.log",
        "format": "{time} | {level} | {message} [file1]",
        "rotation": "100 MB",
        "retention": "10 days",
        "compression": "tar.gz",
        "colorize": False,
    },
    "null": {
        "enabled": True,
        "target": lambda _: None,
        "format": "{message}",
    },
    "network": {
        "enabled": False,
        "params": {
            "host": "localhost",
            "port": 9009,
        },
        "format": "{message}",
    },
    "opensearch": {
        "enabled": False,
        "params": {
            "url": "http://localhost:9200/logs/_doc",
            "username": None,
            "password": None,
        },
        "format": "{time} {level.name[0]} [{correlation_id}] {name}:{line} - {message}",
    },
    "syslog": {
        "enabled": False,
        "address": "/dev/log",
        "format": "{level}: {message}",
    },
}

CURRENT_SINKS = {}
