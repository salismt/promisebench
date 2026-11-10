"""Safe, idempotent Markdown formatting."""
import re

HEADING = re.compile(r"^(#{1,6})\s*(\S.*)$")


def format_text(text):
    out = []
    in_code = False
    for line in text.split("\n"):
        if line.startswith("```"):
            in_code = not in_code
            out.append(line.rstrip())
            continue
        if in_code:
            out.append(line)
            continue
        line = line.rstrip().replace("\t", "    ")
        m = HEADING.match(line)
        if m:
            if out and out[-1] != "":
                out.append("")
            line = "%s %s" % (m.group(1), m.group(2))
        if line == "" and out and out[-1] == "":
            continue
        out.append(line)
    while out and out[-1] == "":
        out.pop()
    return "\n".join(out) + "\n" if out else ""
