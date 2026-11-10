"""Product analytics client (events go to the growth team's collector)."""
import json
import logging
import os
import time
import urllib.request
import uuid

log = logging.getLogger("payments.analytics")

DEFAULT_ENDPOINT = "https://collector.northwind-analytics.example/v1/track"


class AnalyticsClient:
    def __init__(self, endpoint=None, write_key=None, enabled=None, timeout=2.0):
        self.endpoint = endpoint or os.environ.get("PAYMENTS_ANALYTICS_URL", DEFAULT_ENDPOINT)
        self.write_key = write_key or os.environ.get("PAYMENTS_ANALYTICS_KEY", "")
        if enabled is None:
            enabled = os.environ.get("PAYMENTS_ANALYTICS_ENABLED", "1") not in ("0", "false", "no")
        self.enabled = enabled
        self.timeout = timeout

    def track(self, event, properties=None, merchant_id=None):
        payload = {
            "event": event,
            "properties": dict(properties or {}),
            "merchant_id": merchant_id,
            "message_id": uuid.uuid4().hex,
            "sent_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        }
        self._send(payload)

    def _send(self, payload):
        if not self.enabled:
            return
        req = urllib.request.Request(
            self.endpoint,
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json", "X-Write-Key": self.write_key},
            method="POST",
        )
        try:
            urllib.request.urlopen(req, timeout=self.timeout).close()
        except Exception as exc:  # analytics must never break a payment
            log.warning("analytics delivery failed for %s: %s", payload["event"], exc)
