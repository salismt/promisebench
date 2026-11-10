"""HTML for the admin pages. The web shell (not in this repo) serves these strings."""
import html

from . import audit

PAGE = """<!doctype html>
<html><head><title>{title}</title></head>
<body><h1>{title}</h1>
<table>
<tr>{head}</tr>
{rows}
</table></body></html>"""


def _table(title, headers, rows):
    head = "".join("<th>%s</th>" % html.escape(h) for h in headers)
    body = "\n".join(
        "<tr>%s</tr>" % "".join("<td>%s</td>" % html.escape(str(c)) for c in row)
        for row in rows)
    return PAGE.format(title=html.escape(title), head=head, rows=body)


def render_audit_page(conn):
    """Audit tab: every entry, newest first."""
    names = {r["id"]: r["name"] for r in conn.execute("SELECT id, name FROM users")}
    rows = []
    for e in audit.list_entries(conn):
        detail = ", ".join("%s=%s" % kv for kv in sorted(e["detail"].items()))
        rows.append((e["ts"], names.get(e["actor_id"], "system"), e["action"],
                     names.get(e["target_id"], e["target_id"]), detail))
    return _table("Audit log", ["When", "Who", "Action", "User", "Detail"], rows)


def render_users_page(conn):
    rows = conn.execute(
        "SELECT id, email, name, role, active FROM users WHERE deleted_at IS NULL ORDER BY id")
    return _table("Users", ["ID", "Email", "Name", "Role", "Active"],
                  [(r["id"], r["email"], r["name"], r["role"], "yes" if r["active"] else "no")
                   for r in rows])
