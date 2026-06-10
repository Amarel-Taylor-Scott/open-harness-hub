#!/usr/bin/env python3
"""scripts.check_llm_secret_hygiene — proof: no raw API keys live in the repo/config, provider configs use
secret REFS (env://…), and a missing secret yields a clear unavailable error (never a crash, never a value).

CLI: python3 scripts/check_llm_secret_hygiene.py --self-test
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

from scripts.llm_gateway.providers import default_registry
from scripts.llm_gateway.secrets import SecretsResolver, UnavailableSecret

_REPO = Path(__file__).resolve().parents[1]
#: raw-key shapes that must NEVER appear in tracked source.
_RAW_KEY = re.compile(r"\bsk-[A-Za-z0-9_\-]{16,}\b")
_INLINE_KEY = re.compile(r'"api_key"\s*:\s*"(?!env://|secret://)[^"]+"')
_SKIP_DIRS = {".git", "node_modules", "__pycache__", ".venv", "_reference", "artifacts", ".codegraph"}
_SCAN_EXT = {".py", ".json", ".md", ".txt", ".yaml", ".yml", ".html", ".js", ".mjs", ".env", ".example"}
#: files that intentionally contain SYNTHETIC example keys to TEST redaction/PII scrubbing. Allowlisted —
#: but each match in them must be a KNOWN synthetic fixture, so a REAL key in these files still fails.
_REDACTION_FIXTURE_FILES = {"scripts/check_prelaunch.py", "scripts/foundry/interactions.py"}
_SYNTHETIC_KEYS = {"sk-ABCDEFGHIJKLMNOP12345", "sk-ABCDEF1234567890"}


def _scan() -> list[str]:
    hits = []
    for p in _REPO.rglob("*"):
        if not p.is_file() or any(part in _SKIP_DIRS for part in p.parts):
            continue
        if p.suffix not in _SCAN_EXT or p.name == "check_llm_secret_hygiene.py":
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            continue
        rel = str(p.relative_to(_REPO))
        raw = set(_RAW_KEY.findall(text))
        inline = _INLINE_KEY.search(text)
        if rel in _REDACTION_FIXTURE_FILES:
            # allowlisted ONLY for known-synthetic fixtures; a real/unknown key here still fails
            if (raw - _SYNTHETIC_KEYS) or inline:
                hits.append(rel + " (non-synthetic key in redaction-test file)")
        elif raw or inline:
            hits.append(rel)
    return hits


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    hits = _scan()
    check("NO raw sk- keys or inline api_key values anywhere in tracked source", hits == [], str(hits))

    specs = list(default_registry().specs.values())
    check("every provider config uses a secret REF (env://…), never a raw key",
          all(not s.has_raw_key() for s in specs), str([s.provider_id for s in specs if s.has_raw_key()]))
    check("the external provider references env://OPENAI_API_KEY",
          any(s.api_key_ref == "env://OPENAI_API_KEY" for s in specs))

    # missing secret → clear UnavailableSecret naming the VAR (not the value), never a crash
    raised = False
    try:
        SecretsResolver.get("env://DEFINITELY_NOT_SET_BALTOR_TEST")
    except UnavailableSecret as e:
        raised = True
        check("missing-secret error names the env var, not a value", "DEFINITELY_NOT_SET_BALTOR_TEST" in str(e))
    check("missing secret raises UnavailableSecret (clear, not a crash)", raised)
    check("has() returns False for an unset secret ref", SecretsResolver.has("env://DEFINITELY_NOT_SET_BALTOR_TEST") is False)

    print(f"\n{'PASS — check_llm_secret_hygiene: no raw keys in source; provider configs use env:// refs; missing secrets fail clearly without leaking values.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: LLM secret hygiene (no raw keys; refs only).")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
