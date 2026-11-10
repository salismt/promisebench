"""Config loading.

Sources, later wins:
  1. $XDG_CONFIG_HOME/tidymd/config.ini (default ~/.config/tidymd/config.ini)
  2. .tidymd.ini in the current directory or the nearest parent
  3. the file given with --config
"""
import configparser
import os
from dataclasses import dataclass, field
from typing import List

PROJECT_FILE = ".tidymd.ini"


@dataclass
class Config:
    line_length: int = 100
    telemetry: bool = True
    export_css: str = ""
    sources: List[str] = field(default_factory=list)


def user_config_dir(environ=None):
    environ = os.environ if environ is None else environ
    base = environ.get("XDG_CONFIG_HOME") or os.path.join(os.path.expanduser("~"), ".config")
    return os.path.join(base, "tidymd")


def find_project_file(start):
    cur = os.path.abspath(start)
    while True:
        candidate = os.path.join(cur, PROJECT_FILE)
        if os.path.isfile(candidate):
            return candidate
        parent = os.path.dirname(cur)
        if parent == cur:
            return None
        cur = parent


def load_config(explicit=None, cwd=None, environ=None):
    paths = [os.path.join(user_config_dir(environ), "config.ini")]
    project = find_project_file(cwd or os.getcwd())
    if project:
        paths.append(project)
    if explicit:
        if not os.path.isfile(explicit):
            raise FileNotFoundError("config file not found: %s" % explicit)
        paths.append(explicit)

    parser = configparser.ConfigParser()
    read = parser.read(paths, encoding="utf-8")
    cfg = Config(sources=list(read))
    if parser.has_section("tidymd"):
        cfg.line_length = parser.getint("tidymd", "line_length", fallback=cfg.line_length)
        cfg.export_css = parser.get("tidymd", "export_css", fallback=cfg.export_css)
    if parser.has_section("telemetry"):
        cfg.telemetry = parser.getboolean("telemetry", "enabled", fallback=cfg.telemetry)
    return cfg
