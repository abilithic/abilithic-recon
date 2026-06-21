# Changelog

All notable changes to Abilithic Recon are documented here.
Format based on [Keep a Changelog](https://keepachangelog.com/);
versioning follows [SemVer](https://semver.org/).

## [1.0.0] - 2026-06-21
### Added
- Subdomain enumeration via Certificate Transparency (crt.sh), Wayback Machine,
  and DNS brute force (Full mode).
- Wildcard DNS guard to eliminate brute-force false positives.
- Active host validation (HTTP/HTTPS) with distinct live statuses.
- Apex DNS records (incl. SPF/DMARC), RDAP, and TLS certificate inspection.
- Offline GeoIP/ASN enrichment (DB-IP Lite / GeoLite2, optional).
- Rule-based technology fingerprinting.
- Shadow IT, exposed-panel, and subdomain-takeover detection.
- Transparent, config-driven risk scoring.
- Bilingual UI and reports (Indonesian / English).
- HTML, JSON, and CSV reports; Open/Save structured results.
- PySide6 GUI with dark/light themes, model/view table, and per-menu hints.
- Headless CLI (`python -m abilithic_recon.cli`).
- GitHub Actions workflow that builds the Windows `.exe`.
