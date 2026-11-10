"""Read promises.toml. Uses tomllib on Python 3.11+, else a reader for the subset the fixtures use
([[claim]] tables with string and boolean values)."""
import re
from pathlib import Path

try:
    import tomllib
except ImportError:  # Python 3.9 and 3.10
    tomllib = None


def parse_subset(text):
    claims, cur = [], None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if line == "[[claim]]":
            cur = {}
            claims.append(cur)
            continue
        m = re.match(r'^(\w+)\s*=\s*(.+)$', line)
        if not m or cur is None:
            raise ValueError(f"unsupported TOML line: {raw!r}")
        key, val = m.group(1), m.group(2).strip()
        if val.startswith('"'):
            end = re.match(r'"((?:[^"\\]|\\.)*)"', val)
            cur[key] = end.group(1).replace('\\"', '"').replace("\\\\", "\\")
        elif val.split("#")[0].strip() in ("true", "false"):
            cur[key] = val.split("#")[0].strip() == "true"
        else:
            raise ValueError(f"unsupported TOML value: {raw!r}")
    return {"claim": claims}


def load_promises(path):
    text = Path(path).read_text()
    return tomllib.loads(text) if tomllib else parse_subset(text)
