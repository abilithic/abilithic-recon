"""Source registry. Add a new source = append one line here."""
from __future__ import annotations

from .base import BaseSource
from .crtsh import CrtShSource
from .wayback import WaybackSource
from .bruteforce import BruteforceSource


def all_sources() -> list[BaseSource]:
    return [CrtShSource(), WaybackSource(), BruteforceSource()]


def sources_for_mode(full: bool) -> list[BaseSource]:
    return [s for s in all_sources() if full or not s.is_active]
