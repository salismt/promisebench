"""Small JSON-file stores. Good enough for one process; writes are atomic."""
import json
import os
import tempfile
import threading


class JsonFile:
    def __init__(self, path):
        self.path = path
        self._lock = threading.Lock()
        os.makedirs(os.path.dirname(os.path.abspath(path)), exist_ok=True)

    def load(self):
        try:
            with open(self.path, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except FileNotFoundError:
            return {}

    def save(self, data):
        folder = os.path.dirname(os.path.abspath(self.path))
        fd, tmp = tempfile.mkstemp(dir=folder, prefix=".tmp-", suffix=".json")
        with os.fdopen(fd, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=2, sort_keys=True)
        os.replace(tmp, self.path)


def normalize_email(email):
    return (email or "").strip().lower()


class UserStore:
    """Users keyed by normalized email address."""

    def __init__(self, path):
        self._file = JsonFile(path)

    def get(self, email):
        return self._file.load().get(normalize_email(email))

    def put(self, user):
        with self._file._lock:
            data = self._file.load()
            data[normalize_email(user["email"])] = user
            self._file.save(data)

    def update(self, email, **fields):
        with self._file._lock:
            data = self._file.load()
            user = data[normalize_email(email)]
            user.update(fields)
            self._file.save(data)
            return user

    def all(self):
        return list(self._file.load().values())
