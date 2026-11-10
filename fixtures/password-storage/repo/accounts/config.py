"""Runtime settings for the account service.

Most values can be overridden with environment variables so that staging and
production can use the same code.
"""
import os

DATA_DIR = os.environ.get("ACCOUNTS_DATA_DIR", "data")

# PBKDF2-HMAC-SHA256 work factor. Raise it over time; old hashes are upgraded
# on the next successful login.
PBKDF2_ITERATIONS = int(os.environ.get("ACCOUNTS_PBKDF2_ITERATIONS", "120000"))
SALT_BYTES = 16

MIN_PASSWORD_LENGTH = 8
MAX_FAILED_LOGINS = 5
LOCKOUT_SECONDS = 15 * 60

RESET_TOKEN_TTL_SECONDS = 30 * 60

SMTP_HOST = os.environ.get("ACCOUNTS_SMTP_HOST", "")
SMTP_PORT = int(os.environ.get("ACCOUNTS_SMTP_PORT", "25"))
MAIL_FROM = "Brightpath Support <support@brightpath.example>"
APP_URL = os.environ.get("ACCOUNTS_APP_URL", "https://members.brightpath.example")
SUPPORT_PHONE = "0800 555 0199"
