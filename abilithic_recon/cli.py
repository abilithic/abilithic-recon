"""Headless CLI - runs the engine without Qt. Useful for automation & testing."""
from __future__ import annotations

import argparse
import os
import sys

from .core.config import load_config
from .core.events import PrintSink
from .core.models import ScanMode
from .core import paths
from .engine import orchestrator
from .i18n import Translator
from . import reports


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="abilithic-recon",
                                 description="Abilithic Recon - headless scan")
    ap.add_argument("domain")
    ap.add_argument("--mode", choices=["passive", "full"], default="passive")
    ap.add_argument("--lang", choices=["id", "en"], default="en")
    ap.add_argument("--out", help="output directory", default=paths.results_dir())
    ap.add_argument("--format", choices=["json", "csv", "html", "all"], default="all")
    args = ap.parse_args(argv)

    cfg = load_config()
    cfg.language = args.lang
    tr = Translator(args.lang)
    mode = ScanMode.FULL.value if args.mode == "full" else ScanMode.PASSIVE.value

    result = orchestrator.run(args.domain, mode, cfg, sink=PrintSink(), i18n=tr)

    os.makedirs(args.out, exist_ok=True)
    stamp = result.scan_meta.started_at.replace(":", "").replace("-", "")[:15]
    base = os.path.join(args.out, f"abilithic-recon_{result.domain_info.domain}_{stamp}")
    if args.format in ("json", "all"):
        print("saved:", reports.save_json(result, base + ".json"))
    if args.format in ("csv", "all"):
        print("saved:", reports.save_csv(result, base + ".csv"))
    if args.format in ("html", "all"):
        print("saved:", reports.save_html(result, base + ".html", tr))

    print(f"\nScore: {result.risk.score}/100 ({result.risk.grade}) | "
          f"assets={len(result.assets)} findings={len(result.findings)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
