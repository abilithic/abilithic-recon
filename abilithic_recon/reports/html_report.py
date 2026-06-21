"""Self-contained, branded HTML report. All dynamic text is HTML-escaped to
prevent injection from target-controlled strings (titles, headers, CNAMEs).
"""
from __future__ import annotations

from html import escape as E

from ..core.models import ScanResult, LiveStatus, ResolveStatus

_LOGO = (
    '<svg width="40" height="40" viewBox="0 0 256 256" xmlns="http://www.w3.org/2000/svg">'
    '<rect x="66" y="210" width="124" height="8" rx="4" fill="#2FE3C2"/>'
    '<polygon points="128,42 46,204 210,204" fill="#33425A" stroke="#33425A" stroke-width="14" stroke-linejoin="round"/>'
    '<polygon points="128,42 210,204 128,204" fill="#000" fill-opacity="0.18"/>'
    '<circle cx="128" cy="117" r="19" fill="#2FE3C2"/>'
    '<path d="M121 130 H135 L141 166 a3 3 0 0 1 -3 4 H116 a3 3 0 0 1 -3 -4 Z" fill="#2FE3C2"/>'
    "</svg>"
)

_SEV_COLOR = {"CRITICAL": "#ff5c7a", "HIGH": "#ff9f43", "MEDIUM": "#ffd166",
              "LOW": "#62d5b8", "INFO": "#8c97a8"}
_GRADE_COLOR = {"CRITICAL": "#ff5c7a", "HIGH": "#ff9f43", "MEDIUM": "#ffd166",
                "LOW": "#62d5b8", "INFO": "#48f3d2"}


def save_html(result: ScanResult, path: str, t) -> str:
    html = _render(result, t)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(html)
    return path


def _render(r: ScanResult, t) -> str:
    m = r.scan_meta
    di = r.domain_info
    alive = sum(1 for a in r.assets if a.live_status == LiveStatus.ALIVE.value)
    high = sum(1 for f in r.findings if f.severity in ("HIGH", "CRITICAL"))
    shadow = sum(1 for f in r.findings if f.type in ("SHADOW_IT", "TAKEOVER"))
    grade_c = _GRADE_COLOR.get(r.risk.grade, "#48f3d2")

    rows = []
    for a in sorted(r.assets, key=lambda x: (-x.risk_contrib, x.hostname)):
        geo = "; ".join(f"{g.country}" for g in a.geo if g.country)
        tls_days = a.tls.days_left if (a.tls and a.tls.days_left is not None) else "-"
        live_c = "#48f3d2" if a.live_status == "ALIVE" else "#8c97a8"
        rows.append(
            f"<tr><td>{E(a.hostname)}</td><td>{E(a.resolve_status)}</td>"
            f"<td style='color:{live_c}'>{E(a.live_status)}</td>"
            f"<td>{E('; '.join(a.ips))}</td><td>{E(geo)}</td>"
            f"<td>{E('; '.join(a.fingerprint.tech))}</td><td>{E(str(tls_days))}</td></tr>"
        )
    table = "\n".join(rows) or "<tr><td colspan='7'>-</td></tr>"

    finds = []
    for f in sorted(r.findings, key=lambda x: -_rank(x.severity)):
        c = _SEV_COLOR.get(f.severity, "#8c97a8")
        ev = "".join(f"<li>{E(x)}</li>" for x in f.evidence)
        finds.append(
            f"<div class='finding'><span class='sev' style='background:{c}'>{E(f.severity)}</span>"
            f"<b>{E(f.title)}</b> <span class='ref'>{E(f.asset_ref or '')}</span>"
            f"<p>{E(f.detail)}</p>"
            f"{'<ul>'+ev+'</ul>' if ev else ''}"
            f"<p class='rec'>&#9656; {E(f.recommendation)}</p></div>"
        )
    findings_html = "\n".join(finds) or f"<p class='muted'>{E(t('detail.none'))}</p>"

    contribs = "".join(
        f"<tr><td>{E(c.factor)}</td><td>{c.weight}</td><td>{E(c.reason)}</td></tr>"
        for c in r.risk.contributors
    ) or "<tr><td colspan='3'>-</td></tr>"

    dns = di.dns
    meta_rows = [
        ("Mode", m.mode), ("Started", m.started_at), ("Duration (s)", m.duration_s),
        ("Wildcard", "yes" if m.wildcard_detected else "no"),
        ("Sources used", ", ".join(m.sources_used)),
        ("Sources failed", ", ".join(m.sources_failed) or "-"),
        ("Registrar", di.rdap.registrar), ("Created", di.rdap.created),
        ("Expires", di.rdap.expires), ("SPF", dns.SPF or "-"), ("DMARC", dns.DMARC or "-"),
        ("App version", m.app_version), ("Schema", r.schema_version),
    ]
    meta_html = "".join(f"<tr><td>{E(str(k))}</td><td>{E(str(v))}</td></tr>" for k, v in meta_rows)

    return f"""<!doctype html><html lang="{E(m.locale)}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Abilithic Recon - {E(di.domain)}</title>
<style>
:root{{--bg:#0c1118;--card:#161e29;--line:#26303f;--txt:#e7edf5;--mut:#8c97a8;--acc:#48f3d2}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--txt);
font-family:Segoe UI,Roboto,Arial,sans-serif;line-height:1.55}}
.wrap{{max-width:1100px;margin:0 auto;padding:28px}}
header{{display:flex;align-items:center;gap:14px;border-bottom:1px solid var(--line);padding-bottom:18px}}
header h1{{font-size:22px;margin:0}}header .sub{{color:var(--mut);font-size:13px}}
.target{{margin-left:auto;text-align:right}}.target b{{color:var(--acc);font-size:18px}}
.cards{{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin:22px 0}}
.card{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:14px}}
.card .n{{font-size:26px;font-weight:700}}.card .l{{color:var(--mut);font-size:12px}}
.gauge{{font-size:30px;font-weight:800}}
h2{{font-size:16px;border-left:3px solid var(--acc);padding-left:10px;margin:26px 0 12px}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th,td{{text-align:left;padding:8px 10px;border-bottom:1px solid var(--line);vertical-align:top}}
th{{color:var(--mut);font-weight:600}}
.finding{{background:var(--card);border:1px solid var(--line);border-radius:10px;padding:12px;margin-bottom:10px}}
.sev{{color:#0c1118;font-weight:700;font-size:11px;border-radius:6px;padding:2px 8px;margin-right:8px}}
.ref{{color:var(--mut);font-size:12px}}.rec{{color:var(--acc);font-size:13px;margin:6px 0 0}}
.muted{{color:var(--mut)}}.finding ul{{margin:6px 0;color:var(--mut);font-size:12px}}
footer{{color:var(--mut);font-size:12px;margin-top:30px;border-top:1px solid var(--line);padding-top:14px}}
</style></head><body><div class="wrap">
<header>{_LOGO}<div><h1>Abilithic Recon</h1><div class="sub">Attack Surface Intelligence Report</div></div>
<div class="target"><div class="sub">target</div><b>{E(di.domain)}</b></div></header>
<div class="cards">
<div class="card"><div class="n">{len(r.assets)}</div><div class="l">{E(t('card.subdomains'))}</div></div>
<div class="card"><div class="n">{alive}</div><div class="l">{E(t('card.alive'))}</div></div>
<div class="card"><div class="n">{high}</div><div class="l">{E(t('card.highrisk'))}</div></div>
<div class="card"><div class="n">{shadow}</div><div class="l">{E(t('card.shadow'))}</div></div>
<div class="card"><div class="gauge" style="color:{grade_c}">{r.risk.score}</div>
<div class="l">{E(t('card.risk'))} - {E(r.risk.grade)}</div></div>
</div>
<h2>{E(t('col.subdomain'))}</h2>
<table><thead><tr><th>{E(t('col.subdomain'))}</th><th>{E(t('col.resolve'))}</th>
<th>{E(t('col.live'))}</th><th>{E(t('col.ip'))}</th><th>{E(t('col.geo'))}</th>
<th>{E(t('col.tech'))}</th><th>{E(t('col.tls'))}</th></tr></thead><tbody>
{table}</tbody></table>
<h2>{E(t('detail.findings'))}</h2>{findings_html}
<h2>{E(t('card.risk'))}</h2>
<table><thead><tr><th>Factor</th><th>Weight</th><th>Reason</th></tr></thead><tbody>{contribs}</tbody></table>
<h2>Metadata</h2><table><tbody>{meta_html}</tbody></table>
<footer>{E(t('disclaimer.text'))}</footer>
</div></body></html>"""


def _rank(sev: str) -> int:
    return {"INFO": 0, "LOW": 1, "MEDIUM": 2, "HIGH": 3, "CRITICAL": 4}.get(sev, 0)
