"""Charge and refund orchestration."""
import logging
import os
import time
import uuid

from . import cards
from .analytics import AnalyticsClient
from .gateway import GatewayClient, GatewayError
from .logconfig import configure_logging
from .models import ChargeResult
from .store import ChargeStore

log = logging.getLogger("payments.service")


def _now():
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _new_charge_id():
    return "ch_" + uuid.uuid4().hex[:20]


class RefundError(Exception):
    pass


class PaymentService:
    def __init__(self, gateway, store, analytics=None):
        self.gateway = gateway
        self.store = store
        self.analytics = analytics

    @classmethod
    def from_env(cls):
        """Build the service the way the API server does, from environment variables."""
        data_dir = os.environ.get("PAYMENTS_DATA_DIR", "data")
        configure_logging(os.environ.get("PAYMENTS_LOG_DIR"), os.environ.get("PAYMENTS_LOG_LEVEL", "INFO"))
        return cls(
            gateway=GatewayClient(),
            store=ChargeStore(os.path.join(data_dir, "charges.jsonl")),
            analytics=AnalyticsClient(),
        )

    def charge(self, request):
        """Authorize and capture a card payment. Returns a ChargeResult.

        Gateway declines and outages are returned as status "failed"; only an
        invalid request raises (ValueError).
        """
        request.validate()
        number = cards.normalize(request.card_number)
        charge_id = _new_charge_id()
        brand = cards.card_brand(number)
        record = {
            "charge_id": charge_id,
            "merchant_id": request.merchant_id,
            "amount": request.amount,
            "currency": request.currency,
            "card_brand": brand,
            "card_last4": cards.last4(number),
            "description": request.description,
            "created_at": _now(),
            "refunded_amount": 0,
        }
        failure_code = None
        reference = None
        try:
            resp = self.gateway.authorize(
                number, request.exp_month, request.exp_year, request.cvv,
                request.amount, request.currency,
            )
        except GatewayError:
            failure_code = "gateway_unavailable"
        else:
            if resp.approved:
                reference = resp.reference
            else:
                failure_code = "card_declined"

        status = "failed" if failure_code else "succeeded"
        record.update(status=status, gateway_reference=reference)
        self.store.save(record)
        log.info("charge %s %s", charge_id, status)

        if status == "succeeded" and self.analytics:
            self.analytics.track(
                "charge_succeeded",
                {"amount": request.amount, "currency": request.currency, "card_brand": brand},
                merchant_id=request.merchant_id,
            )
        return ChargeResult(
            charge_id=charge_id,
            status=status,
            amount=request.amount,
            currency=request.currency,
            card_brand=brand,
            card_last4=record["card_last4"],
            gateway_reference=reference,
            failure_code=failure_code,
        )

    def refund(self, charge_id, amount=None):
        """Refund all or part of a succeeded charge. Returns the updated record."""
        rec = self.store.get(charge_id)
        if rec is None:
            raise RefundError("no such charge: %s" % charge_id)
        if rec["status"] != "succeeded":
            raise RefundError("charge %s is %s, cannot refund" % (charge_id, rec["status"]))
        remaining = rec["amount"] - rec.get("refunded_amount", 0)
        amount = remaining if amount is None else amount
        if amount <= 0 or amount > remaining:
            raise RefundError("refund amount %s exceeds remaining %s" % (amount, remaining))
        try:
            resp = self.gateway.refund(rec["gateway_reference"], amount)
        except GatewayError as exc:
            log.warning("refund for %s failed: %s", charge_id, exc)
            raise RefundError("gateway unavailable, try again later")
        if not resp.approved:
            raise RefundError("refund declined: %s" % resp.code)
        rec = self.store.update(charge_id, refunded_amount=rec.get("refunded_amount", 0) + amount)
        log.info("refund %s amount=%s", charge_id, amount)
        if self.analytics:
            self.analytics.track(
                "charge_refunded",
                {"amount": amount, "currency": rec["currency"]},
                merchant_id=rec["merchant_id"],
            )
        return rec
