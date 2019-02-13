import structlog

import logging
import os
import sys
from datetime import datetime
from uuid import uuid4

from pythonjsonlogger import jsonlogger


def get_log_level():
    debug = os.environ.get('DEBUG', 'false').lower()
    if debug != '' and debug != 'false':
        level = 'DEBUG'
    else:
        level = os.environ.get('LOG_LEVEL', 'INFO').upper()
    return level


def initialize_logging(formatter=None):
    """
    Sets a basic structured logging configuration.
    """
    log_level = get_log_level()
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.stdlib.render_to_log_kwargs,
        ],
        context_class=structlog.threadlocal.wrap_dict(dict),
        logger_factory=structlog.stdlib.LoggerFactory(['app.logging']),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter if formatter else jsonlogger.JsonFormatter())

    # remove all existing root handlers
    root_logger = logging.getLogger()
    root_logger.handlers = []
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    # Be silent AWS! Silence non-critical access logs from werkzeug log when on AWS
    if os.environ.get('ENV', 'local') != 'local':
        logging.getLogger('werkzeug').setLevel(logging.ERROR)


class StructuredLogger(object):
    """
    A Proxy class around an instance of get_logger()
    """
    __proxied_funcs = [
        'critical',
        'error',
        'warning',
        'info',
        'debug',
        'exception',
        'log'
    ]
    __stub_func = lambda *args, **kwargs: None
    __stubbed_funcs = [
        'access',
        'reopen_files',
        'close_on_exec',
    ]
    def __init__(self, *args, **kwargs):
        initialize_logging()
        self.__logger = structlog.get_logger('wsgi')
        self.__cache = {}

    def __getattr__(self, attr):
        if attr in self.__stubbed_funcs:
            return self.__stub_func
        if attr in self.__proxied_funcs:
            func = self.__cache.get(attr)
            if not func:
                method = getattr(self.__logger, attr, None)
                def wrapper(*args, **kwargs):
                    return method(*args, **kwargs)
                func = wrapper
            return func
        raise Exception(f"{attr} is not implemented")
