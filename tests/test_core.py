"""Pure-logic tests (no network, no Qt). Run: pytest -q"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from abilithic_recon.core.normalize import normalize_host, is_valid_domain, in_scope
from abilithic_recon.core.models import (
    ScanResult, Asset, Finding, FindingType, Severity, ResolveStatus)
from abilithic_recon.engine import scorer, fingerprint, shadow_it
from abilithic_recon.core.models import HttpInfo


def test_normalize_host():
    assert normalize_host("HTTPS://API.Example.com/path?x=1") == "api.example.com"
    assert normalize_host("  api.example.com.  ") == "api.example.com"
    assert normalize_host("*.example.com") == "example.com"
    assert normalize_host("user:pass@web.example.com:8443") == "web.example.com"
    assert normalize_host("") == ""


def test_valid_domain():
    assert is_valid_domain("example.com")
    assert is_valid_domain("sub.example.co.id")
    assert not is_valid_domain("not a domain")
    assert not is_valid_domain("8.8.8.8")
    assert not is_valid_domain("localhost")


def test_in_scope():
    assert in_scope("api.example.com", "example.com")
    assert in_scope("example.com", "example.com")
    assert not in_scope("evil.com", "example.com")
    assert not in_scope("notexample.com", "example.com")


def test_scanresult_roundtrip():
    r = ScanResult()
    r.domain_info.domain = "example.com"
    r.assets.append(Asset(hostname="api.example.com", ips=["1.2.3.4"],
                          resolve_status=ResolveStatus.RESOLVED.value))
    r.findings.append(Finding(id="f1", type=FindingType.SHADOW_IT.value,
                              severity=Severity.HIGH.value, asset_ref="api.example.com",
                              title="t", detail="d", recommendation="r"))
    data = r.to_dict()
    r2 = ScanResult.from_dict(data)
    assert r2.domain_info.domain == "example.com"
    assert r2.assets[0].hostname == "api.example.com"
    assert r2.assets[0].ips == ["1.2.3.4"]
    assert r2.findings[0].severity == "HIGH"


def test_from_dict_ignores_unknown_fields():
    data = {"schema_version": 1, "domain_info": {"domain": "x.com", "future_field": 1},
            "unknown_top": True}
    r = ScanResult.from_dict(data)
    assert r.domain_info.domain == "x.com"


def test_scorer_transparent():
    weights = {"TAKEOVER": 30, "SHADOW_IT": 20}
    finds = [
        Finding(id="a", type="TAKEOVER", severity="CRITICAL", title="takeover"),
        Finding(id="b", type="SHADOW_IT", severity="MEDIUM", title="shadow"),
    ]
    rb = scorer.score(finds, weights)
    assert 0 <= rb.score <= 100
    assert len(rb.contributors) == 2
    assert rb.grade in ("INFO", "LOW", "MEDIUM", "HIGH", "CRITICAL")


def test_fingerprint_rules():
    info = HttpInfo(server="nginx", title="Welcome")
    info._headers = {"X-Powered-By": "Express"}
    info._body = "<html>__NEXT_DATA__ </html>"
    fp = fingerprint.detect(info)
    assert "Nginx" in fp.tech
    assert "Next.js" in fp.tech
    assert "Express/Node.js" in fp.tech
    assert fp.evidence


def test_shadow_it_flags_dev():
    a = Asset(hostname="dev.example.com", live_status="ALIVE")
    finds = shadow_it.analyze([a], lambda k: k)
    assert any(f.type == "SHADOW_IT" for f in finds)
    assert a.findings_ref
