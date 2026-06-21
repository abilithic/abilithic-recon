"""Certificate Transparency source via crt.sh JSON endpoint (no API key)."""
from __future__ import annotations

import time

from .base import BaseSource, SourceResult
from .http_client import get_json
from ..core.cancel import CancelToken
from ..core.normalize import normalize_host, in_scope


class CrtShSource(BaseSource):
    name = "crt.sh"
    requires_network = True
    is_active = False  # passive

    URL = "https://crt.sh/?q=%25.{domain}&output=json"

    def fetch(self, domain: str, token: CancelToken, cfg) -> SourceResult:
        res = SourceResult(source="CRTSH")
        last_err = ""
        for attempt in range(3):
            token.check()
            try:
                data = get_json(self.URL.format(domain=domain), timeout=25)
                for row in data:
                    name_value = row.get("name_value", "") or ""
                    for line in name_value.splitlines():
                        host = normalize_host(line)
                        if host and in_scope(host, domain):
                            res.hosts.add(host)
                res.ok = True
                return res
            except Exception as e:  # crt.sh frequently 502s / times out
                last_err = str(e)
                if token.wait(2 * (attempt + 1)):
                    break
        res.ok = False
        res.error = last_err or "crt.sh unavailable"
        return res
