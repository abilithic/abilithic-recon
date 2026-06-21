"""Thin HTTP helper with a graceful fallback if 'requests' is unavailable."""
from __future__ import annotations

USER_AGENT = "AbilithicRecon/1.0 (+https://github.com/abilithic/abilithic-recon)"

try:
    import requests  # type: ignore
    _HAS_REQUESTS = True
except Exception:  # pragma: no cover
    _HAS_REQUESTS = False
    import urllib.request


def get_text(url: str, timeout: int = 20) -> tuple[int, str]:
    """Return (status_code, text). Raises on network error."""
    if _HAS_REQUESTS:
        r = requests.get(url, timeout=timeout, headers={"User-Agent": USER_AGENT})
        return r.status_code, r.text
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=timeout) as resp:  # nosec - read-only OSINT
        return resp.getcode(), resp.read().decode("utf-8", "replace")


def get_json(url: str, timeout: int = 20):
    import json
    status, text = get_text(url, timeout=timeout)
    if status != 200 or not text.strip():
        raise RuntimeError(f"HTTP {status}")
    return json.loads(text)
