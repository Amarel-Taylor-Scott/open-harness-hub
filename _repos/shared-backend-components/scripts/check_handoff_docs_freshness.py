#!/usr/bin/env python3
"""Validate AI Done Right handoff freshness docs.

This proof keeps the parser-friendly goal handoff, surface counts, method spine,
service-auth references, and transfer reading order from drifting apart.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path


REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
HANDOFF = _resource("docs") / "handoff"
STATE = (REPO / ".agent") / "aidoneright-current-state-verification.json"
BUNDLE = _resource("dist/sites/aidoneright-design")

DOCS = {
    "freshness": HANDOFF / "handoff-freshness.md",
    "claude": HANDOFF / "claude-code-max-transfer.md",
    "codex": HANDOFF / "codex-transfer.md",
    "counts": HANDOFF / "openhub-surface-counts.md",
}

REQUIRED_BUNDLE_FILES = [
    "START-HERE-CLAUDE-CODE.md",
    "README.md",
    "HANDOFF.md",
    "CLAUDE-CODE.md",
    "MARKETING.md",
    "POSITIONING-AUDIT.md",
    "BACKEND-STACK.md",
    "UX-BACKLOG.md",
    "shared/products.js",
    "screens/INDEX.md",
]

METHOD_HUBS = [
    "OpenReconciliationHub",
    "OpenHardeningHub",
    "OpenEnrichmentHub",
    "OpenOptimizationHub",
    "OpenVerificationHub",
]

REQUIRED_TRANSFER_TERMS = [
    "README.md",
    "START-HERE-CLAUDE-CODE.md",
    "HANDOFF.md",
    "CLAUDE.md",
    "CLAUDE-CODE.md",
    "MARKETING.md",
    "POSITIONING-AUDIT.md",
    "BACKEND-STACK.md",
    "UX-BACKLOG.md",
    "products.js",
    "screens/INDEX.md",
    "Control Tower",
    "parent site",
    "Baltor",
    "Teleon",
    "all live hubs",
    "all private bench hubs",
    "method-spine docs",
    "service-auth docs",
    "production-readiness gap",
    "next loop prompt",
]

FORBIDDEN_SECRET_PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{16,}"),
    re.compile(r"AKIA[0-9A-Z]{12,}"),
    re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
]


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    check("current-state verification receipt exists", STATE.exists(), str(STATE))
    state = json.loads(_read(STATE)) if STATE.exists() else {}
    inv = state.get("surface_inventory", {})

    for key, path in DOCS.items():
        check(f"{key}: handoff doc exists", path.exists(), str(path))

    texts = {key: _read(path) for key, path in DOCS.items() if path.exists()}
    combined = "\n".join(texts.values())

    for rel in REQUIRED_BUNDLE_FILES:
        check(f"bundle source exists: {rel}", (BUNDLE / rel).exists(), str(BUNDLE / rel))

    check("short /goal command recorded",
          "/goal follow the instructions in docs/goals/aidoneright-portfolio-loop.md" in combined)

    expected_counts = {
        "design_family_total": 24,
        "products": 2,
        "open_hubs_total": 21,
        "live_open_hubs": 9,
        "private_bench_hubs": 12,
        "operational_demo_registry_surfaces": 20,
        "static_launch_sites": 7,
    }
    for key, expected in expected_counts.items():
        check(f"state count {key} == {expected}", inv.get(key) == expected, str(inv.get(key)))
        check(f"docs mention count {expected} for {key}", str(expected) in combined)

    for hub in METHOD_HUBS:
        check(f"method spine names {hub}", hub in combined)

    for term in REQUIRED_TRANSFER_TERMS:
        check(f"transfer docs mention {term}", term in combined)

    for phrase in [
        "AI Done Right",
        "Baltor governs context",
        "Teleon runs capabilities",
        "OpenHubForAI registries are discovery surfaces",
        "Discovery is not trust",
        "Output is not truth",
        "Dashboards are projection-only",
        "service-auth-and-consumption-model.md",
        "architecture/service_auth_consumption_model.json",
        "check_service_auth_consumption_model.py --self-test",
        "check_ai_done_right_surface_family.py --self-test",
    ]:
        check(f"boundary/proof phrase present: {phrase}", phrase in combined)

    for pattern in FORBIDDEN_SECRET_PATTERNS:
        check(f"no raw secret pattern {pattern.pattern}", not pattern.search(combined))

    print("\n" + (
        "PASS - check_handoff_docs_freshness: AI Done Right handoff docs exist, "
        "record current surface counts, name the five method hubs, link service-auth "
        "and design-family proofs, include transfer artifacts, and contain no obvious raw secrets."
        if not fails else f"{len(fails)} FAILURES: {fails}"
    ))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_handoff_docs_freshness.py --self-test")
    raise SystemExit(0)
