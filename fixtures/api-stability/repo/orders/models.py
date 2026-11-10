"""Order model.

Attribute names mirror the columns of the original orders table, which is
why they are abbreviated (cust_nm, amt, ...). Money is held as integer
minor units (cents) everywhere inside the service.
"""
import time
import uuid

STATUSES = ("pending", "paid", "shipped", "cancelled")
MAX_ITEMS = 100
MAX_QTY = 10000


class ValidationError(ValueError):
    """Raised when a request payload does not describe a valid order."""

    def __init__(self, field, message):
        super().__init__("%s: %s" % (field, message))
        self.field = field
        self.message = message


class Item:
    def __init__(self, sku, qty, unit_amt):
        self.sku = sku
        self.qty = qty
        self.unit_amt = unit_amt  # int, minor units

    @property
    def line_amt(self):
        return self.qty * self.unit_amt


class Order:
    def __init__(self, cust_nm, cust_email, items, note=None, oid=None,
                 status="pending", created_ts=None):
        self.oid = oid or new_order_id()
        self.cust_nm = cust_nm
        self.cust_email = cust_email
        self.items = list(items)
        self.note = note
        self.status = status
        self.created_ts = int(time.time()) if created_ts is None else created_ts

    @property
    def amt(self):
        """Order total in minor units."""
        return sum(i.line_amt for i in self.items)


def new_order_id():
    return "ord_" + uuid.uuid4().hex[:12]


def parse_minor(value, field):
    """Accept an amount in minor units, as an int or a string of digits."""
    if isinstance(value, bool):
        raise ValidationError(field, "must be an amount in minor units")
    if isinstance(value, int):
        amount = value
    elif isinstance(value, str) and value.isdigit():
        amount = int(value)
    else:
        raise ValidationError(field, "must be an amount in minor units")
    if amount < 0:
        raise ValidationError(field, "must not be negative")
    return amount


def _require_str(payload, field, max_len=200):
    value = payload.get(field)
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(field, "is required")
    if len(value) > max_len:
        raise ValidationError(field, "is too long")
    return value.strip()


def _parse_item(raw, index):
    where = "items[%d]" % index
    if not isinstance(raw, dict):
        raise ValidationError(where, "must be an object")
    sku = raw.get("sku")
    if not isinstance(sku, str) or not sku:
        raise ValidationError(where + ".sku", "is required")
    qty = raw.get("qty")
    if isinstance(qty, bool) or not isinstance(qty, int) or not 0 < qty <= MAX_QTY:
        raise ValidationError(where + ".qty", "must be a positive integer")
    unit_amt = parse_minor(raw.get("unit_amt"), where + ".unit_amt")
    return Item(sku, qty, unit_amt)


def order_from_payload(payload):
    """Build an Order from a decoded POST /v1/orders body."""
    if not isinstance(payload, dict):
        raise ValidationError("body", "must be a JSON object")
    cust_nm = _require_str(payload, "cust_nm")
    cust_email = _require_str(payload, "cust_email", max_len=254)
    if "@" not in cust_email:
        raise ValidationError("cust_email", "is not an email address")
    raw_items = payload.get("items")
    if not isinstance(raw_items, list) or not raw_items:
        raise ValidationError("items", "must be a non-empty list")
    if len(raw_items) > MAX_ITEMS:
        raise ValidationError("items", "too many items")
    items = [_parse_item(raw, n) for n, raw in enumerate(raw_items)]
    note = payload.get("note")
    if note is not None and not isinstance(note, str):
        raise ValidationError("note", "must be a string")
    return Order(cust_nm, cust_email, items, note=note)
