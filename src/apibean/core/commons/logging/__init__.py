import os, sys

from app.core.config import configs

from .correlation import (correlation_id_filter, CorrelationIdMiddleware)

from .decorators import (logger, get_caller_info,
        log_function, log_function_with,
        log_method, log_method_with,
        jsonify_func_arg)

def configure_logging():
    logger.remove()

    stdout_logger_id = None
    if configs.LOG_STDOUT_ENABLED is not False:
        opts1 = dict(level=configs.LOG_STDOUT_LEVEL,
            colorize=configs.LOG_STDOUT_COLORS)
        if configs.LOG_STDOUT_FORMAT is not None:
            opts1.update(format=configs.LOG_STDOUT_FORMAT)
        stdout_logger_id = logger.add(sys.stdout, **opts1)

    file_logger_id = None
    if configs.LOG_FILE_ENABLED is not False:
        opts2 = dict(filter=logging_support_filter,
            level=configs.LOG_FILE_LEVEL,
            colorize=configs.LOG_FILE_COLORS)
        if configs.LOG_FILE_FORMAT is not None:
            opts2.update(format=configs.LOG_FILE_FORMAT)
        if configs.LOG_FILE_ROTATION is not None:
            opts2.update(rotation=configs.LOG_FILE_ROTATION)
        if configs.LOG_FILE_RETENTION is not None:
            opts2.update(retention=configs.LOG_FILE_RETENTION)
        if configs.LOG_FILE_COMPRESSION is not None:
            opts2.update(compression=configs.LOG_FILE_COMPRESSION)
        file_logger_id = logger.add(os.path.join(configs.LOG_FILE_DIR, configs.LOG_FILE_PATTERN_NAME), **opts2)

    return (stdout_logger_id, file_logger_id)


from .dynamic_level import dyna_log_level_filter, DynaLogLevelMiddleware

def logging_support_filter(record):
    correlation_id_filter(record)
    return dyna_log_level_filter(record)


__all__ = [
    "logger",
    "get_caller_info",
    "correlation_id_filter",
    "CorrelationIdMiddleware",
    "log_function",
    "log_function_with",
    "log_method",
    "log_method_with",
    "jsonify_func_arg",
    "dyna_log_level_filter",
    "DynaLogLevelMiddleware",
    "logging_support_filter",
]
