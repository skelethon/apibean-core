import sys
import socket
import httpx
from datetime import datetime
from typing import Optional, Dict, Tuple

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger

from .correlation import correlation_id, correlation_id_filter

from .context import DEFAULT_LOG_LEVEL
from .context import AVAILABLE_SINKS, CURRENT_SINKS
from .context import request_log_level
from .context import request_set_sinks

# --- TCP/UDP network sink ---
class NetworkSink:
    def __init__(self, host="localhost", port=9009):
        self.addr = (host, port)
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.sock.connect(self.addr)
        except Exception as e:
            print(f"Network sink error: {e}", file=sys.stderr)

    def __call__(self, message):
        try:
            self.sock.sendall(message.encode())
        except Exception as e:
            print(f"Network send error: {e}", file=sys.stderr)

# --- Opensearch sink ---
class OpensearchSink:
    def __init__(self, endpoint="http://localhost:9200/logs/_doc",
            http_auth: Optional[Tuple] = None,
            verify_certs: bool = False,
            ssl_show_warn: bool = False):
        self.endpoint = endpoint
        self.http_auth = http_auth
        self.verify_certs = verify_certs
        self.ssl_show_warn = ssl_show_warn

    def __call__(self, message, **kwargs):
        try:
            msg = message.strip()
            payload = {
                "requestId": msg[35:71],
                "timestamp": datetime.utcnow().isoformat(),
                "message": msg
            }
            httpx.post(self.endpoint, auth=self.http_auth, json=payload, timeout=60)
        except Exception as e:
            print(f"Opensearch error: {e}", file=sys.stderr)

# --- Syslog sink ---
class SyslogSink:
    def __init__(self, address="/dev/log"):
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self.address = address

    def __call__(self, message):
        try:
            self.sock.sendto(message.encode(), self.address)
        except Exception as e:
            print(f"Syslog error: {e}", file=sys.stderr)

# --- Filter factory ---
def dyna_log_sinks_filter_of(sink_name: str):
    def filter_fn(record):
        try:
            correlation_id_filter(record)
            sinks = request_set_sinks.get()
            level = request_log_level.get()
            return (
                sink_name in sinks
                and logger.level(record["level"].name).no >= logger.level(level).no
            )
        except Exception:
            return True
    return filter_fn


# --- Setup logger once ---
def deep_merge_inplace(dict1, dict2):
    for key, value in dict2.items():
        if (
            key in dict1
            and isinstance(dict1[key], dict)
            and isinstance(value, dict)
        ):
            deep_merge_inplace(dict1[key], value)
        else:
            dict1[key] = value


def setup_dynamic_loggers(options: Optional[Dict]):
    logger.remove()

    deep_merge_inplace(CURRENT_SINKS, AVAILABLE_SINKS)
    deep_merge_inplace(CURRENT_SINKS, options)

    for name, conf in CURRENT_SINKS.items():
        more = dict()

        if not conf.get("enabled", True):
            continue

        if name == "null":
            conf.update(target = lambda _: None)

        elif name == "network":
            if not conf.get("target", None):
                params = conf.get("params", {})
                myargs = dict()

                host = params.get("host", None)
                if host:
                    myargs.update(host=host)

                port = params.get("port", None)
                if port:
                    myargs.update(port=port)

                conf["target"] = NetworkSink(**myargs)

        elif name == "opensearch":
            if not conf.get("target", None):
                params = conf.get("params", {})
                myargs = dict()

                endpoint = params.get("url", None)
                if endpoint:
                    myargs.update(endpoint=endpoint)

                username = params.get("username", None)
                password = params.get("password", None)
                if username and password:
                    myargs.update(http_auth=(username,password))

                conf["target"] = OpensearchSink(**myargs)

        elif name == "syslog":
            if not conf.get("target", None):
                params = conf.get("params", {})
                myargs = dict()

                address = params.get("address", None)
                if address:
                    myargs.update(address=address)

                conf["target"] = SyslogSink(**myargs)

        else:
            more.update({
                k: conf[k] for k in ["colorize", "rotation", "retention", "compression"] if k in conf
            })

        logger.add(
            conf.get("target"),
            level=conf.get("level", "DEBUG"),
            filter=dyna_log_sinks_filter_of(name),
            format=conf.get("format", "{message}"),
            enqueue=conf.get("enqueue", True),
            **more,
        )

# --- Middleware ---
class DynaLogSinksMiddleware(BaseHTTPMiddleware):
    def __init__(self, *args, default_log_level: str = DEFAULT_LOG_LEVEL,
            default_set_sinks: str = "stdout", **kwargs):
        super().__init__(*args, **kwargs)
        self.default_log_level = default_log_level
        self.default_set_sinks = default_set_sinks
        self.default_sinks_set = self._convert_str_to_set(self.default_set_sinks)

    def _convert_str_to_set(self, value):
        return {t.strip() for t in value.split(",")} if isinstance(value, str) else None

    async def dispatch(self, request: Request, call_next):
        level = request.headers.get("X-Log-Level", self.default_log_level).upper()
        try:
            logger.level(level)
            request_log_level.set(level)
        except ValueError:
            logger.warning(f"Invalid log level: {level}, fallback to {self.default_log_level}")
            request_log_level.set(self.default_log_level)

        sinks_header_value = request.headers.get("X-Log-Sinks",
                request.headers.get("X-Log-Targets", self.default_set_sinks))

        if sinks_header_value == self.default_set_sinks:
            request_set_sinks.set(self.default_sinks_set)
        else:
            requested = self._convert_str_to_set(sinks_header_value)
            valid_requested_sinks = requested & AVAILABLE_SINKS.keys()
            if not valid_requested_sinks:
                valid_requested_sinks = self.default_sinks_set
            request_set_sinks.set(valid_requested_sinks)

        response = await call_next(request)
        return response
