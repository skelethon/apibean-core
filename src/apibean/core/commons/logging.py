import inspect
from functools import wraps
from typing import Dict, Optional
from loguru import logger

from asgi_correlation_id import CorrelationIdMiddleware
from asgi_correlation_id.context import correlation_id


KEY_CALLER_INFO = 'caller_info'
KEY_CORRELATION_ID = 'correlation_id'
KEY_LOGGING_EXTRA = 'extra'
KEY_MODULE_NAME = 'name'
KEY_LINE_NUMBER = 'line'


def correlation_id_filter(record):
    record[KEY_CORRELATION_ID] = correlation_id.get()
    caller_info = record[KEY_LOGGING_EXTRA].get(KEY_CALLER_INFO, None)
    if caller_info is not None:
        record[KEY_MODULE_NAME] = caller_info.get(KEY_MODULE_NAME)
        record[KEY_LINE_NUMBER] = caller_info.get(KEY_LINE_NUMBER)
    return record[KEY_CORRELATION_ID]


def log_function(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return log_function_wrapper(func, args, kwargs,
                is_class_method=False)
    return wrapper


def log_function_with(caller_info: Optional[Dict],
        log_function_arguments: bool=False, 
        ignore_log_exception: bool=False,
        **log_kwargs):
    def internal_inject(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return log_function_wrapper(func, args, kwargs,
                is_class_method=False,
                log_function_arguments=log_function_arguments,
                ignore_log_exception=ignore_log_exception,
                caller_info=caller_info,
                **log_kwargs)
        return wrapper
    return internal_inject


def log_method(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return log_function_wrapper(func, args, kwargs,
                is_class_method=True)
    return wrapper


def log_method_with(caller_info: Optional[Dict],
        log_function_arguments: bool=False, 
        ignore_log_exception: bool=False,
        **log_kwargs):
    def internal_inject(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return log_function_wrapper(func, args, kwargs,
                is_class_method=True,
                log_function_arguments=log_function_arguments,
                ignore_log_exception=ignore_log_exception,
                caller_info=caller_info,
                **log_kwargs)
        return wrapper
    return internal_inject


def get_caller_info():
    frame = inspect.currentframe().f_back
    module = inspect.getmodule(frame)
    module_name = module.__name__ if module else '__main__'
    lineno = frame.f_lineno
    return dict(name=module_name, line=lineno)


def log_function_wrapper(func, args, kwargs,
        is_class_method: bool=True, log_function_arguments: bool=False,
        ignore_log_begin: bool=False, ignore_log_end: bool=False,
        ignore_log_exception: bool=False,
        logging_level: str='DEBUG',
        caller_info: Optional[Dict]=None):
    xlogger = logger if caller_info is None else logger.bind(caller_info=caller_info)

    if ignore_log_begin is not True:
        if log_function_arguments:
            try:
                if is_class_method:
                    xlogger.log(logging_level, f"{func.__qualname__} method started with args={args[1:]}, kwargs={kwargs}")
                else:
                    xlogger.log(logging_level, f"{func.__qualname__} function started with args={args}, kwargs={kwargs}")
            except: ...
        else:
            if is_class_method:
                xlogger.log(logging_level, f"{func.__qualname__} method started")
            else:
                xlogger.log(logging_level, f"{func.__qualname__} function started")

    if ignore_log_exception is not True:
        try:
            result = func(*args, **kwargs)
        except Exception as error:
            xlogger.exception(f"{func.__qualname__} failed with exception", exc_info=error)
            raise error
    else:
        result = func(*args, **kwargs)

    if ignore_log_end is not True:
        xlogger.log(logging_level, f"{func.__qualname__} completed successfully")

    return result

__all__ = [
    "logger",
    "get_caller_info",
    "correlation_id_filter",
    "CorrelationIdMiddleware",
    "log_function",
    "log_function_with",
    "log_method",
    "log_method_with",
]
