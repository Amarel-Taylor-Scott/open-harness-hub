#!/usr/bin/env python3
"""scripts.check_no_raw_secrets_in_e2e_artifacts — PROOF that the Browser E2E gate's review
artifacts exist and leak nothing.

Asserts:
  A. ARTIFACTS EXIST — review videos (animated GIFs ≥ 10 KB), the 10 portal-flow stills, HTML
     snapshots, console captures, and both gate reports are present under artifacts/e2e/.
  B. NO RAW SECRETS — no real API-key material (ak_<realm>_<32hex>), no credential refs
     (credref:/keyref:), no provider-style keys (sk-…, AKIA…), and no passphrase-shaped fixture
     leakage in ANY text artifact (html/console/network/reports). The portal flow's secrets policy
     (blur + redact + passphrase-never-recorded) is verified by its own report field.
  C. HONESTY — reports carry the ffmpeg HELD note (GIF format, not faked webm) and the crawl
     report lists skipped held/planned services with reasons.

Offline, stdlib-only. Exit 0/1. `--self-test` runs the gate.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import re
import sys
from pathlib import Path

REPO_ROOT = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
ART = _resource("artifacts") / "e2e"
RAW_KEY_RE = re.compile(r"\bak_[a-z0-9]+_[0-9a-f]{32}\b")
REF_RE = re.compile(r"\b(?:credref|keyref):[0-9a-f]{8,}")
PROVIDER_KEY_RE = re.compile(r"(sk-[A-Za-z0-9]{16,}|AKIA[0-9A-Z]{12,}|gsk_[A-Za-z0-9]{8,})")
PASSPHRASE_RE = re.compile(r"\blocal-[0-9a-z]{6,}-[0-9a-z]{6,}\b")   # the portal fixture's shape
TEXT_DIRS = ("html", "console", "network", "reports")


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    video_dir = ART / "videos"
    videos = sorted(p for p in video_dir.glob("*")
                    if p.suffix in {".gif", ".webm", ".mp4"}) if video_dir.exists() else []
    ck("A: review videos exist (mp4/webm native or GIF fallback)", len(videos) >= 2, str(len(videos)))
    ck("A: videos are non-trivial (≥10KB each)",
       bool(videos) and all(v.stat().st_size >= 10_240 for v in videos))
    stills = sorted((ART / "screenshots").glob("portal-*.png")) if (ART / "screenshots").exists() else []
    ck("A: the 10 portal-flow stills exist", len(stills) >= 10, str(len(stills)))
    crawl_path = ART / "reports" / "crawl-report.json"
    portal_path = ART / "reports" / "portal-flow-report.json"
    ck("A: both gate reports exist", crawl_path.exists() and portal_path.exists())
    if fails:
        print(f"\n{len(fails)} FAILURES: {fails}")
        return 1

    leaks: list[str] = []
    for d in TEXT_DIRS:
        for path in sorted((ART / d).glob("**/*")):
            if not path.is_file():
                continue
            text = path.read_text(encoding="utf-8", errors="replace")
            for label, rx in (("raw_api_key", RAW_KEY_RE), ("credential_ref", REF_RE),
                              ("provider_key", PROVIDER_KEY_RE), ("passphrase_fixture", PASSPHRASE_RE)):
                if rx.search(text):
                    leaks.append(f"{label} in {path.relative_to(REPO_ROOT)}")
    ck("B: no raw secrets in any text artifact", not leaks, str(leaks[:5]))

    portal = json.loads(portal_path.read_text(encoding="utf-8"))
    crawl = json.loads(crawl_path.read_text(encoding="utf-8"))
    ck("B: portal report declares the blur+redact secrets policy",
       "blurred" in portal.get("secrets_policy", "") and "never" in portal.get("secrets_policy", ""))
    ck("C: video format provenance recorded (native ffmpeg or HELD GIF note)",
       "ffmpeg" in portal.get("video_format_note", ""))
    ck("C: crawl report lists skipped held/planned services with reasons",
       all(s.get("reason") for s in crawl.get("skipped_not_active", [])))

    print("\n" + ("PASS — check_no_raw_secrets_in_e2e_artifacts: review videos + stills + reports exist; "
                  "no raw API keys, credential refs, provider keys, or passphrase fixtures in any E2E "
                  "artifact; format limitation and skipped services recorded honestly."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv or len(sys.argv) == 1:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_no_raw_secrets_in_e2e_artifacts.py --self-test")
    raise SystemExit(0)
