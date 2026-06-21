"""RDAP lookup (modern WHOIS replacement, no API key)."""
from __future__ import annotations

from .http_client import get_json
from ..core.cancel import CancelToken
from ..core.models import RdapInfo


def lookup(domain: str, token: CancelToken) -> RdapInfo:
    info = RdapInfo()
    try:
        data = get_json(f"https://rdap.org/domain/{domain}", timeout=15)
        # registrar
        for ent in data.get("entities", []):
            roles = ent.get("roles", [])
            if "registrar" in roles:
                vcard = ent.get("vcardArray", [])
                info.registrar = _vcard_name(vcard) or ent.get("handle", "")
        # events
        for ev in data.get("events", []):
            action = ev.get("eventAction", "")
            when = ev.get("eventDate", "")
            if action == "registration":
                info.created = when
            elif action == "expiration":
                info.expires = when
        info.available = True
    except Exception:
        info.available = False
    return info


def _vcard_name(vcard) -> str:
    try:
        for item in vcard[1]:
            if item[0] == "fn":
                return item[3]
    except Exception:
        pass
    return ""
