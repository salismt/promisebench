"""Preview/thumbnail step.

We do not ship an image library, so a "thumbnail" is a tiny deterministic
summary of the file bytes (a header plus a short digest). It is enough for the
UI to show a stable placeholder, and it is derived from the file, so it is
customer data and stays in the EU region beside the original.
"""
import hashlib

from . import config


def make_thumbnail(data, edge=None):
    edge = edge or config.THUMBNAIL_EDGE
    digest = hashlib.sha256(data).hexdigest()[:16]
    return ("DOCSTORE-THUMB v1 edge=%d size=%d sig=%s\n" % (edge, len(data), digest)).encode("ascii")


def thumbnail_key(key):
    return key + ".thumb"
