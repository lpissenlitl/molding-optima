import functools
import logging

import redis
from redis.exceptions import ConnectionError

_LOGGER = logging.getLogger(__name__)

_MAX_TRY_COUNT = 3


def singleton(cls):
    instances = {}

    def _singleton(*args, **kw):
        if cls not in instances:
            instances[cls] = cls(*args, **kw)
        return instances[cls]

    return _singleton


@singleton
class ProxyAgent:
    def __init__(self, host="127.0.0.1", port=6379, db=0):
        self.client = redis.StrictRedis(
            host=host, port=port, db=db, decode_responses=True
        )

    def __wrap(self, method, *args, **kwargs):
        try_count = 0
        while try_count < _MAX_TRY_COUNT:
            try:
                f = getattr(self.client, method)
                return f(*args, **kwargs)
            except Exception as e:
                try_count += 1
                _LOGGER.exception("Redis connection error.%s try(%d)" % (e, try_count))
                if try_count >= _MAX_TRY_COUNT:
                    raise ConnectionError(
                        "Redis connection reached max tries(%d)." % try_count
                    )
                continue

    def __getattr__(self, method):
        return functools.partial(self.__wrap, method)
