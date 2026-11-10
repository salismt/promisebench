"""Admin actions. Every method takes the acting admin's user id first.

actor_id None means the system itself (bootstrap, scheduled jobs).
"""
import secrets

from . import audit

ROLES = ("member", "support", "admin")


class AdminError(Exception):
    pass


class PermissionDenied(AdminError):
    pass


class UserNotFound(AdminError):
    pass


class AdminService:
    def __init__(self, conn):
        self.conn = conn

    # -- helpers -------------------------------------------------------
    def _now(self):
        return audit.utcnow().isoformat(timespec="seconds")

    def _require_admin(self, actor_id):
        if actor_id is None:
            return
        row = self.conn.execute(
            "SELECT role, active, deleted_at FROM users WHERE id = ?", (actor_id,)).fetchone()
        if row is None or row["role"] != "admin" or not row["active"] or row["deleted_at"]:
            raise PermissionDenied("user %s is not an active admin" % actor_id)

    def _user(self, user_id):
        row = self.conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
        if row is None or row["deleted_at"]:
            raise UserNotFound(user_id)
        return row

    # -- reads ---------------------------------------------------------
    def get_user(self, user_id):
        return dict(self._user(user_id))

    def list_users(self, include_deleted=False):
        sql = "SELECT * FROM users"
        if not include_deleted:
            sql += " WHERE deleted_at IS NULL"
        return [dict(r) for r in self.conn.execute(sql + " ORDER BY id")]

    # -- actions -------------------------------------------------------
    def create_user(self, actor_id, email, name, role="member"):
        self._require_admin(actor_id)
        if role not in ROLES:
            raise AdminError("unknown role %r" % role)
        email = email.strip().lower()
        if "@" not in email:
            raise AdminError("invalid email")
        with self.conn:
            cur = self.conn.execute(
                "INSERT INTO users (email, name, role, created_at) VALUES (?, ?, ?, ?)",
                (email, name, role, self._now()))
            user_id = cur.lastrowid
            audit.record(self.conn, actor_id, "user.created", user_id, email=email, role=role)
        return user_id

    def update_email(self, actor_id, user_id, new_email):
        self._require_admin(actor_id)
        user = self._user(user_id)
        new_email = new_email.strip().lower()
        if "@" not in new_email:
            raise AdminError("invalid email")
        with self.conn:
            self.conn.execute("UPDATE users SET email = ? WHERE id = ?", (new_email, user_id))
            audit.record(self.conn, actor_id, "user.email_changed", user_id,
                         old=user["email"], new=new_email)

    def change_role(self, actor_id, user_id, role):
        self._require_admin(actor_id)
        if role not in ROLES:
            raise AdminError("unknown role %r" % role)
        user = self._user(user_id)
        with self.conn:
            self.conn.execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
            audit.record(self.conn, actor_id, "user.role_changed", user_id,
                         old=user["role"], new=role)

    def disable_user(self, actor_id, user_id):
        self._require_admin(actor_id)
        self._user(user_id)
        with self.conn:
            self.conn.execute("UPDATE users SET active = 0 WHERE id = ?", (user_id,))
            audit.record(self.conn, actor_id, "user.disabled", user_id)

    def enable_user(self, actor_id, user_id):
        self._require_admin(actor_id)
        self._user(user_id)
        with self.conn:
            self.conn.execute("UPDATE users SET active = 1 WHERE id = ?", (user_id,))
            audit.record(self.conn, actor_id, "user.enabled", user_id)

    def reset_password(self, actor_id, user_id):
        """Issue a one-time reset token; the mailer picks it up from the users table."""
        self._require_admin(actor_id)
        self._user(user_id)
        token = secrets.token_urlsafe(24)
        with self.conn:
            self.conn.execute("UPDATE users SET reset_token = ? WHERE id = ?", (token, user_id))
            audit.record(self.conn, actor_id, "user.password_reset", user_id)
        return token

    def delete_user(self, actor_id, user_id):
        """Soft delete: the row stays so audit entries keep pointing at it."""
        self._require_admin(actor_id)
        self._user(user_id)
        with self.conn:
            self.conn.execute(
                "UPDATE users SET active = 0, reset_token = NULL, deleted_at = ? WHERE id = ?",
                (self._now(), user_id))
            audit.record(self.conn, actor_id, "user.deleted", user_id)
