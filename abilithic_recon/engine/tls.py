"""TLS certificate inspection using only the standard library."""
from __future__ import annotations

import socket
import ssl
from datetime import datetime, timezone

from ..core.models import TLSInfo


def inspect(host: str, cfg, port: int = 443) -> TLSInfo | None:
    timeout = float(getattr(cfg, "http_timeout", 8))
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE  # we inspect even invalid certs
    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname=host) as ssock:
                cert = ssock.getpeercert()
                version = ssock.version() or ""
        return _parse(cert, version)
    except Exception:
        return None


def _parse(cert: dict, version: str) -> TLSInfo:
    info = TLSInfo(tls_version=version)
    if not cert:
        return info
    info.issuer = _name(cert.get("issuer"))
    info.subject = _name(cert.get("subject"))
    info.not_before = cert.get("notBefore", "")
    info.not_after = cert.get("notAfter", "")
    info.self_signed = bool(info.issuer) and info.issuer == info.subject
    san = []
    for typ, val in cert.get("subjectAltName", []):
        if typ == "DNS":
            san.append(val)
            if val.startswith("*."):
                info.is_wildcard = True
    info.san = san
    if info.not_after:
        try:
            exp = datetime.strptime(info.not_after, "%b %d %H:%M:%S %Y %Z").replace(tzinfo=timezone.utc)
            info.days_left = (exp - datetime.now(timezone.utc)).days
        except Exception:
            info.days_left = None
    return info


def _name(seq) -> str:
    if not seq:
        return ""
    parts = []
    for rdn in seq:
        for k, v in rdn:
            if k in ("commonName", "organizationName"):
                parts.append(v)
    return parts[0] if parts else ""
