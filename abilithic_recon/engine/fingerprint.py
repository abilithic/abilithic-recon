"""Rule-based technology fingerprinting (no API).

Rules are data-driven: add a tech = append one RULE entry, no code changes.
Each detection carries human-readable evidence so the report is defensible.
"""
from __future__ import annotations

from ..core.models import Fingerprint, HttpInfo

# (tech, where, needle)  where in {"header", "body", "server", "title"}
RULES = [
    ("WordPress", "body", "/wp-content/"),
    ("WordPress", "body", "wp-json"),
    ("Next.js", "body", "__NEXT_DATA__"),
    ("React", "body", "data-reactroot"),
    ("Angular", "body", "ng-version"),
    ("Vue.js", "body", "data-v-"),
    ("Laravel", "header", "laravel_session"),
    ("Laravel", "body", "csrf-token"),
    ("ASP.NET/IIS", "header", "x-aspnet-version"),
    ("ASP.NET/IIS", "server", "iis"),
    ("PHP", "header", "x-powered-by:php"),
    ("Express/Node.js", "header", "x-powered-by:express"),
    ("Nginx", "server", "nginx"),
    ("Apache", "server", "apache"),
    ("Cloudflare", "header", "cf-ray"),
    ("Cloudflare", "server", "cloudflare"),
    ("Drupal", "header", "x-drupal-cache"),
    ("Joomla", "body", "/media/jui/"),
    ("Tomcat", "server", "coyote"),
    ("OpenResty", "server", "openresty"),
    ("Grafana", "title", "grafana"),
    ("Jenkins", "header", "x-jenkins"),
    ("GitLab", "body", "gitlab"),
]


def detect(info: HttpInfo) -> Fingerprint:
    fp = Fingerprint()
    headers = {k.lower(): str(v).lower() for k, v in getattr(info, "_headers", {}).items()}
    header_blob = " ".join(f"{k}:{v}" for k, v in headers.items())
    body = (getattr(info, "_body", "") or "").lower()
    server = (info.server or "").lower()
    title = (info.title or "").lower()

    seen = set()
    for tech, where, needle in RULES:
        hay = {"header": header_blob, "body": body, "server": server, "title": title}[where]
        if needle.lower() in hay:
            if tech not in seen:
                fp.tech.append(tech)
                seen.add(tech)
            fp.evidence.append(f"{tech}: matched '{needle}' in {where}")
    return fp
