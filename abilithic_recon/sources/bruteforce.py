"""DNS brute-force source (ACTIVE - only in FULL mode).

Wildcard filtering is applied later by the orchestrator using the Wildcard
Guard result; this source just generates candidates that actually resolve.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed

from .base import BaseSource, SourceResult
from ..core.cancel import CancelToken
from ..core.normalize import normalize_host
from ..core import paths
from ..engine import dns_resolver


def _load_wordlist() -> list[str]:
    candidates = [
        paths.resource_path("abilithic_recon/data/wordlists/subdomains.txt"),
        paths.resource_path("data/wordlists/subdomains.txt"),
    ]
    for c in candidates:
        try:
            with open(c, "r", encoding="utf-8") as fh:
                return [w.strip() for w in fh if w.strip() and not w.startswith("#")]
        except Exception:
            continue
    # minimal built-in fallback so the tool still works if the file is missing
    return ["www", "mail", "api", "dev", "test", "staging", "admin", "vpn",
            "portal", "app", "dashboard", "internal", "git", "ftp", "ns1"]


class BruteforceSource(BaseSource):
    name = "bruteforce"
    requires_network = True
    is_active = True

    def fetch(self, domain: str, token: CancelToken, cfg) -> SourceResult:
        res = SourceResult(source="BRUTEFORCE")
        words = _load_wordlist()
        candidates = [normalize_host(f"{w}.{domain}") for w in words]
        workers = max(4, min(int(getattr(cfg, "concurrency", 40)), 100))
        try:
            with ThreadPoolExecutor(max_workers=workers) as ex:
                futures = {ex.submit(dns_resolver.resolves, host, cfg): host
                           for host in candidates}
                for fut in as_completed(futures):
                    if token.cancelled:
                        break
                    host = futures[fut]
                    try:
                        if fut.result():
                            res.hosts.add(host)
                    except Exception:
                        pass
            res.ok = True
        except Exception as e:
            res.ok = False
            res.error = str(e)
        return res
