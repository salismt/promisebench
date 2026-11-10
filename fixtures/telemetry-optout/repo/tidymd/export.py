"""Markdown to standalone HTML (new in 0.9)."""
import html
import re

INLINE_CODE = re.compile(r"`([^`]+)`")
BOLD = re.compile(r"\*\*([^*]+)\*\*")
LINK = re.compile(r"\[([^\]]+)\]\(([^)]+)\)")

PAGE = """<!doctype html>
<html><head><meta charset="utf-8"><title>{title}</title>{css}</head>
<body>
{body}
</body></html>
"""


def inline(text):
    text = html.escape(text, quote=False)
    text = INLINE_CODE.sub(r"<code>\1</code>", text)
    text = BOLD.sub(r"<strong>\1</strong>", text)
    return LINK.sub(r'<a href="\2">\1</a>', text)


def _cells(line):
    return [c.strip() for c in line.strip().strip("|").split("|")]


def _table(lines):
    header = _cells(lines[0])
    out = ["<table>", "<thead><tr>" + "".join("<th>%s</th>" % inline(h) for h in header) + "</tr></thead>", "<tbody>"]
    for line in lines[2:]:
        row = _cells(line)
        out.append("<tr>" + "".join("<td>%s</td>" % inline(row[i]) for i in range(len(header))) + "</tr>")
    out.append("</tbody></table>")
    return "\n".join(out)


def render(text, title=None, css=""):
    lines = text.split("\n")
    body, para, i = [], [], 0

    def flush():
        if para:
            body.append("<p>%s</p>" % inline(" ".join(para)))
            del para[:]

    while i < len(lines):
        line = lines[i]
        if line.startswith("```"):
            flush()
            j = i + 1
            while j < len(lines) and not lines[j].startswith("```"):
                j += 1
            body.append("<pre><code>%s</code></pre>" % html.escape("\n".join(lines[i + 1:j])))
            i = j + 1
            continue
        m = re.match(r"^(#{1,6})\s+(.*)$", line)
        if m:
            flush()
            level = len(m.group(1))
            body.append("<h%d>%s</h%d>" % (level, inline(m.group(2)), level))
            title = title or m.group(2)
        elif line.startswith("|") and i + 1 < len(lines) and re.match(r"^\|?\s*:?-{3,}", lines[i + 1]):
            flush()
            j = i
            while j < len(lines) and lines[j].startswith("|"):
                j += 1
            body.append(_table(lines[i:j]))
            i = j
            continue
        elif re.match(r"^\s*[-*]\s+", line):
            flush()
            items = []
            while i < len(lines) and re.match(r"^\s*[-*]\s+", lines[i]):
                items.append("<li>%s</li>" % inline(re.sub(r"^\s*[-*]\s+", "", lines[i])))
                i += 1
            body.append("<ul>%s</ul>" % "".join(items))
            continue
        elif not line.strip():
            flush()
        else:
            para.append(line.strip())
        i += 1
    flush()
    style = "<style>%s</style>" % css if css else ""
    return PAGE.format(title=html.escape(title or "Untitled"), css=style, body="\n".join(body))


def export_file(path, output=None, title=None, css=""):
    with open(path, encoding="utf-8") as fh:
        text = fh.read()
    page = render(text, title=title, css=css)
    if output:
        with open(output, "w", encoding="utf-8") as fh:
            fh.write(page)
    return page
