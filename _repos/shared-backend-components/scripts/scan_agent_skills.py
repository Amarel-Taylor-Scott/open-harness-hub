#!/usr/bin/env python3
"""scripts.scan_agent_skills — detect poisoning / hidden instructions / undeclared tools in skills.

Reuses the shared poison detector from scan_mcp_manifests (No-Magic-Values: one pattern set) and
adds a skill-specific check: a skill that invokes shell/network commands but does NOT declare them
in its `allowed-tools` frontmatter is flagged (a skill cannot silently add shell/network/source-write
tools — _repos/shared-backend-components/docs/security/mcp-and-skill-security.md). Stdlib regex pre-screen; a real scanner is the SEAM.

CLI:
    python3 _repos/shared-backend-components/scripts/scan_agent_skills.py --self-test
    python3 _repos/shared-backend-components/scripts/scan_agent_skills.py path/to/SKILL.md
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import argparse
import re
from pathlib import Path

if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    import os
    import sys

    _REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _REPO_ROOT not in sys.path:
        sys.path.insert(0, _REPO_ROOT)

from scripts.scan_mcp_manifests import find_poison

#: shell/network invocations a skill must DECLARE to use.
_SHELL_NET = re.compile(r"\b(curl|wget|subprocess|os\.system|bash\s+-c|nc\s|ssh\s|scp\s)\b", re.I)
#: does the frontmatter declare a shell/network/exec tool?
_DECLARES_SHELL = re.compile(r"allowed-tools:[^\n]*(shell|bash|exec|network|http|curl)", re.I)


def scan_skill(text: str) -> list[str]:
    """Return finding names for a SKILL.md (empty = clean)."""
    findings = list(find_poison(text))
    if _SHELL_NET.search(text or "") and not _DECLARES_SHELL.search(text or ""):
        findings.append("undeclared_shell_or_network")
    return findings


def scan_file(path: Path) -> list[str]:
    return scan_skill(path.read_text(encoding="utf-8"))


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    repo = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
    clean = scan_file(_resource("fixtures/security/clean-skill.md"))
    poisoned = scan_file(_resource("fixtures/security/poisoned-skill.md"))

    check("clean skill → no findings", clean == [], str(clean))
    check("poisoned skill → flagged (ENFORCEMENT)", bool(poisoned), "expected findings")
    check("  → caught disregard-rules + secrets/exfil", {"disregard_rules"} <= set(poisoned) and
          ("secrets_access" in poisoned or "exfiltration" in poisoned), str(poisoned))
    check("  → caught undeclared shell/network", "undeclared_shell_or_network" in poisoned)
    # a declared shell tool is NOT flagged for undeclared use
    declared = scan_skill("---\nname: x\nallowed-tools: [shell]\n---\nrun curl https://api.example.com")
    check("declared shell use is not flagged undeclared", "undeclared_shell_or_network" not in declared)

    print(f"\n{'all scan_agent_skills self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Scan agent SKILL.md files for poisoning / undeclared tools.")
    p.add_argument("--self-test", action="store_true")
    p.add_argument("skill", nargs="?")
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.skill:
        findings = scan_file(Path(args.skill))
        if findings:
            print("FAIL — skill security findings: " + ", ".join(findings))
            return 1
        print("OK — no skill poisoning signatures (stdlib pre-screen; run a real scanner in CI).")
        return 0
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
