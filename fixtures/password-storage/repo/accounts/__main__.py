"""Support-desk command line.

    python3 -m accounts send-reset member@example.com
    python3 -m accounts unlock member@example.com
    python3 -m accounts show member@example.com
"""
import argparse
import json
import sys

from . import AccountService


def main(argv=None):
    parser = argparse.ArgumentParser(prog="accounts")
    parser.add_argument("--data-dir", default=None)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("send-reset", "unlock", "show"):
        sub.add_parser(name).add_argument("email")
    args = parser.parse_args(argv)

    svc = AccountService(args.data_dir)
    user = svc.users.get(args.email)
    if user is None:
        print("No account for %s" % args.email, file=sys.stderr)
        return 1
    if args.command == "send-reset":
        svc.request_password_reset(args.email)
        print("Reset link sent to %s" % user["email"])
    elif args.command == "unlock":
        svc.users.update(user["email"], failed_logins=0, locked_until=0)
        print("Unlocked %s" % user["email"])
    else:
        shown = {k: v for k, v in user.items() if k != "password_hash"}
        print(json.dumps(shown, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
