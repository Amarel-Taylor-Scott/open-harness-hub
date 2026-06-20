#!/usr/bin/env python3
"""scripts.check_no_direct_provider_bypass — proof (the wrapper-first rule): a processor may not reach a
boundary directly when a port/wrapper exists. Processors must not import raw sqlite3, the admin server, the
global BUS/DURABLE, or a vendor LLM SDK — those live only inside adapters/providers. And vendor LLM SDKs
may only be imported inside the LLM gateway. This is what keeps internals swappable behind stable surfaces.

CLI: python3 scripts/check_no_direct_provider_bypass.py --self-test
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
#: processor designations — business logic that must go through ctx ports, never raw backends.
_PROCESSOR_GLOBS = ["scripts/runtime/builtin_processors.py", "src/baltor/processors/**/*.py"]
_PROCESSOR_FORBIDDEN = (r"^\s*import sqlite3", r"sqlite3\.connect", r"baltor_admin_demo_server",
                        r"^\s*from web", r"\bDURABLE\b", r"\bBUS\.publish")
#: vendor LLM SDKs may ONLY be imported inside the gateway.
_VENDOR_LLM = (r"^\s*import openai", r"^\s*from openai", r"^\s*import anthropic", r"google\.generativeai",
               r"^\s*import ollama", r"^\s*import vllm")
_LLM_GATEWAY_DIRS = ("scripts/llm_gateway", "src/baltor/llm_gateway")
_GOVERNED = ["scripts/runtime", "scripts/artifact_graph", "scripts/security", "src/baltor"]


def _files(globs):
    out = []
    for g in globs:
        out += [p for p in _REPO.glob(g) if p.is_file() and "__pycache__" not in p.parts]
    return sorted(set(out))


def _walk(dirs):
    out = []
    for d in dirs:
        p = _REPO / d
        if p.is_dir():
            out += [f for f in p.rglob("*.py") if "__pycache__" not in f.parts]
    return sorted(set(out))


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    # 1) processors do not reach raw backends / admin / global bus
    proc_offenders = []
    for p in _files(_PROCESSOR_GLOBS):
        text = p.read_text(encoding="utf-8", errors="ignore")
        for pat in _PROCESSOR_FORBIDDEN:
            if re.search(pat, text, re.M):
                proc_offenders.append(f"{p.relative_to(_REPO)}:{pat}")
    check("processors do NOT import raw sqlite3 / admin server / global BUS / DURABLE", proc_offenders == [], str(proc_offenders))

    # 2) vendor LLM SDKs appear only inside the gateway
    llm_offenders = []
    for p in _walk(_GOVERNED):
        rel = str(p.relative_to(_REPO))
        if any(rel.startswith(d) for d in _LLM_GATEWAY_DIRS):
            continue
        text = p.read_text(encoding="utf-8", errors="ignore")
        for pat in _VENDOR_LLM:
            if re.search(pat, text, re.M):
                llm_offenders.append(f"{rel}:{pat}")
    check("no direct vendor LLM SDK import outside the LLM gateway", llm_offenders == [], str(llm_offenders))

    # 3) the gateway IS the declared single seam (sanity: a gateway entry point exists)
    check("the LLM gateway seam exists (router)", (_REPO / "scripts/llm_gateway/router.py").exists())

    print(f"\n{'PASS — check_no_direct_provider_bypass: processors reach storage/bus/LLM only through ports; vendor SDKs live only behind the gateway. Internals stay swappable behind stable surfaces.' if not fails else f'{len(fails)} FAILURES: {fails}'}")
    return 0 if not fails else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Proof: no direct provider/storage/LLM bypass in processors.")
    p.add_argument("--self-test", action="store_true")
    a = p.parse_args(argv)
    if a.self_test:
        return _self_test()
    p.print_help(); return 0


if __name__ == "__main__":
    raise SystemExit(_main())
