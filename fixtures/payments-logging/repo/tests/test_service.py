import logging
import os
import shutil
import tempfile
import unittest

from payments import ChargeRequest, PaymentService, RefundError
from payments.gateway import GatewayClient
from payments.store import ChargeStore


class FakeAnalytics:
    def __init__(self):
        self.events = []

    def track(self, event, properties=None, merchant_id=None):
        self.events.append((event, dict(properties or {}), merchant_id))


def make_request(**overrides):
    fields = dict(
        merchant_id="m_acme",
        amount=4999,
        currency="USD",
        card_number="4242 4242 4242 4242",
        exp_month=11,
        exp_year=2031,
        cvv="314",
        description="Order 88",
    )
    fields.update(overrides)
    return ChargeRequest(**fields)


class ServiceTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.store = ChargeStore(os.path.join(self.tmp, "charges.jsonl"))
        self.analytics = FakeAnalytics()
        logging.getLogger("payments").addHandler(logging.NullHandler())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def service(self, mode="approve"):
        return PaymentService(GatewayClient(mode=mode), self.store, self.analytics)

    def test_successful_charge_is_stored(self):
        result = self.service().charge(make_request())
        self.assertTrue(result.succeeded)
        self.assertEqual(result.card_last4, "4242")
        self.assertEqual(result.card_brand, "visa")
        rec = self.store.get(result.charge_id)
        self.assertEqual(rec["status"], "succeeded")
        self.assertEqual(rec["amount"], 4999)
        self.assertEqual(self.analytics.events[0][0], "charge_succeeded")

    def test_decline_returns_failed_result(self):
        result = self.service("decline").charge(make_request())
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.failure_code, "card_declined")
        self.assertEqual(self.store.get(result.charge_id)["status"], "failed")

    def test_gateway_outage_returns_failed_result(self):
        result = self.service("error").charge(make_request())
        self.assertEqual(result.status, "failed")
        self.assertEqual(result.failure_code, "gateway_unavailable")

    def test_invalid_request_raises(self):
        with self.assertRaises(ValueError):
            self.service().charge(make_request(card_number="4242424242424241"))
        with self.assertRaises(ValueError):
            self.service().charge(make_request(amount=0))
        with self.assertRaises(ValueError):
            self.service().charge(make_request(cvv="12"))

    def test_full_and_partial_refund(self):
        svc = self.service()
        result = svc.charge(make_request())
        rec = svc.refund(result.charge_id, 1000)
        self.assertEqual(rec["refunded_amount"], 1000)
        rec = svc.refund(result.charge_id)
        self.assertEqual(rec["refunded_amount"], 4999)
        with self.assertRaises(RefundError):
            svc.refund(result.charge_id, 1)

    def test_cannot_refund_failed_charge(self):
        result = self.service("decline").charge(make_request())
        with self.assertRaises(RefundError):
            self.service().refund(result.charge_id)

    def test_from_env(self):
        env = {"PAYMENTS_DATA_DIR": self.tmp, "PAYMENTS_ANALYTICS_ENABLED": "0"}
        old = {k: os.environ.get(k) for k in env}
        os.environ.update(env)
        try:
            svc = PaymentService.from_env()
            self.assertTrue(svc.charge(make_request()).succeeded)
        finally:
            for k, v in old.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v


if __name__ == "__main__":
    unittest.main()
