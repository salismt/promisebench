"""Password hashing with PBKDF2-HMAC-SHA256 and a per-user random salt.

Encoded format: ``pbkdf2_sha256$<iterations>$<salt hex>$<hash hex>``
"""
import hashlib
import hmac
import os

from . import config

ALGORITHM = "pbkdf2_sha256"


def _derive(password, salt, iterations):
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations)


def hash_password(password, iterations=None):
    iterations = iterations or config.PBKDF2_ITERATIONS
    salt = os.urandom(config.SALT_BYTES)
    digest = _derive(password, salt, iterations)
    return "%s$%d$%s$%s" % (ALGORITHM, iterations, salt.hex(), digest.hex())


def _split(encoded):
    try:
        algorithm, iterations, salt_hex, digest_hex = encoded.split("$")
        return algorithm, int(iterations), bytes.fromhex(salt_hex), digest_hex
    except (AttributeError, ValueError):
        return None


def verify_password(password, encoded):
    parts = _split(encoded)
    if parts is None or parts[0] != ALGORITHM:
        return False
    _, iterations, salt, digest_hex = parts
    candidate = _derive(password, salt, iterations).hex()
    return hmac.compare_digest(candidate, digest_hex)


def needs_rehash(encoded):
    parts = _split(encoded)
    return parts is None or parts[0] != ALGORITHM or parts[1] < config.PBKDF2_ITERATIONS
