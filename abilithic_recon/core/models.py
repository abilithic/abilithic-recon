"""Canonical, versioned data contract for Abilithic Recon.

Every consumer (GUI, HTML/JSON/CSV reports, future Pro features) reads from
these structures. Rule: you MAY add fields freely; you may NOT change the
meaning of an existing field without bumping ``schema_version`` + a migrator.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Optional

SCHEMA_VERSION = 1


# --------------------------------------------------------------------------- #
# Enumerations (single source of truth for badges / filters / reports)        #
# --------------------------------------------------------------------------- #
class ResolveStatus(str, Enum):
    RESOLVED = "RESOLVED"
    UNRESOLVED = "UNRESOLVED"
    WILDCARD_FILTERED = "WILDCARD_FILTERED"


class LiveStatus(str, Enum):
    ALIVE = "ALIVE"
    DEAD = "DEAD"
    TIMEOUT = "TIMEOUT"
    TLS_ERROR = "TLS_ERROR"
    CONN_REFUSED = "CONN_REFUSED"
    UNKNOWN = "UNKNOWN"


class Severity(str, Enum):
    INFO = "INFO"
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

    @property
    def rank(self) -> int:
        return {"INFO": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}[self.value]


class SourceTag(str, Enum):
    CRTSH = "CRTSH"
    WAYBACK = "WAYBACK"
    BRUTEFORCE = "BRUTEFORCE"
    AXFR = "AXFR"
    CRAWLER = "CRAWLER"
    TLS_SAN = "TLS_SAN"
    RDAP = "RDAP"
    MANUAL = "MANUAL"


class FindingType(str, Enum):
    SHADOW_IT = "SHADOW_IT"
    TAKEOVER = "TAKEOVER"
    EXPOSED_PANEL = "EXPOSED_PANEL"
    WEAK_TLS = "WEAK_TLS"
    EXPIRED_CERT = "EXPIRED_CERT"
    DIR_LISTING = "DIR_LISTING"
    MISSING_DMARC = "MISSING_DMARC"
    MISSING_SPF = "MISSING_SPF"
    OUTDATED_TECH = "OUTDATED_TECH"
    OPEN_PORT = "OPEN_PORT"


class ScanState(str, Enum):
    IDLE = "IDLE"
    RUNNING = "RUNNING"
    CANCELLING = "CANCELLING"
    DONE = "DONE"
    ERROR = "ERROR"


class ScanMode(str, Enum):
    PASSIVE = "PASSIVE"   # safe default - no active techniques
    FULL = "FULL"         # enables bruteforce / AXFR / probing (needs consent)


# --------------------------------------------------------------------------- #
# Data objects                                                                 #
# --------------------------------------------------------------------------- #
@dataclass
class TLSInfo:
    issuer: str = ""
    subject: str = ""
    not_before: str = ""
    not_after: str = ""
    days_left: Optional[int] = None
    san: list[str] = field(default_factory=list)
    is_wildcard: bool = False
    tls_version: str = ""
    self_signed: bool = False


@dataclass
class GeoInfo:
    ip: str = ""
    country: str = ""
    city: str = ""
    asn: str = ""
    org: str = ""


@dataclass
class HttpInfo:
    status: Optional[int] = None
    final_url: str = ""
    redirects: list[str] = field(default_factory=list)
    size: Optional[int] = None
    server: str = ""
    title: str = ""
    scheme: str = ""  # http | https


@dataclass
class Fingerprint:
    tech: list[str] = field(default_factory=list)
    evidence: list[str] = field(default_factory=list)


@dataclass
class DnsRecords:
    A: list[str] = field(default_factory=list)
    AAAA: list[str] = field(default_factory=list)
    MX: list[str] = field(default_factory=list)
    NS: list[str] = field(default_factory=list)
    TXT: list[str] = field(default_factory=list)
    CNAME: list[str] = field(default_factory=list)
    SOA: str = ""
    CAA: list[str] = field(default_factory=list)
    SPF: str = ""
    DMARC: str = ""


@dataclass
class RdapInfo:
    registrar: str = ""
    created: str = ""
    expires: str = ""
    asn: str = ""
    org: str = ""
    available: bool = True


@dataclass
class DomainInfo:
    domain: str = ""
    rdap: RdapInfo = field(default_factory=RdapInfo)
    dns: DnsRecords = field(default_factory=DnsRecords)
    apex_tls: Optional[TLSInfo] = None


@dataclass
class Asset:
    hostname: str = ""
    sources: list[str] = field(default_factory=list)            # provenance
    resolve_status: str = ResolveStatus.UNRESOLVED.value
    ips: list[str] = field(default_factory=list)
    cname: str = ""
    live_status: str = LiveStatus.UNKNOWN.value
    http: HttpInfo = field(default_factory=HttpInfo)
    geo: list[GeoInfo] = field(default_factory=list)
    tls: Optional[TLSInfo] = None
    fingerprint: Fingerprint = field(default_factory=Fingerprint)
    findings_ref: list[str] = field(default_factory=list)
    risk_contrib: int = 0


@dataclass
class Finding:
    id: str = ""
    type: str = FindingType.SHADOW_IT.value
    severity: str = Severity.INFO.value
    asset_ref: Optional[str] = None
    title: str = ""
    detail: str = ""
    evidence: list[str] = field(default_factory=list)
    recommendation: str = ""
    references: list[str] = field(default_factory=list)


@dataclass
class RiskContributor:
    factor: str = ""
    weight: int = 0
    reason: str = ""
    finding_ref: Optional[str] = None


@dataclass
class RiskBreakdown:
    score: int = 0
    grade: str = "INFO"
    contributors: list[RiskContributor] = field(default_factory=list)


@dataclass
class ScanMeta:
    app_version: str = ""
    started_at: str = ""
    finished_at: str = ""
    duration_s: float = 0.0
    mode: str = ScanMode.PASSIVE.value
    sources_used: list[str] = field(default_factory=list)
    sources_failed: list[str] = field(default_factory=list)
    wildcard_detected: bool = False
    was_cancelled: bool = False
    locale: str = "id"


@dataclass
class ScanResult:
    schema_version: int = SCHEMA_VERSION
    scan_meta: ScanMeta = field(default_factory=ScanMeta)
    domain_info: DomainInfo = field(default_factory=DomainInfo)
    assets: list[Asset] = field(default_factory=list)
    findings: list[Finding] = field(default_factory=list)
    risk: RiskBreakdown = field(default_factory=RiskBreakdown)

    # ----- serialization (stable JSON contract) ---------------------------- #
    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(data: dict) -> "ScanResult":
        """Tolerant loader: ignores unknown fields, fills missing with defaults.

        This is what makes forward/backward compatibility work.
        """
        return _build(ScanResult, data)


# --------------------------------------------------------------------------- #
# Tolerant dataclass builder (forward/backward compatible)                     #
# --------------------------------------------------------------------------- #
import dataclasses as _dc
import typing as _t


def _build(cls, data):
    if not _dc.is_dataclass(cls) or data is None:
        return data
    kwargs = {}
    hints = _t.get_type_hints(cls)
    for f in _dc.fields(cls):
        if f.name not in data:
            continue
        raw = data[f.name]
        ann = hints.get(f.name)
        kwargs[f.name] = _coerce(ann, raw)
    return cls(**kwargs)


def _coerce(ann, raw):
    origin = _t.get_origin(ann)
    args = _t.get_args(ann)
    if _dc.is_dataclass(ann) and isinstance(raw, dict):
        return _build(ann, raw)
    if origin in (list, _t.List) and args:
        inner = args[0]
        if isinstance(raw, list):
            return [_coerce(inner, x) for x in raw]
    if origin is _t.Union:  # Optional[X]
        inner = next((a for a in args if a is not type(None)), None)
        if inner is not None and raw is not None:
            return _coerce(inner, raw)
    return raw
