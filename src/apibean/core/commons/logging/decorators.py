import inspect
import json

from functools import wraps
from typing import Callable, Dict, Optional
from loguru import logger
from pydantic import BaseModel

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
