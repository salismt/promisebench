"""Request and result types for the charge API."""
import datetime
from dataclasses import dataclass
from typing import Optional

from . import cards

SUPPORTED_CURRENCIES = ("USD", "EUR", "GBP", "IDR", "SGD")


@dataclass
class ChargeRequest:
    merchant_id: str
    amount: int  # minor units (cents)
    currency: str
    card_number: str
    exp_month: int
    exp_year: int
    cvv: str
    description: str = ""
    idempotency_key: Optional[str] = None

    def validate(self, today=None):
        """Raise ValueError if the request cannot be sent to the gateway."""
        today = today or datetime.date.today()
        if not self.merchant_id:
            raise ValueError("merchant_id is required")
        if not isinstance(self.amount, int) or self.amount <= 0:
            raise ValueError("amount must be a positive integer in minor units")
        if self.currency not in SUPPORTED_CURRENCIES:
            raise ValueError("unsupported currency: %s" % self.currency)
        number = cards.normalize(self.card_number)
        if not cards.luhn_valid(number):
            raise ValueError("card number failed checksum")
        if not (1 <= int(self.exp_month) <= 12):
            raise ValueError("exp_month must be 1-12")
        if (int(self.exp_year), int(self.exp_month)) < (today.year, today.month):
            raise ValueError("card is expired")
        if not (str(self.cvv).isdigit() and len(str(self.cvv)) in (3, 4)):
            raise ValueError("cvv must be 3 or 4 digits")


@dataclass
class ChargeResult:
    charge_id: str
    status: str  # "succeeded" | "failed"
    amount: int
    currency: str
    card_brand: str
    card_last4: str
    gateway_reference: Optional[str] = None
    failure_code: Optional[str] = None

    @property
    def succeeded(self):
        return self.status == "succeeded"
