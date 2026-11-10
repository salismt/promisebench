"""Command-line entry point: python3 -m tidymd <command> ..."""
import argparse
import json
import sys
import time

from . import __version__
from .config import load_config
from .export import export_file
from .fmt import format_text
from .lint import lint
from .stats import stats
from .telemetry import Telemetry

# export is new in 0.9 and not wired into telemetry yet
TRACKED_COMMANDS = ("check", "fmt", "stats")


def _read(path):
    with open(path, encoding="utf-8") as fh:
        return fh.read()


def cmd_check(args, config):
    found = 0
    for path in args.paths:
        for issue in lint(_read(path), args.max_line or config.line_length):
            print("%s:%d: %s %s" % (path, issue.line, issue.rule, issue.message))
            found += 1
    return 1 if found else 0


def cmd_fmt(args, config):
    changed = 0
    for path in args.paths:
        text = _read(path)
        new = format_text(text)
        if new != text:
            changed += 1
            if args.check:
                print("would reformat %s" % path)
            else:
                with open(path, "w", encoding="utf-8") as fh:
                    fh.write(new)
                print("reformatted %s" % path)
    return 1 if (args.check and changed) else 0


def cmd_stats(args, config):
    for path in args.paths:
        result = stats(_read(path))
        if args.json:
            print(json.dumps(dict(result, path=path)))
        else:
            print("%s: %d words, %d headings, %d links, ~%d min read" % (
                path, result["words"], result["headings"], result["links"], result["reading_minutes"]))
    return 0


def cmd_export(args, config):
    page = export_file(args.path, output=args.output, title=args.title, css=config.export_css)
    if not args.output:
        sys.stdout.write(page)
    return 0


def build_parser():
    p = argparse.ArgumentParser(prog="tidymd", description="Lint, format and export Markdown.")
    p.add_argument("--version", action="version", version="tidymd " + __version__)
    p.add_argument("--config", help="extra config file (overrides user and project config)")
    sub = p.add_subparsers(dest="command")

    c = sub.add_parser("check", help="report style problems")
    c.add_argument("paths", nargs="+")
    c.add_argument("--max-line", type=int)
    c.set_defaults(func=cmd_check)

    f = sub.add_parser("fmt", help="reformat files in place")
    f.add_argument("paths", nargs="+")
    f.add_argument("--check", action="store_true", help="only report files that would change")
    f.set_defaults(func=cmd_fmt)

    s = sub.add_parser("stats", help="word and structure counts")
    s.add_argument("paths", nargs="+")
    s.add_argument("--json", action="store_true")
    s.set_defaults(func=cmd_stats)

    e = sub.add_parser("export", help="convert a file to standalone HTML")
    e.add_argument("path")
    e.add_argument("-o", "--output", help="write HTML here instead of stdout")
    e.add_argument("--title")
    e.set_defaults(func=cmd_export)
    return p


def main(argv=None):
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.command:
        parser.print_help()
        return 0
    try:
        config = load_config(args.config)
    except (OSError, ValueError) as exc:
        print("tidymd: error: bad config: %s" % exc, file=sys.stderr)
        return 2
    telemetry = Telemetry(config)
    started = time.monotonic()
    code = 1
    try:
        code = args.func(args, config)
    except OSError as exc:
        print("tidymd: error: %s" % exc, file=sys.stderr)
        code = 2
    finally:
        if args.command in TRACKED_COMMANDS:
            telemetry.track("command_run", {
                "command": args.command,
                "exit_code": code,
                "duration_ms": int((time.monotonic() - started) * 1000),
                "files": len(getattr(args, "paths", []) or []),
            })
    return code
