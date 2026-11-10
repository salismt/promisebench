"""Outbound client for optional external integrations (e.g. a virus scanner).

Only small metadata events are sent, and only for features the customer has
turned on. The client is a stub: it records calls and, if a base URL is set,
would POST to it.
"""
import json
import urllib.request

from . import config


class IntegrationsClient:
    def __init__(self, base_url=None):
        self.base_url = base_url if base_url is not None else \
            __import__("os").environ.get("DOCSTORE_INTEGRATIONS_URL", "")
        self.calls = []

    def send_event(self, name, payload):
        """Report a small event (e.g. an antivirus scan request) to an external service."""
        body = json.dumps({"event": name, "data": payload}).encode("utf-8")
        self.calls.append((name, payload))
        if self.base_url:
            req = urllib.request.Request(self.base_url, data=body,
                                         headers={"Content-Type": "application/json"})
            urllib.request.urlopen(req, timeout=10).read()
        return {"ok": True}
