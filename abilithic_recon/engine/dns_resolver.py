"""DNS resolution. Uses dnspython when available; falls back to stdlib socket
for A/AAAA so the tool still runs (with reduced detail) if dnspython is absent.
"""
from __future__ import annotations

import socket

from ..core.models import DnsRecords

try:
    import dns.resolver  # type: ignore
    import dns.exception  # type: ignore
    _HAS_DNSPYTHON = True
except Exception:  # pragma: no cover
    _HAS_DNSPYTHON = False


def _resolver(cfg):
    r = dns.resolver.Resolver()
    t = float(getattr(cfg, "dns_timeout", 4))
    r.timeout = t
    r.lifetime = t
    return r


def resolve_a(host: str, cfg) -> tuple[list[str], str]:
    """Return (ip_list, cname_target)."""
    ips: list[str] = []
    cname = ""
    if _HAS_DNSPYTHON:
        r = _resolver(cfg)
        try:
            ans = r.resolve(host, "CNAME")
            cname = str(ans[0].target).rstrip(".")
        except Exception:
            pass
        for rtype in ("A", "AAAA"):
            try:
                for rec in r.resolve(host, rtype):
                    ips.append(rec.to_text())
            except Exception:
                pass
    else:
        try:
            for fam, _, _, _, sockaddr in socket.getaddrinfo(host, None):
                ip = sockaddr[0]
                if ip not in ips:
                    ips.append(ip)
        except Exception:
            pass
    return ips, cname


def resolves(host: str, cfg) -> bool:
    ips, _ = resolve_a(host, cfg)
    return bool(ips)


def apex_records(domain: str, cfg) -> DnsRecords:
    rec = DnsRecords()
    a, _ = resolve_a(domain, cfg)
    rec.A = [ip for ip in a if ":" not in ip]
    rec.AAAA = [ip for ip in a if ":" in ip]
    if not _HAS_DNSPYTHON:
        return rec
    r = _resolver(cfg)
    rec.MX = _q(r, domain, "MX")
    rec.NS = _q(r, domain, "NS")
    rec.TXT = _q(r, domain, "TXT")
    rec.CAA = _q(r, domain, "CAA")
    soa = _q(r, domain, "SOA")
    rec.SOA = soa[0] if soa else ""
    # SPF / DMARC parsing from TXT
    for t in rec.TXT:
        tl = t.lower()
        if "v=spf1" in tl:
            rec.SPF = t.strip('"')
    dmarc = _q(r, f"_dmarc.{domain}", "TXT")
    for t in dmarc:
        if "v=dmarc1" in t.lower():
            rec.DMARC = t.strip('"')
    return rec


def get_nameservers(domain: str, cfg) -> list[str]:
    if not _HAS_DNSPYTHON:
        return []
    return [ns.rstrip(".") for ns in _q(_resolver(cfg), domain, "NS")]


def _q(resolver, name: str, rtype: str) -> list[str]:
    try:
        return [r.to_text().strip('"') for r in resolver.resolve(name, rtype)]
    except Exception:
        return []
