"""Contract every subdomain source implements.

Adding a new source (including a future API-based one) = create one file that
subclasses BaseSource and register it. The orchestrator never changes.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from ..core.cancel import CancelToken


@dataclass
class SourceResult:
    source: str
    hosts: set[str] = field(default_factory=set)
    ok: bool = True
    error: str = ""


class BaseSource:
    name: str = "base"
    requires_network: bool = True
    is_active: bool = False  # True => only runs in FULL mode (needs consent)

    def fetch(self, domain: str, token: CancelToken, cfg) -> SourceResult:
        raise NotImplementedError
