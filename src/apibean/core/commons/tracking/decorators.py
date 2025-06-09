from functools import wraps
from typing import Callable

from apibean.core.commons.logging import logger

DEFAULT_LEVEL = "DEBUG"


def pick_api_invoker(arg_key: str, *args, **kwargs):
    if len(args) > 0:
        return getattr(args[0], arg_key, None)
    return None


def get_or_set_default(redis_client, key: str, default_value: int, expire_seconds: int = None):
    value = redis_client.get(key)
    if value is not None:
        return value
    
    # Key chưa tồn tại → set default
    was_set = redis_client.setnx(key, default_value)
    
    if was_set and expire_seconds is not None:
        redis_client.expire(key, expire_seconds)
    
    # Đọc lại value (đảm bảo đúng value)
    value = redis_client.get(key)
    return value


async def get_or_set_default_async(redis_client, key: str, default_value: int, expire_seconds: int = None):
    value = await redis_client.get(key)
    if value is not None:
        return value
    
    # Key chưa tồn tại → set default
    was_set = await redis_client.setnx(key, default_value)
    
    if was_set and expire_seconds is not None:
        await redis_client.expire(key, expire_seconds)
    
    # Đọc lại value (đảm bảo đúng value)
    value = await redis_client.get(key)
    return value


def track_creations_on_service(model_type: str,
        tenant_code_key: str = "tenant_code",
        api_invoker_key: str = "api_invoker",
        pick_api_invoker: Callable = pick_api_invoker,
        restrict_key_pattern: str = "limitation_{tenant_code}_{model_type}",
        redis_client = None,
        default_limit_value: int = 10000,
        default_count_value: int = 0,
):
    """
    Decorator để tăng biến đếm Redis khi POST thành công.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            api_invoker = pick_api_invoker(api_invoker_key, *args, **kwargs)
            tenant_code = getattr(api_invoker, tenant_code_key, "unknown")

            logger.debug(f"tenant_code: [{ tenant_code }]")
            logger.debug(f"model_type: [{ model_type }]")

            redis_entrypoint = restrict_key_pattern.format(model_type=model_type, tenant_code=tenant_code)
            entrypoint_count = redis_entrypoint + "_count"
            entrypoint_limit = redis_entrypoint + "_limit"

            limit_value = default_limit_value
            if redis_client:
                limit_value = get_or_set_default(redis_client, entrypoint_limit, default_limit_value)
                logger.log(DEFAULT_LEVEL, f"read the limit value from [{entrypoint_limit}] is: {limit_value}")
            else:
                logger.log(DEFAULT_LEVEL, "the redis_client is not available")

            count_value = default_count_value
            if redis_client:
                count_value = get_or_set_default(redis_client, entrypoint_count, default_count_value)
                logger.log(DEFAULT_LEVEL, f"read the count value from [{entrypoint_count}] is: {count_value}")
            else:
                logger.log(DEFAULT_LEVEL, "the redis_client is not available")

            if count_value >= limit_value:
                raise LimitExceededError(f"total record [{count_value}] has exceeded [{limit_value}]")

            response = func(*args, **kwargs)

            # increase the count entry in redis
            if redis_client:
                logger.log(DEFAULT_LEVEL, "call the redis_client.incr")
                redis_client.incr(entrypoint_count)
            else:
                logger.log(DEFAULT_LEVEL, "the redis_client is not available")

            return response
        return wrapper
    return decorator


class LimitExceededError(Exception):
    pass
