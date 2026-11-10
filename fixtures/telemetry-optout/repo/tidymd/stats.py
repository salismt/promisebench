"""Document statistics."""
import re

WORD = re.compile(r"[A-Za-z0-9']+")
LINK = re.compile(r"\[[^\]]*\]\([^)]+\)")


def stats(text):
    lines = text.split("\n")
    words = len(WORD.findall(text))
    return {
        "lines": len(lines),
        "words": words,
        "headings": sum(1 for l in lines if l.startswith("#")),
        "links": len(LINK.findall(text)),
        "code_blocks": sum(1 for l in lines if l.startswith("```")) // 2,
        "reading_minutes": max(1, round(words / 230)),
    }
