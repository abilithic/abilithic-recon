"""Canonical host normalization & domain validation.

CRITICAL: this is the single canonical implementation used everywhere
(enumeration, dedup, comparison). Using different normalization in different
places lets duplicates ("API.x" vs "api.x." vs "api.x") slip through.
"""
from __future__ import annotations

import re

_LABEL = r"[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?"
_DOMAIN_RE = re.compile(r"^(?:%s\.)+%s$" % (_LABEL, _LABEL))
_IPV4_RE = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$")


def normalize_host(value: str) -> str:
    """Return a canonical hostname or '' if it cannot be normalized."""
    if not value:
        return ""
    h = value.strip().lower()
    # strip scheme
    h = re.sub(r"^[a-z]+://", "", h)
    # strip path / query / fragment
    h = re.split(r"[/?#]", h, 1)[0]
    # strip credentials
    if "@" in h:
        h = h.split("@", 1)[1]
    # strip port
    h = re.sub(r":\d+$", "", h)
    # strip leading wildcard and stray dots
    h = h.lstrip("*.")
    h = h.strip(".")
    if not h:
        return ""
    # IDN -> punycode
    try:
        h = h.encode("idna").decode("ascii")
    except Exception:
        pass
    return h


def is_valid_domain(value: str) -> bool:
    h = normalize_host(value)
    if not h or len(h) > 253:
        return False
    if _IPV4_RE.match(h):
        return False  # raw IP not accepted as a target
    if "." not in h:
        return False
    return bool(_DOMAIN_RE.match(h))


def in_scope(host: str, domain: str) -> bool:
    """True if host == domain or is a subdomain of domain."""
    host = normalize_host(host)
    domain = normalize_host(domain)
    return host == domain or host.endswith("." + domain)
