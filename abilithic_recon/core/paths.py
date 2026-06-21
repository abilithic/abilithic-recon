"""Filesystem paths that work both from source and from a PyInstaller .exe.

JEBAKAN PyInstaller: bundled assets live under sys._MEIPASS at runtime. Always
resolve bundled resources through ``resource_path`` - never use bare relative
paths or the .exe will break even though ``python main.py`` works.

Writable data (config, logs, results) goes to %APPDATA% - never next to the
.exe, because Program Files is read-only for normal users.
"""
from __future__ import annotations

import os
import sys


def resource_path(rel: str) -> str:
    """Absolute path to a bundled, read-only resource."""
    base = getattr(sys, "_MEIPASS", None)
    if base is None:
        base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base, rel)


def app_data_dir() -> str:
    """Per-user writable directory for config/logs/results."""
    if sys.platform.startswith("win"):
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config")
    path = os.path.join(base, "AbilithicRecon")
    os.makedirs(path, exist_ok=True)
    return path


def results_dir() -> str:
    path = os.path.join(app_data_dir(), "results")
    os.makedirs(path, exist_ok=True)
    return path


def logs_dir() -> str:
    path = os.path.join(app_data_dir(), "logs")
    os.makedirs(path, exist_ok=True)
    return path


def config_path() -> str:
    return os.path.join(app_data_dir(), "config.json")
