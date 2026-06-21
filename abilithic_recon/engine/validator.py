"""Active host validation (HTTP/HTTPS probe). Concurrent via thread pool.

Distinguishes resolve (DNS) from alive (HTTP) and records specific live
statuses (TIMEOUT / TLS_ERROR / CONN_REFUSED), not just DEAD.
"""
from __future__ import annotations

import re
import ssl

from ..core.models import HttpInfo, LiveStatus

try:
    import requests  # type: ignore
    _HAS_REQUESTS = True
except Exception:  # pragma: no cover
    _HAS_REQUESTS = False
    import urllib.request
    import urllib.error

USER_AGENT = "AbilithicRecon/1.0 (+https://github.com/abilithic/abilithic-recon)"
_TITLE_RE = re.compile(r"<title[^>]*>(.*?)</title>", re.I | re.S)
_MAX_BYTES = 200_000


def probe(host: str, cfg) -> tuple[str, HttpInfo]:
    timeout = int(getattr(cfg, "http_timeout", 8))
    for scheme in ("https", "http"):
        status, info, fatal = _probe_once(scheme, host, timeout)
        if status == LiveStatus.ALIVE.value:
            return status, info
        if scheme == "https" and status == LiveStatus.TLS_ERROR.value:
            continue  # try http
    return status, info  # last attempt's result


def _probe_once(scheme: str, host: str, timeout: int) -> tuple[str, HttpInfo, bool]:
    url = f"{scheme}://{host}"
    info = HttpInfo(scheme=scheme)
    if _HAS_REQUESTS:
        try:
            r = requests.get(url, timeout=timeout, allow_redirects=True,
                             headers={"User-Agent": USER_AGENT}, stream=True, verify=False)
            body = r.raw.read(_MAX_BYTES, decode_content=True) or b""
            info.status = r.status_code
            info.final_url = r.url
            info.redirects = [h.url for h in r.history]
            info.size = len(body)
            info.server = r.headers.get("Server", "")
            info.title = _title(body)
            info._headers = dict(r.headers)  # type: ignore[attr-defined]
            info._body = body[:50_000].decode("utf-8", "replace")  # type: ignore[attr-defined]
            return LiveStatus.ALIVE.value, info, False
        except requests.exceptions.SSLError:
            return LiveStatus.TLS_ERROR.value, info, False
        except requests.exceptions.ConnectTimeout:
            return LiveStatus.TIMEOUT.value, info, False
        except requests.exceptions.ReadTimeout:
            return LiveStatus.TIMEOUT.value, info, False
        except requests.exceptions.ConnectionError:
            return LiveStatus.CONN_REFUSED.value, info, False
        except Exception:
            return LiveStatus.DEAD.value, info, False
    else:  # stdlib fallback
        try:
            ctx = ssl.create_default_context()
            ctx.check_hostname = False
            ctx.verify_mode = ssl.CERT_NONE
            req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
            with urllib.request.urlopen(req, timeout=timeout, context=ctx) as resp:
                body = resp.read(_MAX_BYTES)
                info.status = resp.getcode()
                info.final_url = resp.geturl()
                info.size = len(body)
                info.server = resp.headers.get("Server", "")
                info.title = _title(body)
                info._headers = dict(resp.headers)  # type: ignore[attr-defined]
                info._body = body[:50_000].decode("utf-8", "replace")  # type: ignore[attr-defined]
            return LiveStatus.ALIVE.value, info, False
        except Exception:
            return LiveStatus.DEAD.value, info, False


def _title(body: bytes) -> str:
    try:
        text = body.decode("utf-8", "replace")
    except Exception:
        return ""
    m = _TITLE_RE.search(text)
    return re.sub(r"\s+", " ", m.group(1)).strip()[:160] if m else ""
