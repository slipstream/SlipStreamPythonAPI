import logging

# Mapping between logging levels and CLI verbosity levels.
# Default WARNING
# -v INFO
# -vv DEBUG
# -vvv DEBUG + HTTP request and body

LOG_LEVEL = logging.DEBUG

FORMAT_FIELD_SEP = ' '
FORMAT = '%(asctime)s{0}%(name)s{0}%(levelname)s{0}%(message)s'.format(
    FORMAT_FIELD_SEP)
FORMAT_DATE = '%Y-%m-%dT%H:%M:%SZ'

logging.basicConfig(format=FORMAT, datefmt=FORMAT_DATE, level=LOG_LEVEL)


def get_logger(name=__name__, log_level=LOG_LEVEL):
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    return logger


class Logger(object):
    def __init__(self):
        self.log = get_logger('%s.%s' % (__name__, self.__class__.__name__))
