"""Logging setup shared by the API server and the batch jobs."""
import logging
import os
import sys

LOG_FORMAT = "%(asctime)s %(levelname)s %(name)s %(message)s"


def configure_logging(log_dir=None, level="INFO"):
    """Send the "payments" logger to $log_dir/payments.log, or stderr if unset.

    Safe to call more than once; handlers are only attached the first time
    for a given destination.
    """
    logger = logging.getLogger("payments")
    logger.setLevel(level)
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        target = os.path.abspath(os.path.join(log_dir, "payments.log"))
        for h in logger.handlers:
            if getattr(h, "baseFilename", None) == target:
                return logger
        handler = logging.FileHandler(target, encoding="utf-8")
    else:
        for h in logger.handlers:
            if getattr(h, "_payments_stderr", False):
                return logger
        handler = logging.StreamHandler(sys.stderr)
        handler._payments_stderr = True
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    logger.addHandler(handler)
    return logger
