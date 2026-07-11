#!/usr/bin/env python3
"""check_discovery_pipeline — the GitHub/Facebook -> ideas pipeline + the runtime KEY HOLDER are real + governed.

Proves: the pipeline spec has sources (github wired / facebook governed+key-gated) mapping to real key services + the 4
stages (discover/classify/ideate/govern); the KEY HOLDER is REDACTION-SAFE (no values), honors byo/platform ownership,
shapes auth headers, and gates social on a held key (honest 'needs RAPIDAPI_KEY'); classify->ideate->govern keeps
everything a license-classified, deduped CANDIDATE (discovery≠trust, promotion boundary). serves_truth=false.

  python3 _repos/shared-backend-components/scripts/check_discovery_pipeline.py --self-test
"""
from __future__ import annotations

import json
from pathlib import Path

from scripts import discovery_pipeline as P
from src.teleon.research.source_search import ToolHit
from src.teleon.runtime.key_holder import py_const_src_teleon_runtime_key_holder__HOLDER

REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource


def _self_test() -> int:
    spec = json.loads((_resource("architecture") / "discovery_pipeline.json").read_text(encoding="utf-8"))
    cred = {s["id"] for s in json.loads((_resource("architecture") / "credential_registry.json").read_text())["services"]}
    fails = []
    def ck(n, ok, d=""):
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok: fails.append(n)

    # ── spec ──────────────────────────────────────────────────────────────────────────────────────────────────
    srcs = {s["id"]: s for s in spec["sources"]}
    ck("sources include github + facebook", {"github", "facebook"} <= set(srcs))
    ck("each source's key_service is a real credential service (or none)",
       all(s.get("key_service") in cred or s.get("key_service") is None for s in spec["sources"]))
    ck("facebook is governed (public-only/ToS) + key-gated", "ToS" in srcs["facebook"].get("governance", "") and srcs["facebook"]["key_service"] == "rapidapi")
    ck("4 stages: discover/classify/ideate/govern", {s["stage"] for s in spec["stages"]} == {"discover", "classify", "ideate", "govern"})
    ck("ideation kinds = tool/plugin/capability", set(spec["ideation_kinds"]) == {"tool", "plugin", "capability"})

    # ── key holder: redaction + ownership + gating ────────────────────────────────────────────────────────────
    # redaction: an actual secret VALUE in the env must NOT appear in the status (env-var NAMES like AWS_SECRET_ACCESS_KEY are fine)
    secret = "SUPERSECRETtoken_DO_NOT_LEAK_42"
    st = py_const_src_teleon_runtime_key_holder__HOLDER.status({"OH_GITHUB_TOKEN": secret}, {"github"})
    ck("holder status leaks NO secret VALUE (redacted)", secret not in json.dumps(st))
    ck("github held keyless (no developer key needed for the cheap tier)", "github" in st["held"])
    ck("rapidapi byo-gated: not held without a key", "rapidapi" not in py_const_src_teleon_runtime_key_holder__HOLDER.held({}))
    ck("holder names the missing env var honestly", py_const_src_teleon_runtime_key_holder__HOLDER.missing("rapidapi", {}) == ["RAPIDAPI_KEY"])
    ck("auth_headers empty without a key; shaped with one",
       py_const_src_teleon_runtime_key_holder__HOLDER.auth_headers("rapidapi", {}) == {} and py_const_src_teleon_runtime_key_holder__HOLDER.auth_headers("rapidapi", {"RAPIDAPI_KEY": "k"}) == {"X-RapidAPI-Key": "k"})
    ck("tenant byo key is honored (github with a token -> held byo)", "github" in py_const_src_teleon_runtime_key_holder__HOLDER.held({"OH_GITHUB_TOKEN": "t"}, {"github"}))

    # ── discover (honest-unavailable) + classify -> ideate -> govern ──────────────────────────────────────────
    _, status = P.discover_sources("ocr", env={})
    ck("facebook honest-unavailable without a held key (never fabricated)", "needs RAPIDAPI_KEY" in status["facebook"])
    ck("classify maps a description to a plane", P.classify_plane("a cross-encoder reranker") == "reranker")
    hits = [ToolHit("github", "x/permrerank", "u", "fast reranker", "MIT", 200),
            ToolHit("github", "x/gplocr", "u", "ocr toolkit", "GPL-3.0", 30)]
    from scripts.discover_tools import build_candidates
    cands = build_candidates(hits, set(), plane=None)
    for c in cands:
        c["plane"] = P.classify_plane(c["name"] + " " + c["description"])
    ideas = [P.ideate(c, {"reranker"}) for c in cands]
    ck("vendorable repo -> tool+plugin+capability idea", set(next(i for i in ideas if i["id"] == "permrerank")["idea_kinds"]) >= {"tool", "plugin"})
    ck("copyleft repo not ideated as a vendorable tool", "tool" not in next(i for i in ideas if i["id"] == "gplocr")["idea_kinds"])
    ck("everything stays a governed candidate", all(c["status"] == "candidate" and c["serves_truth"] is False for c in cands))
    ck("serves_truth=false", spec.get("serves_truth") is False)

    print("\n" + ("PASS - check_discovery_pipeline: github+governed-facebook -> ideas; key holder redacted + byo-gated; "
                  "candidate-only (discovery≠trust)." if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
