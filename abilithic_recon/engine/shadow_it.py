"""Shadow IT heuristics. Pure function over assets -> findings (easy to test)."""
from __future__ import annotations

import re

from ..core.models import Asset, Finding, FindingType, Severity, LiveStatus

RISKY_LABELS = {
    "dev", "test", "testing", "staging", "stage", "uat", "qa", "sandbox",
    "internal", "intranet", "backup", "old", "legacy", "tmp", "temp",
    "vpn", "admin", "adminer", "phpmyadmin", "jenkins", "gitlab", "git",
    "jira", "grafana", "kibana", "dashboard", "portal", "beta", "demo",
}
_PANEL_HINTS = ("login", "admin", "sign in", "dashboard", "phpmyadmin", "grafana")


def analyze(assets: list[Asset], i18n) -> list[Finding]:
    findings: list[Finding] = []
    n = 0
    for a in assets:
        labels = set(re.split(r"[.\-_]", a.hostname.lower()))
        risky = labels & RISKY_LABELS
        alive = a.live_status == LiveStatus.ALIVE.value
        if risky and alive:
            n += 1
            fid = f"shadow-{n}"
            kw = ", ".join(sorted(risky))
            sev = Severity.HIGH if ({"admin", "internal", "backup", "vpn"} & risky) else Severity.MEDIUM
            findings.append(Finding(
                id=fid, type=FindingType.SHADOW_IT.value, severity=sev.value,
                asset_ref=a.hostname,
                title=i18n("finding.shadow.title"),
                detail=i18n("finding.shadow.detail").format(host=a.hostname, kw=kw),
                evidence=[f"hostname label(s): {kw}", f"live: {a.live_status}"],
                recommendation=i18n("finding.shadow.rec"),
            ))
            a.findings_ref.append(fid)
        # exposed panel hint
        title = (a.http.title or "").lower()
        if alive and any(h in title for h in _PANEL_HINTS):
            n += 1
            fid = f"panel-{n}"
            findings.append(Finding(
                id=fid, type=FindingType.EXPOSED_PANEL.value, severity=Severity.HIGH.value,
                asset_ref=a.hostname,
                title=i18n("finding.panel.title"),
                detail=i18n("finding.panel.detail").format(host=a.hostname, title=a.http.title),
                evidence=[f"page title: {a.http.title}"],
                recommendation=i18n("finding.panel.rec"),
            ))
            a.findings_ref.append(fid)
    return findings
