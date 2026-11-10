"""Command line for ops: python3 -m admin.cli --db admin.db --as 1 disable 42"""
import argparse
import json
import os
import sys

from .audit import list_entries
from .db import connect
from .export import export_user
from .service import AdminError, AdminService, ROLES


def build_parser():
    p = argparse.ArgumentParser(prog="admin")
    p.add_argument("--db", default=os.environ.get("ADMIN_DB", "admin.db"))
    p.add_argument("--as", dest="actor", type=int, default=None,
                   help="id of the acting admin (omit for system)")
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("create-user")
    c.add_argument("email")
    c.add_argument("name")
    c.add_argument("--role", choices=ROLES, default="member")

    c = sub.add_parser("update-email")
    c.add_argument("user_id", type=int)
    c.add_argument("email")

    c = sub.add_parser("set-role")
    c.add_argument("user_id", type=int)
    c.add_argument("role", choices=ROLES)

    for name in ("disable", "enable", "reset-password", "delete-user", "export"):
        c = sub.add_parser(name)
        c.add_argument("user_id", type=int)

    c = sub.add_parser("audit")
    c.add_argument("--user", type=int, default=None)
    c.add_argument("--action", default=None)
    return p


def main(argv=None):
    args = build_parser().parse_args(argv)
    conn = connect(args.db)
    svc = AdminService(conn)
    try:
        if args.cmd == "create-user":
            print(svc.create_user(args.actor, args.email, args.name, role=args.role))
        elif args.cmd == "update-email":
            svc.update_email(args.actor, args.user_id, args.email)
        elif args.cmd == "set-role":
            svc.change_role(args.actor, args.user_id, args.role)
        elif args.cmd == "disable":
            svc.disable_user(args.actor, args.user_id)
        elif args.cmd == "enable":
            svc.enable_user(args.actor, args.user_id)
        elif args.cmd == "reset-password":
            svc.reset_password(args.actor, args.user_id)
            print("reset link queued")
        elif args.cmd == "delete-user":
            svc.delete_user(args.actor, args.user_id)
        elif args.cmd == "export":
            print(json.dumps(export_user(conn, args.user_id), indent=2))
        elif args.cmd == "audit":
            for e in list_entries(conn, target_id=args.user, action=args.action):
                print("%s  %-22s actor=%s target=%s %s" % (
                    e["ts"], e["action"], e["actor_id"], e["target_id"], json.dumps(e["detail"])))
    except (AdminError, KeyError) as e:
        print("error: %s" % e, file=sys.stderr)
        return 1
    finally:
        conn.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
