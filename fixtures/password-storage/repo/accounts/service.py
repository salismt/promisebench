"""Account service: sign-up, sign-in and password reset for Brightpath members."""
import os

from . import clock, config, emails, hashing
from .mailer import Mailer
from .store import UserStore, normalize_email
from .tokens import InvalidToken, ResetTokenStore


class AccountError(Exception):
    """Base class for errors shown to the member."""


class EmailTaken(AccountError):
    pass


class WeakPassword(AccountError):
    pass


class InvalidCredentials(AccountError):
    pass


class AccountLocked(AccountError):
    pass


PUBLIC_FIELDS = ("email", "name", "created_at", "last_login_at")


def _public(user):
    return {k: user.get(k) for k in PUBLIC_FIELDS}


def check_password_rules(password):
    if not isinstance(password, str) or len(password) < config.MIN_PASSWORD_LENGTH:
        raise WeakPassword("Passwords need at least %d characters." % config.MIN_PASSWORD_LENGTH)
    if password.strip() != password:
        raise WeakPassword("Passwords cannot start or end with a space.")


class AccountService:
    def __init__(self, data_dir=None, mailer=None):
        self.data_dir = data_dir or config.DATA_DIR
        os.makedirs(self.data_dir, exist_ok=True)
        self.users = UserStore(os.path.join(self.data_dir, "users.json"))
        self.tokens = ResetTokenStore(os.path.join(self.data_dir, "reset_tokens.json"))
        self.mailer = mailer or Mailer(os.path.join(self.data_dir, "outbox"))

    # -- sign-up and sign-in ------------------------------------------------

    def signup(self, email, password, name=""):
        email = normalize_email(email)
        if "@" not in email:
            raise AccountError("Please enter a valid email address.")
        if self.users.get(email):
            raise EmailTaken("An account with this email already exists.")
        check_password_rules(password)
        user = {
            "email": email,
            "name": name.strip(),
            "password_hash": hashing.hash_password(password),
            "created_at": clock.now(),
            "last_login_at": None,
            "failed_logins": 0,
            "locked_until": 0,
        }
        self.users.put(user)
        self.mailer.send(email, *emails.welcome(user["name"]))
        return _public(user)

    def login(self, email, password):
        user = self.users.get(email)
        if user is None:
            raise InvalidCredentials("Email or password is incorrect.")
        now = clock.now()
        if user.get("locked_until", 0) > now:
            raise AccountLocked("Too many attempts. Try again later or reset your password.")
        if not hashing.verify_password(password, user["password_hash"]):
            self._record_failure(user, now)
            raise InvalidCredentials("Email or password is incorrect.")
        fields = {"failed_logins": 0, "locked_until": 0, "last_login_at": now}
        if hashing.needs_rehash(user["password_hash"]):
            fields["password_hash"] = hashing.hash_password(password)
        return _public(self.users.update(user["email"], **fields))

    def _record_failure(self, user, now):
        failures = user.get("failed_logins", 0) + 1
        if failures >= config.MAX_FAILED_LOGINS:
            self.users.update(user["email"], failed_logins=0,
                              locked_until=now + config.LOCKOUT_SECONDS)
            self.mailer.send(user["email"], *emails.locked_out(
                user.get("name"), config.LOCKOUT_SECONDS // 60))
        else:
            self.users.update(user["email"], failed_logins=failures)

    # -- password changes ---------------------------------------------------

    def change_password(self, email, current_password, new_password):
        self.login(email, current_password)
        self._set_password(normalize_email(email), new_password)

    def request_password_reset(self, email):
        """Email a single-use reset link. Silent for unknown addresses."""
        user = self.users.get(email)
        if user is None:
            return
        token = self.tokens.issue(user["email"])
        self.mailer.send(user["email"], *emails.reset_link(user.get("name"), token))

    def reset_password(self, token, new_password):
        check_password_rules(new_password)
        email = self.tokens.consume(token)
        if self.users.get(email) is None:
            raise InvalidToken("This reset link is invalid or has expired.")
        self._set_password(email, new_password)

    def _set_password(self, email, new_password):
        check_password_rules(new_password)
        user = self.users.update(email, password_hash=hashing.hash_password(new_password),
                                 failed_logins=0, locked_until=0)
        self.tokens.revoke_all(email)
        self.mailer.send(email, *emails.password_changed(user.get("name")))
