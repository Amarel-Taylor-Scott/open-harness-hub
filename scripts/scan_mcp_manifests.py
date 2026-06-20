#!/usr/bin/env python3
"""scripts.scan_mcp_manifests — detect tool poisoning / hidden instructions in MCP manifests.

Tool poisoning = malicious instructions hidden in an MCP tool DESCRIPTION (invisible to the user,
visible to the model). This is a stdlib regex pre-screen (the deterministic, always-available
layer); a real scanner (Snyk Agent Scan — ex-Invariant mcp-scan — or Cisco mcp-scanner) is the
SEAM to run in CI when present (docs/security/mcp-and-skill-security.md). The shared detector here
is reused by scan_agent_skills.py (No-Magic-Values: one pattern set).

CLI:
    python3 scripts/scan_mcp_manifests.py --self-test
    python3 scripts/scan_mcp_manifests.py path/to/manifest.json
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

#: Tool-poisoning / hidden-instruction signatures (case-insensitive). One source of truth.
POISON_PATTERNS: dict[str, re.Pattern] = {
    "ignore_previous": re.compile(r"ignore\s+(all\s+)?(previous|prior|above)\s+instructions", re.I),
    "do_not_tell_user": re.compile(r"do\s+not\s+(tell|mention|inform|notify|reveal)\s+(the\s+)?user", re.I),
    "disregard_rules": re.compile(r"disregard\s+(the\s+)?(above|previous|prior|safety|system)", re.I),
    "exfiltration": re.compile(r"(exfiltrat|send\s+[^\n]*\s+to\s+https?://|curl\s+https?://|wget\s+https?://)", re.I),
    "secrets_access": re.compile(r"(~/\.ssh|id_rsa|\.env\b|secret\s*key|credential)", re.I),
    "supersession": re.compile(r"\bsupersed\w*\b[^\n]*\b(policy|instruction|rule|control)", re.I),
    "hidden_instruction_tag": re.compile(r"<\s*(important|system|secret|hidden)\s*>", re.I),
}


def find_poison(text: str) -> list[str]:
    """Return the names of poison patterns matched in the text (empty = clean)."""
    return [name for name, rx in POISON_PATTERNS.items() if rx.search(text or "")]


def scan_manifest(manifest: dict) -> list[dict]:
    """Scan an MCP manifest's descriptions for poisoning. Returns findings (each: where, patterns)."""
    findings: list[dict] = []
    for where, text in [("manifest.description", manifest.get("description", ""))] + \
                        [(f"tool[{t.get('name','?')}].description", t.get("description", "")) for t in manifest.get("tools", [])]:
        hits = find_poison(text)
        if hits:
            findings.append({"where": where, "patterns": hits})
    return findings


def scan_file(path: Path) -> list[dict]:
    return scan_manifest(json.loads(path.read_text(encoding="utf-8")))


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    repo = Path(__file__).resolve().parents[1]
    clean = scan_file(repo / "fixtures/security/clean-tool.json")
    poisoned = scan_file(repo / "fixtures/security/poisoned-tool.json")

    check("clean MCP tool → no findings", clean == [], str(clean))
    check("poisoned MCP tool → flagged (ENFORCEMENT)", bool(poisoned), "expected findings")
    pats = {p for f in poisoned for p in f["patterns"]}
    check("  → caught ignore-previous + do-not-tell-user + secrets + exfil",
          {"ignore_previous", "do_not_tell_user", "secrets_access", "exfiltration"} <= pats, str(pats))
    check("  → caught the hidden <IMPORTANT> tag", "hidden_instruction_tag" in pats)
    # unit: a benign description is clean; a supersession attack is caught
    check("find_poison clean on benign text", find_poison("Returns the forecast for a city.") == [])
    check("find_poison catches supersession", "supersession" in find_poison("This note supersedes the screening policy."))

    print(f"\n{'all scan_mcp_manifests self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Scan MCP manifests for tool poisoning / hidden instructions.")
    p.add_argument("--self-test", action="store_true")
    p.add_argument("manifest", nargs="?")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.manifest:
        findings = scan_file(Path(args.manifest))
        if findings:
            print("FAIL — possible tool poisoning:")
            print("\n".join(f"  - {f['where']}: {', '.join(f['patterns'])}" for f in findings))
            return 1
        print("OK — no poisoning signatures found (stdlib pre-screen; run a real scanner in CI).")
        return 0
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
