"""Anonymous usage telemetry.

What we send: the command name, exit code, duration, number of files, tidymd
and Python versions, OS name, and a random install id. Nothing else.

Telemetry is off when DO_NOT_TRACK=1 (https://consoledonottrack.com) or when
the config has `[telemetry] enabled = false`.
"""
import json
import os
import platform
import time
import urllib.request
import uuid

from . import __version__
from .config import user_config_dir

ENDPOINT = "https://telemetry.tidymd.dev/v1/events"


def disabled_reason(config, environ=None):
    """Return why telemetry is off ("DO_NOT_TRACK" / "config"), or None if on."""
    environ = os.environ if environ is None else environ
    if environ.get("DO_NOT_TRACK", "").strip().lower() in ("1", "true", "yes"):
        return "DO_NOT_TRACK"
    if not config.telemetry:
        return "config"
    return None


def _install_id(environ):
    path = os.path.join(user_config_dir(environ), "install_id")
    try:
        with open(path, encoding="utf-8") as fh:
            value = fh.read().strip()
            if value:
                return value
    except OSError:
        pass
    value = uuid.uuid4().hex
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(value)
    except OSError:
        pass
    return value


class Telemetry:
    def __init__(self, config, environ=None, endpoint=ENDPOINT, timeout=1.5):
        self.environ = os.environ if environ is None else environ
        self.enabled = disabled_reason(config, self.environ) is None
        self.endpoint = endpoint
        self.timeout = timeout
        self._install = None

    def track(self, event, props=None):
        if not self.enabled:
            return
        if self._install is None:
            self._install = _install_id(self.environ)
        payload = {
            "event": event,
            "props": dict(props or {}),
            "install_id": self._install,
            "version": __version__,
            "python": platform.python_version(),
            "os": platform.system(),
            "ts": int(time.time()),
        }
        self._post(payload)

    def _post(self, payload):
        req = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "User-Agent": "tidymd/" + __version__},
        )
        try:
            urllib.request.urlopen(req, timeout=self.timeout).close()
        except Exception:
            pass  # telemetry must never get in the user's way
