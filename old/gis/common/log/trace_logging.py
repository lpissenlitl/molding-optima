import logging
import threading
import uuid

LOG_THREAD_VALUE = threading.local()


def clear_trace():
    try:
        del LOG_THREAD_VALUE.trace_id
    except AttributeError:
        pass


def get_trace_id():
    try:
        return LOG_THREAD_VALUE.trace_id
    except AttributeError:
        LOG_THREAD_VALUE.trace_id = trace_id = uuid.uuid4().hex
        return trace_id


class TraceFilter(logging.Filter):
    def filter(self, record):
        record.trace_id = get_trace_id()
        return True
