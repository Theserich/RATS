# Library/timer.py
import logging
from time import time

logger = logging.getLogger("Library.timer")  # Will propagate to root
logger.setLevel(logging.DEBUG)
logger.propagate = True  # ensure it reaches root

def timer(func):
    def wrapper(*args, **kwargs):
        start = time()
        rtrn = func(*args, **kwargs)
        end = time()
        logger.debug("%r took %.3f s" % (func.__name__, end - start))
        return rtrn
    return wrapper