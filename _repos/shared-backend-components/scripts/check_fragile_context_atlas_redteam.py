#!/usr/bin/env python3
"""scripts.check_fragile_context_atlas_redteam — PROOF (NEGATIVE): the Fragile Context Atlas validator actually REJECTS
governance violations. _repos/shared-backend-components/scripts/check_fragile_context_atlas.py proves the real files are clean; this proof feeds the SAME
validator (find_violations) deliberately-broken copies of the real atlas and asserts the matching guardrail fires for
each attack. One validator, two directions — a guardrail that is never exercised against a violation is not a guardrail.

Control:
  0. the unmodified real atlas produces ZERO violations (so every attack below is the mutation's fault, not a baseline).

Attacks (each = a deep copy of the real atlas with ONE injected violation; the named rule MUST fire):
  1. public named-company accusation          -> brand_named
  2. pack marked as a TRUTH status            -> status_invalid
  3. pack with no source authority            -> no_source_authority
  4. pack with no held-out example            -> no_heldout
  5. time-fragile pack with no refresh policy -> refresh_missing
  6. private credential leaked into the hub   -> secret_leak
  7. held-out contradiction served (not held) -> heldout_not_never_served
  8. benchmark result cited as authority      -> benchmark_authority
  9. unverified LLM output cited as authority -> llm_authority
 10. active pack overclaiming a non-existent demo -> demo_bijection
 11. candidate pack given a served answer (candidate-as-active) -> candidate_invalid
 12. duplicate demo priority                  -> dup_demo_priority

Deterministic + offline. Exit 0/1.
"""
from __future__ import annotations

import copy
import json
import os
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from scripts.check_fragile_context_atlas import _ATLAS, _TAXONOMY, find_violations, load_refs

_TIME_MODES = {"TIME_FRAGILE", "FRESHNESS_FRAGILE"}


def _first_time_pack_index(atlas: dict) -> int:
    for i, p in enumerate(atlas["packs"]):
        if _TIME_MODES & set(p.get("fragility_modes") or []):
            return i
    return 0


def _first_candidate_index(atlas: dict) -> int:
    for i, p in enumerate(atlas["packs"]):
        if p.get("status") == "candidate":
            return i
    return -1


def _atk_vendor(a):       a["packs"][0]["title"] += " — Glean serves stale answers"
def _atk_truth(a):        a["packs"][0]["status"] = "truth"
def _atk_no_auth(a):      a["packs"][0]["source_authorities"] = []
def _atk_no_held(a):      a["packs"][0]["held_out_examples"] = []
def _atk_no_refresh(a):   a["packs"][_first_time_pack_index(a)]["refresh_policy"] = {}
def _atk_secret(a):       a["packs"][0]["source_authorities"].append("Bearer abcdef0123456789ghijklmno")
def _atk_serve_held(a):   a["packs"][0]["held_out_examples"][0]["never_served"] = False
def _atk_benchmark(a):    a["packs"][0]["source_authorities"] = ["benchmark result: 0.94 on our eval set"]
def _atk_llm(a):          a["packs"][0]["source_authorities"] = ["LLM output (model-generated, unverified)"]
def _atk_overclaim(a):    a["packs"].append({"pack_id": "fragile.x.ghost", "status": "active", "domain": a["packs"][0]["domain"],
                                             "title": "ghost", "fragility_modes": ["AUTHORITY_FRAGILE"], "volatility_class": "low",
                                             "source_authorities": ["x"], "demo_key": "ghostdemo", "served_answer": "z",
                                             "held_out_examples": [{"value": "y", "status": "stale", "never_served": True}]})
def _atk_cand_served(a):
    i = _first_candidate_index(a)
    a["packs"][i]["served_answer"] = "now serving an unverified candidate"
def _atk_dup_priority(a):  a["packs"][1]["demo_priority"] = a["packs"][0]["demo_priority"]


_ATTACKS = [
    ("1. public named-company accusation", "brand_named", _atk_vendor),
    ("2. pack marked as a TRUTH status", "status_invalid", _atk_truth),
    ("3. pack with no source authority", "no_source_authority", _atk_no_auth),
    ("4. pack with no held-out example", "no_heldout", _atk_no_held),
    ("5. time-fragile pack, no refresh policy", "refresh_missing", _atk_no_refresh),
    ("6. private credential leaked into the hub", "secret_leak", _atk_secret),
    ("7. held-out contradiction served (not held)", "heldout_not_never_served", _atk_serve_held),
    ("8. benchmark result cited as authority", "benchmark_authority", _atk_benchmark),
    ("9. unverified LLM output cited as authority", "llm_authority", _atk_llm),
    ("10. active pack overclaiming a non-existent demo", "demo_bijection", _atk_overclaim),
    ("11. candidate given a served answer (candidate-as-active)", "candidate_invalid", _atk_cand_served),
    ("12. duplicate demo priority", "dup_demo_priority", _atk_dup_priority),
]


def _self_test() -> int:
    fails: list[str] = []

    def check(n: str, ok: bool, d: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}{(': ' + d) if d and not ok else ''}")
        if not ok:
            fails.append(n)

    tax = json.loads(_TAXONOMY.read_text(encoding="utf-8"))
    atlas = json.loads(_ATLAS.read_text(encoding="utf-8"))
    refs = load_refs()

    # 0. control — the real atlas is clean
    base = find_violations(tax, atlas, refs)
    base_total = sum(len(x) for x in base.values())
    check("0. CONTROL: the unmodified real atlas yields ZERO violations", base_total == 0,
          json.dumps({k: base[k] for k in base if base[k]}))

    # 1..11 — each injected attack fires its guardrail
    for name, rule, mutate in _ATTACKS:
        broken = copy.deepcopy(atlas)
        mutate(broken)
        v = find_violations(tax, broken, refs)
        fired = bool(v.get(rule))
        check(f"{name} -> rule '{rule}' fires", fired, f"fired rules={sorted(k for k in v if v[k])}")

    print("\n" + (f"PASS — check_fragile_context_atlas_redteam: the real atlas is clean (0 violations) and all "
                  f"{len(_ATTACKS)} injected governance attacks (vendor accusation, pack-as-truth, missing source "
                  "authority/held-out, missing refresh, leaked credential, served contradiction, benchmark/LLM cited as "
                  "authority, demo overclaim, candidate-as-active, duplicate priority) are caught by the shared validator." if not fails
                  else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_fragile_context_atlas_redteam.py --self-test")
    raise SystemExit(0)
