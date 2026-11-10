"""Client for the upstream card processor (Northwind Processing).

In production this talks HTTPS to the processor. In development and tests it
runs in sandbox mode and never leaves the process. The sandbox outcome is
chosen with PAYMENTS_GATEWAY_MODE: approve (default), decline or error.
"""
import os
import uuid

SANDBOX_MODES = ("approve", "decline", "error")


class GatewayError(Exception):
    """The processor could not be reached or sent an unexpected response."""


class GatewayResponse:
    def __init__(self, approved, reference, code, message):
        self.approved = approved
        self.reference = reference
        self.code = code
        self.message = message

    def __repr__(self):
        return "GatewayResponse(approved=%r, code=%r)" % (self.approved, self.code)


class GatewayClient:
    def __init__(self, mode=None, timeout=10.0):
        self.mode = mode or os.environ.get("PAYMENTS_GATEWAY_MODE", "approve")
        if self.mode not in SANDBOX_MODES:
            raise ValueError("unknown gateway mode: %s" % self.mode)
        self.timeout = timeout

    def authorize(self, card_number, exp_month, exp_year, cvv, amount, currency):
        payload = {
            "source": {
                "number": card_number,
                "exp_month": exp_month,
                "exp_year": exp_year,
                "cvc": cvv,
            },
            "amount": amount,
            "currency": currency,
            "capture": True,
        }
        return self._post("/v2/authorizations", payload)

    def refund(self, reference, amount):
        return self._post("/v2/refunds", {"authorization": reference, "amount": amount})

    def _post(self, path, payload):
        # Sandbox transport. The production transport lives in the deploy repo.
        if self.mode == "error":
            raise GatewayError("processor timed out after %.1fs on POST %s" % (self.timeout, path))
        if self.mode == "decline" and path == "/v2/authorizations":
            return GatewayResponse(False, None, "do_not_honor", "The issuer declined the transaction.")
        return GatewayResponse(True, "auth_" + uuid.uuid4().hex[:16], "approved", "Approved")
