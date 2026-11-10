"""Single-use password reset tokens.

Only a SHA-256 digest of each token is stored, so a copy of the token file
cannot be used to reset anyone's password.
"""
import hashlib
import secrets

from . import clock, config
from .store import JsonFile, normalize_email


class InvalidToken(Exception):
    """The reset link is unknown, already used, or expired."""


def _digest(token):
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


class ResetTokenStore:
    def __init__(self, path, ttl_seconds=None):
        self._file = JsonFile(path)
        self.ttl_seconds = ttl_seconds or config.RESET_TOKEN_TTL_SECONDS

    def issue(self, email):
        token = secrets.token_urlsafe(32)
        now = clock.now()
        with self._file._lock:
            data = self._purge(self._file.load(), now)
            data[_digest(token)] = {"email": normalize_email(email), "issued_at": now,
                                    "expires_at": now + self.ttl_seconds}
            self._file.save(data)
        return token

    def consume(self, token):
        """Return the email the token was issued for and invalidate it."""
        now = clock.now()
        with self._file._lock:
            data = self._file.load()
            record = data.pop(_digest(token or ""), None)
            self._file.save(self._purge(data, now))
        if record is None or record["expires_at"] <= now:
            raise InvalidToken("This reset link is invalid or has expired.")
        return record["email"]

    def revoke_all(self, email):
        email = normalize_email(email)
        with self._file._lock:
            data = self._file.load()
            data = {k: v for k, v in data.items() if v["email"] != email}
            self._file.save(data)

    @staticmethod
    def _purge(data, now):
        return {k: v for k, v in data.items() if v["expires_at"] > now}
