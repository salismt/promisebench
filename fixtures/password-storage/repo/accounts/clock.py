"""One place to read the current time, so tests can control it."""
import time


def now():
    """Seconds since the epoch, as a float."""
    return time.time()
