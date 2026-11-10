"""Markdown lint rules."""
import re
from dataclasses import dataclass


@dataclass
class Issue:
    line: int
    rule: str
    message: str


HEADING = re.compile(r"^(#{1,6})(\s*)(.*)$")


def lint(text, line_length=100):
    issues = []
    lines = text.split("\n")
    in_code = False
    blank_run = 0
    for no, line in enumerate(lines, 1):
        if line.startswith("```"):
            in_code = not in_code
        if in_code:
            continue
        if line != line.rstrip():
            issues.append(Issue(no, "MD009", "trailing whitespace"))
        if "\t" in line:
            issues.append(Issue(no, "MD010", "hard tab"))
        if len(line) > line_length and not line.lstrip().startswith(("http://", "https://", "|")):
            issues.append(Issue(no, "MD013", "line is %d chars (max %d)" % (len(line), line_length)))
        m = HEADING.match(line)
        if m and m.group(3) and not m.group(2):
            issues.append(Issue(no, "MD018", "no space after heading marker"))
        if m and no > 1 and lines[no - 2].strip():
            issues.append(Issue(no, "MD022", "heading should be preceded by a blank line"))
        blank_run = blank_run + 1 if not line.strip() else 0
        if blank_run == 2:
            issues.append(Issue(no, "MD012", "multiple consecutive blank lines"))
    if text and not text.endswith("\n"):
        issues.append(Issue(len(lines), "MD047", "file should end with a newline"))
    return issues
