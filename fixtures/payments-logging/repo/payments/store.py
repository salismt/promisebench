"""Append-only JSON-lines store for charge records."""
import json
import os
import threading


class ChargeStore:
    def __init__(self, path):
        self.path = path
        self._lock = threading.Lock()
        parent = os.path.dirname(path)
        if parent:
            os.makedirs(parent, exist_ok=True)

    def save(self, record):
        line = json.dumps(record, sort_keys=True)
        with self._lock, open(self.path, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")

    def all(self):
        if not os.path.exists(self.path):
            return []
        latest = {}
        with open(self.path, encoding="utf-8") as fh:
            for line in fh:
                if line.strip():
                    rec = json.loads(line)
                    latest[rec["charge_id"]] = rec
        return list(latest.values())

    def get(self, charge_id):
        for rec in self.all():
            if rec["charge_id"] == charge_id:
                return rec
        return None

    def update(self, charge_id, **changes):
        rec = self.get(charge_id)
        if rec is None:
            raise KeyError(charge_id)
        rec.update(changes)
        self.save(rec)
        return rec
