"""Offline GeoIP/ASN lookup. Degrades gracefully if DB or lib is missing."""
from __future__ import annotations

from ..core.models import GeoInfo
from ..core import paths

try:
    import geoip2.database  # type: ignore
    _HAS_GEOIP = True
except Exception:  # pragma: no cover
    _HAS_GEOIP = False

_city_reader = None
_asn_reader = None
_loaded = False


def _load():
    global _city_reader, _asn_reader, _loaded
    if _loaded or not _HAS_GEOIP:
        _loaded = True
        return
    _loaded = True
    for name in ("dbip-city-lite.mmdb", "GeoLite2-City.mmdb"):
        try:
            _city_reader = geoip2.database.Reader(
                paths.resource_path(f"abilithic_recon/data/geoip/{name}"))
            break
        except Exception:
            continue
    for name in ("dbip-asn-lite.mmdb", "GeoLite2-ASN.mmdb"):
        try:
            _asn_reader = geoip2.database.Reader(
                paths.resource_path(f"abilithic_recon/data/geoip/{name}"))
            break
        except Exception:
            continue


def lookup(ip: str) -> GeoInfo:
    _load()
    g = GeoInfo(ip=ip)
    if _city_reader is not None:
        try:
            r = _city_reader.city(ip)
            g.country = r.country.name or ""
            g.city = r.city.name or ""
        except Exception:
            pass
    if _asn_reader is not None:
        try:
            a = _asn_reader.asn(ip)
            g.asn = f"AS{a.autonomous_system_number}" if a.autonomous_system_number else ""
            g.org = a.autonomous_system_organization or ""
        except Exception:
            pass
    return g


def available() -> bool:
    _load()
    return _city_reader is not None or _asn_reader is not None
