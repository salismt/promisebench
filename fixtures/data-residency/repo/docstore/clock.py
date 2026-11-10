"""Single source of 'now', so the retention job can be tested."""
import time


def now():
    """Seconds since the epoch, as a float."""
    return time.time()
