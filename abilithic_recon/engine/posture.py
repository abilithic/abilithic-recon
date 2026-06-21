"""Security-posture findings: weak/expired TLS, missing SPF/DMARC."""
from __future__ import annotations

from ..core.models import (Asset, DomainInfo, Finding, FindingType, Severity, TLSInfo)

_WEAK_TLS = {"TLSv1", "TLSv1.0", "TLSv1.1", "SSLv3"}


def analyze(domain_info: DomainInfo, assets: list[Asset], i18n) -> list[Finding]:
    findings: list[Finding] = []
    n = 0

    def _tls_findings(tls: TLSInfo | None, ref: str):
        nonlocal n
        out = []
        if not tls:
            return out
        if tls.tls_version in _WEAK_TLS:
            n += 1
            out.append(Finding(
                id=f"tls-{n}", type=FindingType.WEAK_TLS.value, severity=Severity.MEDIUM.value,
                asset_ref=ref, title=i18n("finding.weaktls.title"),
                detail=i18n("finding.weaktls.detail").format(host=ref, ver=tls.tls_version),
                evidence=[f"TLS version: {tls.tls_version}"],
                recommendation=i18n("finding.weaktls.rec")))
        if tls.days_left is not None and tls.days_left < 0:
            n += 1
            out.append(Finding(
                id=f"cert-{n}", type=FindingType.EXPIRED_CERT.value, severity=Severity.HIGH.value,
                asset_ref=ref, title=i18n("finding.expcert.title"),
                detail=i18n("finding.expcert.detail").format(host=ref),
                evidence=[f"notAfter: {tls.not_after}"],
                recommendation=i18n("finding.expcert.rec")))
        return out

    findings += _tls_findings(domain_info.apex_tls, domain_info.domain)
    for a in assets:
        for f in _tls_findings(a.tls, a.hostname):
            a.findings_ref.append(f.id)
            findings.append(f)

    dns = domain_info.dns
    if not dns.SPF:
        n += 1
        findings.append(Finding(
            id=f"spf-{n}", type=FindingType.MISSING_SPF.value, severity=Severity.LOW.value,
            asset_ref=domain_info.domain, title=i18n("finding.spf.title"),
            detail=i18n("finding.spf.detail").format(domain=domain_info.domain),
            recommendation=i18n("finding.spf.rec")))
    if not dns.DMARC:
        n += 1
        findings.append(Finding(
            id=f"dmarc-{n}", type=FindingType.MISSING_DMARC.value, severity=Severity.LOW.value,
            asset_ref=domain_info.domain, title=i18n("finding.dmarc.title"),
            detail=i18n("finding.dmarc.detail").format(domain=domain_info.domain),
            recommendation=i18n("finding.dmarc.rec")))
    return findings
