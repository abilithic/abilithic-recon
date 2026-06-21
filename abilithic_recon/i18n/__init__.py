"""Tiny translation layer. Stores KEYS in data; resolves to text at display time
so switching language never mutates results.
"""
from __future__ import annotations

import json

from ..core import paths

_DEFAULT = "en"


class Translator:
    def __init__(self, lang: str = "id") -> None:
        self._lang = lang
        self._strings: dict[str, str] = {}
        self._fallback: dict[str, str] = {}
        self._fallback = _load(_DEFAULT)
        self.set_language(lang)

    def set_language(self, lang: str) -> None:
        self._lang = lang
        self._strings = _load(lang)

    @property
    def language(self) -> str:
        return self._lang

    def t(self, key: str) -> str:
        return self._strings.get(key) or self._fallback.get(key) or key

    def __call__(self, key: str) -> str:
        return self.t(key)


def _load(lang: str) -> dict:
    for p in (paths.resource_path(f"abilithic_recon/i18n/locales/{lang}.json"),
              paths.resource_path(f"i18n/locales/{lang}.json")):
        try:
            with open(p, "r", encoding="utf-8") as fh:
                return json.load(fh)
        except Exception:
            continue
    return {}


def available_languages() -> list[str]:
    return ["id", "en"]
