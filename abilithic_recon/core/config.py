"""User configuration with versioning + forward-compatible migration."""
from __future__ import annotations

import json
from dataclasses import dataclass, asdict, field

from . import paths

CONFIG_VERSION = 1


@dataclass
class AppConfig:
    config_version: int = CONFIG_VERSION
    language: str = "id"            # id | en
    theme: str = "dark"            # dark | light
    default_mode: str = "PASSIVE"  # PASSIVE | FULL
    concurrency: int = 40
    http_timeout: int = 8
    dns_timeout: int = 4
    max_assets: int = 5000
    output_dir: str = ""
    # risk weights are config-driven so they can be calibrated without a rebuild
    risk_weights: dict = field(default_factory=lambda: {
        "TAKEOVER": 30,
        "EXPOSED_PANEL": 25,
        "SHADOW_IT": 20,
        "WEAK_TLS": 12,
        "EXPIRED_CERT": 12,
        "DIR_LISTING": 15,
        "OUTDATED_TECH": 8,
        "MISSING_DMARC": 5,
        "MISSING_SPF": 5,
        "OPEN_PORT": 10,
    })


def load_config() -> AppConfig:
    p = paths.config_path()
    try:
        with open(p, "r", encoding="utf-8") as fh:
            data = json.load(fh)
        data = _migrate(data)
        cfg = AppConfig()
        for k, v in data.items():
            if hasattr(cfg, k):
                setattr(cfg, k, v)
        return cfg
    except Exception:
        cfg = AppConfig()
        save_config(cfg)
        return cfg


def save_config(cfg: AppConfig) -> None:
    try:
        with open(paths.config_path(), "w", encoding="utf-8") as fh:
            json.dump(asdict(cfg), fh, indent=2)
    except Exception:
        pass


def _migrate(data: dict) -> dict:
    """Bump old config schemas forward. Extend as versions grow."""
    ver = data.get("config_version", 0)
    # if ver < 2: ...transform...; ver = 2
    data["config_version"] = CONFIG_VERSION
    return data
