import inspect
from functools import wraps
from typing import Dict, Optional
from loguru import logger

from asgi_correlation_id import CorrelationIdMiddleware
from asgi_correlation_id.context import correlation_id

def correlation_id_filter(record):
    record['correlation_id'] = correlation_id.get()
    caller_info = record['extra'].get('caller_info', None)
    if caller_info is not None:
        record['name'] = caller_info.get('name')
        record['line'] = caller_info.get('line')
    return record['correlation_id']


def log_function(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return log_function_wrapper(func, *args, **kwargs,
                is_class_method=False)
    return wrapper


def log_function_with(caller_info: Optional[Dict], log_function_arguments: bool=False):
    def internal_inject(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return log_function_wrapper(func, *args,**kwargs,
                is_class_method=False,
                caller_info=caller_info,
                log_function_arguments=log_function_arguments)
        return wrapper
    return internal_inject


def log_method(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return log_function_wrapper(func, *args, **kwargs,
                is_class_method=True)
    return wrapper


def log_method_with(caller_info: Optional[Dict], log_function_arguments: bool=False):
    def internal_inject(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return log_function_wrapper(func, *args,**kwargs,
                is_class_method=True,
                caller_info=caller_info,
                log_function_arguments=log_function_arguments)
        return wrapper
    return internal_inject


def get_caller_info():
    frame = inspect.currentframe().f_back
    module = inspect.getmodule(frame)
    module_name = module.__name__ if module else '__main__'
    lineno = frame.f_lineno
    return dict(name=module_name, line=lineno)


def log_function_wrapper(func, *args,
        is_class_method: bool=True, log_function_arguments: bool=False,
        caller_info: Optional[Dict]=None,
        **kwargs):
    xlogger = logger if caller_info is None else logger.bind(caller_info=caller_info)

    try:
        if log_function_arguments:
            if is_class_method:
                xlogger.debug(f"{func.__qualname__} method started with args={args[1:]}, kwargs={kwargs}")
            else:
                xlogger.debug(f"{func.__qualname__} function started with args={args}, kwargs={kwargs}")
        else:
            if is_class_method:
                xlogger.debug(f"{func.__qualname__} method started")
            else:
                xlogger.debug(f"{func.__qualname__} function started")
    except: ...

    try:
        result = func(*args, **kwargs)
    except Exception as error:
        xlogger.exception(f"{func.__qualname__} failed with exception", exc_info=error)
        raise error

    try:
        xlogger.debug(f"{func.__qualname__} completed successfully")
    except: ...

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
