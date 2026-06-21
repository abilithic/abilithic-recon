"""Subdomain takeover detection via dangling CNAME + service error fingerprints.

Fingerprint DB is external + versioned (data/takeover-fingerprints.json) so it
can be updated without rebuilding the app. Requires BOTH a CNAME to a known
service AND a matching error pattern to avoid false positives.
"""
from __future__ import annotations

import json

from ..core.models import Asset, Finding, FindingType, Severity, LiveStatus
from ..core import paths

_fps = None


def _load_fingerprints() -> list[dict]:
    global _fps
    if _fps is not None:
        return _fps
    for p in (paths.resource_path("abilithic_recon/data/takeover-fingerprints.json"),
              paths.resource_path("data/takeover-fingerprints.json")):
        try:
            with open(p, "r", encoding="utf-8") as fh:
                _fps = json.load(fh)
                return _fps
        except Exception:
            continue
    _fps = []
    return _fps


def analyze(assets: list[Asset], i18n) -> list[Finding]:
    findings: list[Finding] = []
    fps = _load_fingerprints()
    n = 0
    for a in assets:
        if not a.cname:
            continue
        body = (getattr(a.http, "_body", "") or "").lower()
        cname = a.cname.lower()
        for fp in fps:
            cname_match = any(c in cname for c in fp.get("cname", []))
            sig_match = any(s.lower() in body for s in fp.get("fingerprint", []))
            if cname_match and sig_match:
                n += 1
                fid = f"takeover-{n}"
                findings.append(Finding(
                    id=fid, type=FindingType.TAKEOVER.value, severity=Severity.CRITICAL.value,
                    asset_ref=a.hostname,
                    title=i18n("finding.takeover.title"),
                    detail=i18n("finding.takeover.detail").format(
                        host=a.hostname, service=fp.get("service", "?"), cname=a.cname),
                    evidence=[f"CNAME -> {a.cname}", f"service: {fp.get('service')}"],
                    recommendation=i18n("finding.takeover.rec"),
                    references=fp.get("references", []),
                ))
                a.findings_ref.append(fid)
                break
    return findings
