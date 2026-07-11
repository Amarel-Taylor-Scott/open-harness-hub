#!/usr/bin/env python3
"""scripts.check_prelaunch — a READ-ONLY private→public readiness gate (reports; never mutates).

Before this repo (or the demo) goes public it must clear a small, mechanical checklist:
  * the bundled demo corpora are SYNTHETIC-ONLY — no real PII slipped in (real-domain emails,
    SSN-shaped strings, credit-card-like digit runs, real API-key shapes);
  * `.env.example` carries placeholders, not real-looking secrets;
  * user-facing demo copy uses the LOCKED brand set and no stray/blocked naming;
  * the internal strategy/codex/research/agent docs that should be de-tracked are LISTED (so a human
    can decide) — this tool never deletes or de-tracks anything.

It scans only what would actually ship with the demo (demo-data/ + the demo web copy), so it is fast
and deterministic. The body is the gate; `--self-test` proves the scanners (incl. a negative case).

CLI:
    python3 _repos/shared-backend-components/scripts/check_prelaunch.py --self-test
    python3 _repos/shared-backend-components/scripts/check_prelaunch.py            # print the readiness report; exit 1 if not ready
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource

#: email domains that are reserved-for-docs / safe (RFC 2606 / 6761). Anything else is "real".
_SAFE_EMAIL = re.compile(r"@[\w.-]*\b(example|test|invalid|localhost)\b", re.IGNORECASE)
_EMAIL = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
_SSN = re.compile(r"\b\d{3}-\d{2}-\d{4}\b")                       # US SSN shape
_CARD = re.compile(r"\b\d{13,16}\b")                             # contiguous card-length digit run
_API_KEYS = (
    re.compile(r"\bsk-[A-Za-z0-9]{16,}\b"),                      # OpenAI-style
    re.compile(r"\bAKIA[0-9A-Z]{16}\b"),                        # AWS access key id
    re.compile(r"\bghp_[A-Za-z0-9]{30,}\b"),                    # GitHub PAT
    re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),           # Slack token
)
#: LOCKED brand set (memory: brand-architecture-and-naming; parent tagline "AI Done Right" per
#: _repos/shared-backend-components/architecture/brand.json — superseded "Context is Everything" preserved there as the rollback target) —
#: at least one must appear in demo copy.
LOCKED_BRANDS = ("AI Done Right", "Baltor", "OpenHubForAI")
#: naming that must NOT appear in NEW user-facing demo copy (flagged tools + retired product terms).
BLOCKED_IN_DEMO_COPY = ("Synapse AI", "Microsoft Conductor")
#: internal trees a human should de-track (NOT publish) before going public — listed, never deleted.
DETRACK_CANDIDATES = ("docs/strategy", "docs/codex", ".research-notes", ".agent")
#: the demo copy that DOES ship publicly (scanned for brand/blocked-term hygiene).
_DEMO_COPY = ("_repos/baltor/frontend/demo-console.html", "_repos/baltor/frontend/reviews.html", "docs/deployment/demo-console.md")


def scan_pii(text: str) -> list[str]:
    """Return PII-pattern hits in `text` (real-domain emails, SSN, card-like, api keys)."""
    hits: list[str] = []
    for m in _EMAIL.finditer(text):
        if not _SAFE_EMAIL.search(m.group(0)):
            hits.append(f"real-domain email: {m.group(0)}")
    if _SSN.search(text):
        hits.append("SSN-shaped string")
    if _CARD.search(text):
        hits.append("credit-card-like digit run")
    for rx in _API_KEYS:
        if rx.search(text):
            hits.append(f"api-key-shaped secret ({rx.pattern})")
    return hits


def _iter_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*") if p.is_file()) if root.exists() else []


def assess() -> dict:
    pii: list[str] = []
    for p in _iter_files(_resource("demo-data")):
        try:
            for h in scan_pii(p.read_text(encoding="utf-8")):
                pii.append(f"{p.relative_to(_REPO).as_posix()}: {h}")
        except (UnicodeDecodeError, OSError):
            continue  # binary/unreadable → not text PII

    env_findings: list[str] = []
    env = _REPO / ".env.example"
    if env.exists():
        for i, line in enumerate(env.read_text(encoding="utf-8").splitlines(), 1):
            if "=" not in line or line.strip().startswith("#"):
                continue
            val = line.split("=", 1)[1].strip().strip('"\'')
            if any(rx.search(val) for rx in _API_KEYS):
                env_findings.append(f".env.example:{i}: real-looking secret value")

    brand_findings: list[str] = []
    branded = False
    for rel in _DEMO_COPY:
        p = _resource(rel)
        if not p.exists():
            continue
        txt = p.read_text(encoding="utf-8")
        if any(b in txt for b in LOCKED_BRANDS):
            branded = True
        for bad in BLOCKED_IN_DEMO_COPY:
            if bad in txt:
                brand_findings.append(f"{rel}: blocked naming {bad!r}")
    if not branded:
        brand_findings.append("no LOCKED brand appears in any demo copy (unbranded)")

    detrack = [d for d in DETRACK_CANDIDATES if (_resource(d)).exists()]
    ready = not pii and not env_findings and not brand_findings
    return {"ready": ready, "pii_findings": pii, "env_findings": env_findings,
            "brand_findings": brand_findings, "detrack_candidates": detrack}


def _self_test() -> int:
    failures: list[str] = []

    def chk(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    rep = assess()
    chk("bundled demo-data is synthetic-only (no real PII)", not rep["pii_findings"], "; ".join(rep["pii_findings"][:3]))
    chk(".env.example has no real-looking secrets", not rep["env_findings"], "; ".join(rep["env_findings"][:2]))
    chk("demo copy uses the LOCKED brand set + no blocked naming", not rep["brand_findings"], "; ".join(rep["brand_findings"][:2]))
    chk("de-track candidate list is non-empty (human reviews before public)", bool(rep["detrack_candidates"]),
        str(rep["detrack_candidates"]))

    # NEGATIVE: an inline string with a real email + SSN + key MUST be flagged (scanner works).
    bad = "Contact john@gmail.com, SSN 123-45-6789, key sk-ABCDEFGHIJKLMNOP12345"
    hits = scan_pii(bad)
    chk("scanner flags a real email", any("email" in h for h in hits))
    chk("scanner flags an SSN", any("SSN" in h for h in hits))
    chk("scanner flags an api key", any("api-key" in h for h in hits))
    # POSITIVE: a synthetic .example email is NOT flagged.
    chk("scanner passes a *.example email", not scan_pii("alice@acme.example"))

    chk("assessment is deterministic", assess() == rep)

    print(f"\n{'all check_prelaunch self-tests passed (demo synthetic-only; scanners proven; read-only gate).' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Private→public readiness gate (read-only; reports).")
    p.add_argument("--self-test", action="store_true")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    rep = assess()
    print("=== Baltor pre-launch readiness (READ-ONLY report) ===")
    print(f"READY: {rep['ready']}")
    for key in ("pii_findings", "env_findings", "brand_findings"):
        items = rep[key]
        print(f"\n{key} ({len(items)}):")
        print("\n".join(f"  - {x}" for x in items) if items else "  (none)")
    print(f"\nde-track before public (review + git rm --cached, NOT done here): {rep['detrack_candidates']}")
    return 0 if rep["ready"] else 1


if __name__ == "__main__":
    raise SystemExit(_main())
