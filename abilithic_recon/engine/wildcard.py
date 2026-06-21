"""Wildcard DNS guard - run BEFORE trusting brute-force results.

Without this, a wildcard domain makes every guessed subdomain "resolve",
producing hundreds of false positives and an untrustworthy report.
"""
from __future__ import annotations

import random
import string

from . import dns_resolver


def detect(domain: str, cfg) -> set[str]:
    """Return the set of wildcard IPs (empty if no wildcard)."""
    wildcard_ips: set[str] = set()
    hits = 0
    for _ in range(3):
        label = "".join(random.choices(string.ascii_lowercase + string.digits, k=12))
        ips, _ = dns_resolver.resolve_a(f"{label}.{domain}", cfg)
        if ips:
            hits += 1
            wildcard_ips.update(ips)
    # require at least 2 of 3 random labels to resolve to call it a wildcard
    return wildcard_ips if hits >= 2 else set()
