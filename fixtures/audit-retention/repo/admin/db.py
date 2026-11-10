import sqlite3

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    email       TEXT NOT NULL UNIQUE,
    name        TEXT NOT NULL,
    role        TEXT NOT NULL DEFAULT 'member',
    active      INTEGER NOT NULL DEFAULT 1,
    reset_token TEXT,
    deleted_at  TEXT,
    created_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS audit_log (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    ts        TEXT NOT NULL,
    actor_id  INTEGER,
    action    TEXT NOT NULL,
    target_id INTEGER,
    detail    TEXT NOT NULL DEFAULT '{}'
);
"""


def connect(path):
    """Open the admin database, creating tables on first use."""
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    conn.executescript(SCHEMA)
    return conn
