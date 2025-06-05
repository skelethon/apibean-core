import sys

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List

from loguru import logger

from .context import DEFAULT_LOG_LEVEL
from .context import CURRENT_SINKS
from . import context as ctx

router = APIRouter(prefix="/loggers", tags=["loggers"])

def _transform_sink_conf_to_info(name, config):
    active = ctx.request_set_sinks.get()
    sink_info = {
        "name": name,
        "level": DEFAULT_LOG_LEVEL,
        "enqueue": True,
        "enabled_for_current_request": name in active
    }

    fmt = config.get("format")
    if fmt:
        sink_info["format"] = fmt

    target = config.get("target")
    if isinstance(target, str):
        sink_info["type"] = "file"
        sink_info["target"] = target
    elif target == sys.stdout:
        sink_info["type"] = "stream"
        sink_info["target"] = "stdout"
    elif target == sys.stderr:
        sink_info["type"] = "stream"
        sink_info["target"] = "stderr"
    elif callable(target):
        sink_info["type"] = "function"
        sink_info["target"] = getattr(target, "__name__", str(target))
    else:
        sink_info["type"] = "unknown"
        sink_info["target"] = str(target)

    return sink_info

@router.get("/")
async def get_loggers():
    founds = []

    for name, config in CURRENT_SINKS.items():
        founds.append(_transform_sink_conf_to_info(name, config))

    return {
        "count": len(founds),
        "founds": founds,
        "default": {
            "level": ctx.default_log_level,
            "sinks": list(ctx.default_set_sinks)
        },
    }


@router.get("/{name}")
async def get_logger_detail(name: str):
    config = CURRENT_SINKS.get(name)
    if not config:
        raise HTTPException(status_code=404, detail=f"Sink '{name}' not found")

    return _transform_sink_conf_to_info(name, config)


class LoggerConfigRequest(BaseModel):
    level: str = ctx.default_log_level
    sinks: List[str] = list(ctx.default_set_sinks)


@router.post("/")
async def configure_logging(config: LoggerConfigRequest):
    try:
        logger.level(config.level.upper())
        ctx.default_log_level = config.level.upper()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid log level")

    valid_targets = set(config.sinks) & CURRENT_SINKS.keys()
    if not valid_targets:
        raise HTTPException(status_code=400, detail="No valid sinks provided")

    ctx.default_set_sinks = valid_targets
    ctx.default_str_sinks = ",".join(ctx.default_set_sinks)

    return {
        "message": "Logger configuration applied for current request",
        "default": {
            "level": ctx.default_log_level,
            "sinks": list(ctx.default_set_sinks)
        }
    }
