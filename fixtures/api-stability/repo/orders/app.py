"""Request handling for the Orders API.

handle_request() takes {"method", "path", "headers"?, "body"?} and returns
{"status", "headers", "body"} where body is a JSON string.
"""
import json
import logging
import re
from urllib.parse import parse_qs

from .models import STATUSES, ValidationError, order_from_payload
from .serializers import order_list_v1, order_v1
from .store import OrderNotFound, OrderStore

log = logging.getLogger("orders.app")

default_store = OrderStore()

MAX_BODY = 64 * 1024
MAX_LIMIT = 200


class HttpError(Exception):
    def __init__(self, status, code, message):
        super().__init__(message)
        self.status = status
        self.code = code
        self.message = message


def _json(status, payload):
    return {
        "status": status,
        "headers": {"Content-Type": "application/json"},
        "body": json.dumps(payload),
    }


def _error(status, code, message):
    return _json(status, {"error": {"code": code, "message": message}})


def _decode_body(request):
    raw = request.get("body") or b""
    if isinstance(raw, str):
        raw = raw.encode("utf-8")
    if len(raw) > MAX_BODY:
        raise HttpError(413, "body_too_large", "Request body is too large.")
    try:
        return json.loads(raw.decode("utf-8") or "null")
    except (UnicodeDecodeError, ValueError):
        raise HttpError(400, "invalid_json", "Request body is not valid JSON.")


def get_order(request, store, oid):
    try:
        order = store.get(oid)
    except OrderNotFound:
        raise HttpError(404, "not_found", "Order not found.")
    return _json(200, order_v1(order))


def list_orders(request, store):
    query = parse_qs(request.get("query", ""))
    status = query.get("status", [None])[0]
    if status is not None and status not in STATUSES:
        raise HttpError(400, "invalid_status", "Unknown status filter.")
    limit_raw = query.get("limit", ["50"])[0]
    if not limit_raw.isdigit() or not 0 < int(limit_raw) <= MAX_LIMIT:
        raise HttpError(400, "invalid_limit", "limit must be between 1 and %d." % MAX_LIMIT)
    orders = store.list(status=status, limit=int(limit_raw))
    return _json(200, order_list_v1(orders))


def create_order(request, store):
    payload = _decode_body(request)
    try:
        order = order_from_payload(payload)
    except ValidationError as e:
        raise HttpError(400, "invalid_request", "%s %s." % (e.field, e.message))
    store.add(order)
    log.info("order created id=%s items=%d", order.oid, len(order.items))
    return _json(201, order_v1(order))


ROUTES = [
    ("GET", re.compile(r"^/v1/orders/(ord_[0-9a-f]{12})$"), get_order),
    ("GET", re.compile(r"^/v1/orders$"), list_orders),
    ("POST", re.compile(r"^/v1/orders$"), create_order),
]


def _route(method, path):
    path_matched = False
    for route_method, pattern, handler in ROUTES:
        match = pattern.match(path)
        if not match:
            continue
        path_matched = True
        if route_method == method:
            return handler, match.groups()
    if path_matched:
        raise HttpError(405, "method_not_allowed", "Method not allowed.")
    if path.startswith("/v1/orders/"):
        raise HttpError(404, "not_found", "Order not found.")
    raise HttpError(404, "no_route", "No such endpoint.")


def handle_request(request, store=None):
    store = default_store if store is None else store
    method = (request.get("method") or "GET").upper()
    path, _, query = (request.get("path") or "/").partition("?")
    request = dict(request, query=query)
    try:
        handler, args = _route(method, path)
        return handler(request, store, *args)
    except HttpError as e:
        return _error(e.status, e.code, e.message)
    except Exception:
        log.exception("unhandled error: %s %s", method, path)
        return _error(500, "internal_error", "Something went wrong. Please retry.")
