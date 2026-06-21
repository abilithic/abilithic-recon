"""CSV export. UTF-8 *with BOM* so Excel (Windows) renders characters correctly."""
from __future__ import annotations

import csv

from ..core.models import ScanResult


def save_csv(result: ScanResult, path: str) -> str:
    with open(path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["Subdomain", "Resolve", "Live", "Status Code", "IPs", "CNAME",
                    "Location", "Server", "Technology", "TLS days", "Title",
                    "Sources", "Risk hits"])
        for a in result.assets:
            geo = "; ".join(f"{g.country}/{g.city}".strip("/") for g in a.geo if g.country or g.city)
            tls_days = a.tls.days_left if (a.tls and a.tls.days_left is not None) else ""
            w.writerow([
                a.hostname, a.resolve_status, a.live_status,
                a.http.status or "", "; ".join(a.ips), a.cname,
                geo, a.http.server, "; ".join(a.fingerprint.tech),
                tls_days, a.http.title, "; ".join(a.sources), a.risk_contrib,
            ])
    return path
