"""Wayback Machine CDX source - historical hosts (no API key)."""
from __future__ import annotations

from urllib.parse import urlparse

from .base import BaseSource, SourceResult
from .http_client import get_json
from ..core.cancel import CancelToken
from ..core.normalize import normalize_host, in_scope


class WaybackSource(BaseSource):
    name = "wayback"
    requires_network = True
    is_active = False

    URL = ("https://web.archive.org/cdx/search/cdx?url=*.{domain}"
           "&output=json&fl=original&collapse=urlkey&limit=20000")

    def fetch(self, domain: str, token: CancelToken, cfg) -> SourceResult:
        res = SourceResult(source="WAYBACK")
        try:
            data = get_json(self.URL.format(domain=domain), timeout=25)
            for row in data[1:]:  # first row is the header
                token.check()
                url = row[0] if row else ""
                host = normalize_host(urlparse(url if "://" in url else "http://" + url).netloc)
                if host and in_scope(host, domain):
                    res.hosts.add(host)
            res.ok = True
        except Exception as e:
            res.ok = False
            res.error = str(e)
        return res
