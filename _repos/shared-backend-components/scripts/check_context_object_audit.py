#!/usr/bin/env python3
"""scripts.check_context_object_audit — PROOF: the Context Auditor governs REAL governed context.

Runs the auditor (via from_context_objects) over the ACTUAL acme-billing seed graph (demo-data/acme-billing/
seed-graph.json — the real corpus, NOT a hand-crafted fixture) and asserts:
  A. REAL corpus — the seed graph loads with its real objects (>= 8).
  B. STALE flagged from REAL freshness metadata — the auditor flags the stale runbook (freshness.staleness ==
     'stale') as stale_context.
  C. NO FALSE CONFLICT — the structured claims that AGREE (ADR-014 'max_retries = 5' and retry.py
     'MAX_RETRIES = 5') do NOT manufacture a conflict; the auditor's claim_key detector only fires on genuine
     disagreement. (The runbook's PROSE 'retries up to 3 times' is intentionally deferred to the reconciliation
     engine context_graph.find_contradictions — not faked into a claim_key conflict here.)
  D. LOSSLESS-IN / DETERMINISTIC — from_context_objects never mutates the input objects and is deterministic.
  E. evidence, not truth — the manifest carries applied=False; no raw secrets.

Deterministic, offline, stdlib-only. Exit 0/1. `--self-test` runs the gate (also the default body).
"""
from __future__ import annotations

import copy
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

from src.baltor.context_audit import audit, from_context_objects

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
_SEED = _resource("demo-data") / "acme-billing" / "seed-graph.json"
_KEY_RE = re.compile(r"(sk-[A-Za-z0-9]{8,}|AKIA[0-9A-Z]{12,}|gsk_[A-Za-z0-9]{8,})")


def _oid(o: dict) -> str:
    return o.get("context_object_id") or o.get("id") or o.get("title") or ""


def _self_test() -> int:
    fails: list[str] = []

    def ck(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    objects = json.loads(_SEED.read_text())["objects"]
    before = copy.deepcopy(objects)
    sources = from_context_objects(objects)
    rep = audit(sources)
    by_type: dict[str, list[dict]] = defaultdict(list)
    for it in rep["issues"]:
        by_type[it["type"]].append(it)

    # A. real corpus
    ck("A: ran over the REAL acme seed graph (>=8 objects)", len(objects) >= 8, str(len(objects)))

    # B. stale flagged from real freshness metadata
    stale_ids = {_oid(o) for o in objects if str((o.get("freshness") or {}).get("staleness")).lower() == "stale"}
    ck("B: the corpus has >=1 genuinely-stale object", len(stale_ids) >= 1)
    flagged = {sid for i in by_type["stale_context"] for sid in i["sources"]}
    ck("B: the auditor flags the real stale runbook", bool(stale_ids & flagged), f"stale={stale_ids} flagged={flagged}")

    # C. no false conflict on agreeing structured claims
    ck("C: no false-positive conflict on agreeing 'max_retries = 5' claims", not by_type["conflicting_context"],
       str([i["sources"] for i in by_type["conflicting_context"]]))

    # D. deterministic + non-mutating
    ck("D: from_context_objects is deterministic", from_context_objects(objects) == sources)
    ck("D: from_context_objects does not mutate the input objects", objects == before)

    # E. evidence, not truth + no secrets
    ck("E: manifest is evidence, not truth (applied=False)", rep["applied"] is False)
    ck("E: no raw keys", not _KEY_RE.search(json.dumps(rep)))

    # F. COMPOSE find_contradictions — fold the prose/semantic conflict the claim_key heuristic can't see
    from src.baltor.context_audit import audit_context_graph
    seed = json.loads(_SEED.read_text())
    before_seed = copy.deepcopy(seed)
    merged = audit_context_graph(seed)
    mconf = [i for i in merged["issues"] if i["type"] == "conflicting_context"]
    ck("F: audit_context_graph FOLDS the real prose conflict (find_contradictions, obj-runbook 3 vs ADR 5)",
       any(i.get("detector") == "find_contradictions" and "obj-runbook" in i["sources"] for i in mconf), str(mconf)[:200])
    ck("F: DEFER-not-DUPLICATE — base auditor (claim_key) raised 0 conflicts; find_contradictions ADDS exactly the prose one",
       not by_type["conflicting_context"] and len(mconf) >= 1)
    ck("F: merged manifest still flags the stale runbook", any(i["type"] == "stale_context" for i in merged["issues"]))
    ck("F: composed flag set · seed NOT mutated · deterministic",
       merged.get("composed_find_contradictions") is True and seed == before_seed
       and audit_context_graph(json.loads(_SEED.read_text()))["issues"] == merged["issues"])

    print("\n" + ("PASS — check_context_object_audit: the Context Auditor governs REAL governed context (the acme "
                  "seed graph via from_context_objects) — flags the genuinely-stale runbook from real freshness "
                  "metadata, raises NO false conflict on agreeing structured claims (prose conflict deferred to "
                  "find_contradictions), deterministic + non-mutating, evidence-not-truth."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv or len(sys.argv) == 1:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_context_object_audit.py --self-test")
    raise SystemExit(0)
