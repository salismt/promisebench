"""Audit log: who did what to which account."""
import json
from datetime import datetime, timezone


def utcnow():
    return datetime.now(timezone.utc)


def record(conn, actor_id, action, target_id=None, **detail):
    """Write one audit entry. Call inside the same transaction as the change."""
    conn.execute(
        "INSERT INTO audit_log (ts, actor_id, action, target_id, detail) VALUES (?, ?, ?, ?, ?)",
        (utcnow().isoformat(timespec="seconds"), actor_id, action, target_id,
         json.dumps(detail, sort_keys=True)),
    )


def entry_from_row(row):
    return {
        "id": row["id"],
        "ts": row["ts"],
        "actor_id": row["actor_id"],
        "action": row["action"],
        "target_id": row["target_id"],
        "detail": json.loads(row["detail"]),
    }


def list_entries(conn, target_id=None, action=None):
    """All matching entries, newest first."""
    sql = "SELECT * FROM audit_log"
    where, args = [], []
    if target_id is not None:
        where.append("target_id = ?")
        args.append(target_id)
    if action is not None:
        where.append("action = ?")
        args.append(action)
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY id DESC"
    return [entry_from_row(r) for r in conn.execute(sql, args)]
