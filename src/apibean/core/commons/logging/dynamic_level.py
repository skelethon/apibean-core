from contextvars import ContextVar
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger

DEFAULT_LOG_LEVEL = "DEBUG"

# ContextVar lưu mức log hiện tại cho mỗi request
current_log_level: ContextVar[str] = ContextVar("current_log_level", default=DEFAULT_LOG_LEVEL)

# Hàm filter theo mức log trong ContextVar
def dyna_log_level_filter(record):
    try:
        level = current_log_level.get()
        return logger.level(record["level"].name).no >= logger.level(level).no
    except Exception:
        return True  # fallback nếu có lỗi


class DynaLogLevelMiddleware(BaseHTTPMiddleware):
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
