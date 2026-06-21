"""Scan orchestrator. Pure engine - never imports Qt.

Produces a ScanResult. Always returns a (possibly partial) result on cancel or
partial failure; one failing source never aborts the whole scan.
"""
from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone

from .. import __version__
from ..core.cancel import CancelToken, CancelledError
from ..core.events import NullSink
from ..core.models import (
    ScanResult, ScanMeta, DomainInfo, Asset, ResolveStatus, LiveStatus, ScanMode)
from ..core.normalize import normalize_host, is_valid_domain
from ..sources import registry, rdap
from . import dns_resolver, wildcard, validator, tls, fingerprint, geoip
from . import shadow_it, takeover, posture, scorer


def run(domain_raw: str, mode: str, cfg, token: CancelToken | None = None,
        sink=None, i18n=None) -> ScanResult:
    token = token or CancelToken()
    sink = sink or NullSink()
    i18n = i18n or (lambda k: k)
    full = (mode == ScanMode.FULL.value)

    domain = normalize_host(domain_raw)
    if not is_valid_domain(domain):
        raise ValueError(f"Invalid domain: {domain_raw}")

    started = datetime.now(timezone.utc)
    t0 = time.time()
    result = ScanResult()
    meta = result.scan_meta
    meta.app_version = __version__
    meta.started_at = started.isoformat()
    meta.mode = mode
    meta.locale = getattr(cfg, "language", "id")
    result.domain_info = DomainInfo(domain=domain)

    try:
        # ---- Phase 1: apex intelligence ---------------------------------- #
        sink.on_phase("domain_intel")
        sink.on_log("INFO", i18n("log.domain_intel"))
        result.domain_info.dns = dns_resolver.apex_records(domain, cfg)
        result.domain_info.rdap = rdap.lookup(domain, token)
        if full:
            result.domain_info.apex_tls = tls.inspect(domain, cfg)
        token.check()

        # ---- Phase 2: wildcard guard ------------------------------------- #
        sink.on_phase("wildcard")
        wildcard_ips = wildcard.detect(domain, cfg)
        meta.wildcard_detected = bool(wildcard_ips)
        if wildcard_ips:
            sink.on_log("WARN", i18n("log.wildcard"))
        token.check()

        # ---- Phase 3: enumeration ---------------------------------------- #
        sink.on_phase("enumeration")
        provenance: dict[str, set[str]] = {}
        sources = registry.sources_for_mode(full)
        for src in sources:
            token.check()
            sink.on_log("INFO", i18n("log.source").format(name=src.name))
            try:
                sr = src.fetch(domain, token, cfg)
                if sr.ok:
                    meta.sources_used.append(sr.source)
                    for h in sr.hosts:
                        provenance.setdefault(h, set()).add(sr.source)
                else:
                    meta.sources_failed.append(f"{sr.source}: {sr.error}")
                    sink.on_log("WARN", i18n("log.source_fail").format(name=src.name, err=sr.error))
            except CancelledError:
                raise
            except Exception as e:
                meta.sources_failed.append(f"{src.name}: {e}")

        provenance.setdefault(domain, set()).add("RDAP")  # apex always included
        hosts = sorted(provenance.keys())
        max_assets = int(getattr(cfg, "max_assets", 5000))
        if len(hosts) > max_assets:
            sink.on_log("WARN", i18n("log.capped").format(n=max_assets))
            hosts = hosts[:max_assets]
        sink.on_log("INFO", i18n("log.found").format(n=len(hosts)))

        # ---- Phase 4: resolve -------------------------------------------- #
        sink.on_phase("resolve")
        assets: dict[str, Asset] = {h: Asset(hostname=h, sources=sorted(provenance[h]))
                                    for h in hosts}
        _parallel(hosts, lambda h: _resolve_one(assets[h], cfg, wildcard_ips),
                  cfg, token, sink, total=len(hosts))

        # ---- Phase 5: active probe (FULL only) --------------------------- #
        live_hosts = [h for h, a in assets.items()
                      if a.resolve_status == ResolveStatus.RESOLVED.value]
        if full and live_hosts:
            sink.on_phase("probe")
            _parallel(live_hosts, lambda h: _probe_one(assets[h], cfg),
                      cfg, token, sink, total=len(live_hosts))

        # ---- Phase 6: geo ------------------------------------------------ #
        sink.on_phase("geo")
        if geoip.available():
            for a in assets.values():
                for ip in a.ips:
                    a.geo.append(geoip.lookup(ip))

        # ---- Phase 7: analysis ------------------------------------------- #
        sink.on_phase("analysis")
        asset_list = list(assets.values())
        result.assets = asset_list
        findings = []
        findings += posture.analyze(result.domain_info, asset_list, i18n)
        if full:
            findings += shadow_it.analyze(asset_list, i18n)
            findings += takeover.analyze(asset_list, i18n)
        result.findings = findings
        result.risk = scorer.score(findings, getattr(cfg, "risk_weights", {}), i18n)
        for f in findings:  # tally per-asset contribution
            if f.asset_ref in assets:
                assets[f.asset_ref].risk_contrib += 1

    except CancelledError:
        meta.was_cancelled = True
        sink.on_log("WARN", i18n("log.cancelled"))
    finally:
        meta.finished_at = datetime.now(timezone.utc).isoformat()
        meta.duration_s = round(time.time() - t0, 2)
    return result


# --------------------------------------------------------------------------- #
def _parallel(items, fn, cfg, token, sink, total):
    workers = max(4, min(int(getattr(cfg, "concurrency", 40)), 100))
    done = 0
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(fn, it): it for it in items}
        for fut in as_completed(futures):
            done += 1
            sink.on_progress(done, total)
            if token.cancelled:
                for f in futures:
                    f.cancel()
                raise CancelledError()
            try:
                fut.result()
            except CancelledError:
                raise
            except Exception:
                pass


def _resolve_one(asset: Asset, cfg, wildcard_ips: set[str]):
    ips, cname = dns_resolver.resolve_a(asset.hostname, cfg)
    asset.ips = ips
    asset.cname = cname
    if not ips:
        asset.resolve_status = ResolveStatus.UNRESOLVED.value
        return
    # wildcard filter: only-bruteforced host pointing solely to wildcard IPs
    only_brute = set(asset.sources) <= {"BRUTEFORCE"}
    if wildcard_ips and only_brute and set(ips) <= wildcard_ips:
        asset.resolve_status = ResolveStatus.WILDCARD_FILTERED.value
    else:
        asset.resolve_status = ResolveStatus.RESOLVED.value


def _probe_one(asset: Asset, cfg):
    status, info = validator.probe(asset.hostname, cfg)
    asset.live_status = status
    asset.http = info
    if status == LiveStatus.ALIVE.value:
        asset.fingerprint = fingerprint.detect(info)
        asset.tls = tls.inspect(asset.hostname, cfg)
