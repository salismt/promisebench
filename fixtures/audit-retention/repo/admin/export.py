"""Data export for one user (support sends this when a customer asks for their data)."""
from . import audit


def _actor_names(conn, ids):
    ids = [i for i in ids if i is not None]
    if not ids:
        return {}
    marks = ",".join("?" * len(ids))
    rows = conn.execute("SELECT id, name FROM users WHERE id IN (%s)" % marks, ids)
    return {r["id"]: r["name"] for r in rows}


def export_user(conn, user_id):
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if row is None:
        raise KeyError(user_id)
    history = audit.list_entries(conn, target_id=user_id)
    names = _actor_names(conn, {e["actor_id"] for e in history})
    return {
        "user": {
            "id": row["id"],
            "email": row["email"],
            "name": row["name"],
            "role": row["role"],
            "active": bool(row["active"]),
            "created_at": row["created_at"],
            "deleted_at": row["deleted_at"],
        },
        "history": [
            {
                "ts": e["ts"],
                "action": e["action"],
                "by": names.get(e["actor_id"], "system"),
                "detail": e["detail"],
            }
            for e in reversed(history)
        ],
    }
