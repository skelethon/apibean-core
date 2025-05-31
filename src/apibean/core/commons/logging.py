import inspect
import json

from functools import wraps
from typing import Callable, Dict, Optional
from loguru import logger
from pydantic import BaseModel

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
        arguments_extractor: Optional[Callable]=None,
        log_function_arguments: bool=False, 
        ignore_log_exception: bool=False,
        **log_kwargs):
    def internal_inject(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return log_function_wrapper(func, args, kwargs,
                is_class_method=False,
                arguments_extractor=arguments_extractor,
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
        arguments_extractor: Optional[Callable]=None,
        log_function_arguments: bool=False, 
        ignore_log_exception: bool=False,
        **log_kwargs):
    def internal_inject(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            return log_function_wrapper(func, args, kwargs,
                is_class_method=True,
                arguments_extractor=arguments_extractor,
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
        is_class_method: bool=True,
        log_function_arguments: bool=False,
        arguments_extractor: Optional[Callable]=None,
        return_values_extractor: Optional[Callable]=None,
        ignore_log_begin: bool=False, ignore_log_end: bool=False,
        ignore_log_exception: bool=False,
        logging_level: str='DEBUG',
        caller_info: Optional[Dict]=None):
    xlogger = logger if caller_info is None else logger.bind(caller_info=caller_info)

    if ignore_log_begin is not True:
        if callable(arguments_extractor):
            try:
                args_str = arguments_extractor(args[1:] if is_class_method else args, kwargs)
            except Exception as exc:
                args_str = f"<arguments_extractor-error: {str(exc)}>"

            if not isinstance(args_str, str):
                args_str = str(args_str)

            xlogger.log(logging_level, f"{func.__qualname__} function started with: { args_str }")

        elif log_function_arguments:
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
        if callable(return_values_extractor):
            try:
                return_values = return_values_extractor(result)
            except Exception as exc:
                return_values = f"<return_values_extractor-error: {str(exc)}>"

            if not isinstance(return_values, str):
                return_values = str(return_values)

            xlogger.log(logging_level, f"{func.__qualname__} return with values '{return_values}'")
        else:
            xlogger.log(logging_level, f"{func.__qualname__} ... done")

    return result


def jsonify_func_arg(arg):
    if isinstance(arg, BaseModel):
        return arg.model_dump_json(exclude_none=True)
    try:
        return json.dumps(arg, ensure_ascii=False, default=str)
    except:
        return None


from contextvars import ContextVar
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger

DEFAULT_LOG_LEVEL = "DEBUG"

# ContextVar lưu mức log hiện tại cho mỗi request
current_log_level: ContextVar[str] = ContextVar("current_log_level", default=DEFAULT_LOG_LEVEL)

# Hàm filter theo mức log trong ContextVar
def dynamic_log_filter(record):
    try:
        level = current_log_level.get()
        return logger.level(record["level"].name).no >= logger.level(level).no
    except Exception:
        return True  # fallback nếu có lỗi


class LogLevelMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        header_level = request.headers.get("X-Log-Level", DEFAULT_LOG_LEVEL).upper()
        try:
            # Kiểm tra tính hợp lệ của log level
            logger.level(header_level)
            current_log_level.set(header_level)
        except ValueError:
            logger.warning(f"Invalid X-Log-Level: {header_level} — fallback to INFO")
            current_log_level.set(DEFAULT_LOG_LEVEL)

        response = await call_next(request)
        return response


def logging_support_filter(record):
    correlation_id_filter(record)
    return dynamic_log_filter(record)


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
    "dynamic_log_filter",
    "LogLevelMiddleware",
    "logging_support_filter",
]
