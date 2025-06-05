import sys

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger

from .context import DEFAULT_LOG_LEVEL
from . import context as ctx

# Hàm filter theo mức log trong ContextVar
def dyna_log_level_filter(record):
    try:
        level = ctx.request_log_level.get()
        return logger.level(record["level"].name).no >= logger.level(level).no
    except Exception:
        return True  # fallback nếu có lỗi


class DynaLogLevelMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        header_level = request.headers.get("X-Log-Level", ctx.default_log_level).upper()
        try:
            # Kiểm tra tính hợp lệ của log level
            logger.level(header_level)
            ctx.request_log_level.set(header_level)
        except ValueError:
            logger.warning(f"Invalid X-Log-Level: {header_level} — fallback to {ctx.default_log_level}")
            ctx.request_log_level.set(ctx.default_log_level)

        response = await call_next(request)
        return response


from .correlation import correlation_id_filter

def _logging_support_filter(record):
    correlation_id_filter(record)
    return dyna_log_level_filter(record)


def setup_static_loggers(configs = dict()):
    logger.remove()

    stdout_logger_id = None
    config = configs.get("stdout", {})
    if config.get("enabled", False):
        opts1 = dict(level=config.get("level", DEFAULT_LOG_LEVEL),
            colorize=config.get("colorize", True),
            filter=_logging_support_filter)
        if "format" in config:
            opts1.update(format=config.get("format"))
        stdout_logger_id = logger.add(sys.stdout, **opts1)

    file_logger_id = None
    config = configs.get("file", {})
    if config.get("enabled", False):
        opts2 = dict(level=config.get("level", DEFAULT_LOG_LEVEL),
            colorize=config.get("colorize", True),
            filter=_logging_support_filter)
        if "format" in config:
            opts2.update(format=config.get("format"))
        if "rotation" in config:
            opts2.update(rotation=config.get("rotation"))
        if "retention" in config:
            opts2.update(retention=config.get("retention"))
        if "compression" in config:
            opts2.update(compression=config.get("compression"))

        log_file = config.get("log_file", "/tmp/dyna.log")
        if log_file:
            file_logger_id = logger.add(log_file, **opts2)

    return (stdout_logger_id, file_logger_id)
