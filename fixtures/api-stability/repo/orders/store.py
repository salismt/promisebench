"""In-process order store.

Production swaps this for the Postgres-backed store with the same methods;
tests and local runs use this one.
"""
import threading


class OrderNotFound(KeyError):
    pass


class OrderStore:
    def __init__(self):
        self._orders = {}
        self._lock = threading.Lock()

    def add(self, order):
        with self._lock:
            self._orders[order.oid] = order
        return order

    def get(self, oid):
        with self._lock:
            try:
                return self._orders[oid]
            except KeyError:
                raise OrderNotFound(oid)

    def list(self, status=None, limit=50):
        with self._lock:
            orders = list(self._orders.values())
        if status is not None:
            orders = [o for o in orders if o.status == status]
        orders.sort(key=lambda o: (o.created_ts, o.oid), reverse=True)
        return orders[:limit]

    def __len__(self):
        return len(self._orders)
