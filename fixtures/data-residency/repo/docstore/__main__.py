"""Operator command line.

    python3 -m docstore upload <customer> <path>
    python3 -m docstore backup
    python3 -m docstore retention
"""
import argparse
import sys

from . import DocumentService


def main(argv=None):
    parser = argparse.ArgumentParser(prog="docstore")
    parser.add_argument("--root", default=None)
    sub = parser.add_subparsers(dest="command", required=True)
    up = sub.add_parser("upload")
    up.add_argument("customer")
    up.add_argument("path")
    sub.add_parser("backup")
    sub.add_parser("retention")
    args = parser.parse_args(argv)

    svc = DocumentService(args.root)
    if args.command == "upload":
        with open(args.path, "rb") as fh:
            fid = svc.upload(args.customer, args.path, fh.read())
        print("stored %s in %s" % (fid, svc.primary.region))
    elif args.command == "backup":
        print("backed up %d file(s)" % svc.backup_job())
    else:
        print("purged %d file(s)" % svc.retention_job())
    return 0


if __name__ == "__main__":
    sys.exit(main())
