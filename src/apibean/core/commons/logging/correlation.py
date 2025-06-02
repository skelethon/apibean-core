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
