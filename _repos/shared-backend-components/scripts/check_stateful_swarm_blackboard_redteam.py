#!/usr/bin/env python3
"""check_stateful_swarm_blackboard_redteam — adversarial proof for the stateful-swarm + governed-blackboard layer.

A shared ``find_violations(record, *, catalog, module_src)`` validator is reused by BOTH a CONTROL (the REAL CFPB
``blackboard.baltor.cfpb_evidence@v1`` run projected into a record + the REAL stateful-swarm catalog + the REAL
module source → MUST be clean) AND attack fixtures, each of which mutates ONE thing and MUST be caught:

  A1  observation -> CanonicalFact         an observation entry is marked serves_truth / promoted to a canonical fact
  A2  analysis    -> served_fact           an analysis entry is marked a served fact (analysis is never truth)
  A3  synthesis-ignores-held-out           the served answer LEAKS the held-out "30 days" (held-out must stay a warning)
  A4  missing-source-handles               an observation / the synthesis has NO source handle (sourceless)
  A5  tenant-private-entry-in-public-proj   a tenant-private entry's lineage leaks into the public governed projection
  A6  benchmark/score-as-promotion         a benchmark score is used to set promotion_eligible=true (score != promotion)
  A7  swarm.irys-marked-active-without-proof the Irys candidate is marked active in the catalog (candidate != active)
  A8  live-LLM-call-in-self-test           a worker turn records a live LLM call symbol (the local stub is deterministic)
  A9  raw-key-in-a-receipt                 a worker receipt carries a raw API key literal (refs are env:// only)
  A10 compression-drops-held-out           a compression report drops held-out items (lossless distillation violation)
  A11 entity-mismatch-not-surfaced-as-gap   an entity mismatch exists but no gap was raised (must be surfaced, not dropped)

Deterministic, offline, stdlib only. Mirrors the agent-runtime-layer redteam shape (control + attacks via one validator).
_REPO = parents[1]; sys.path.insert. No raw keys (any fake key is ASSEMBLED from fragments).

CLI: PYTHONPATH=. python3 _repos/shared-backend-components/scripts/check_stateful_swarm_blackboard_redteam.py --self-test
"""
from __future__ import annotations

import argparse
import copy
import json
import re
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
from scripts._repo_paths import resource as _resource
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.environments.baltor_cfpb_context_governance import HELD_OUT_CONTRADICTION  # noqa: E402
from src.teleon.ports.blackboard_provider import (  # noqa: E402
    KIND_ANALYSIS,
    KIND_OBSERVATION,
)
from src.teleon.stateful_swarms.cfpb_evidence_demo import run_cfpb_evidence_demo  # noqa: E402

_NOW = "2026-06-08T00:00:00Z"
#: the active local stub id + the Irys research-candidate id (single source — mirrors the catalog).
_LOCAL_STUB_ID = "swarm.local_stub@v1"
_IRYS_ID = "stateful_swarm.irys@research_candidate"
#: the swarm catalog this redteam reads (the same one check_stateful_swarm_provider_catalog.py governs).
_SWARM_CATALOG = _resource("architecture") / "stateful_swarm_provider_catalog.json"

#: a FAKE leaked key for A9 — ASSEMBLED from fragments so the literal never appears in tracked source (otherwise
#: a secret-hygiene scan would correctly flag it); it still matches _KEY_RE at runtime.
_FAKE_LEAKED_KEY = "sk-" + "live" + "0123456789abcdef"
_KEY_RE = re.compile(r"(sk-[A-Za-z0-9]{8,}|AKIA[0-9A-Z]{12,}|gsk_[A-Za-z0-9]{8,}|AIza[0-9A-Za-z_\-]{20,})")
#: live-LLM / network call symbols that must NEVER appear in a deterministic local-stub worker turn.
_LIVE_LLM_SYMBOLS = ("openai.", "anthropic.", "requests.", "urllib.request.urlopen", "httpx.", "gemini.")


def find_violations(record: dict, *, catalog: dict, module_src: str) -> list[str]:
    """The single governance gate. Returns a list of violation codes (empty = clean). Used by the control + every attack.

    ``record`` is the projected state of a swarm run: ``entries`` (typed blackboard entries), ``synthesis``
    (the synthesis body), ``governed_entry`` (the GovernedBlackboardEntry verdict), ``served_answer``,
    ``held_out_values``, ``public_projection_refs`` (lineage exposed in the public projection),
    ``worker_turns`` (each turn's recorded detail incl. any llm symbol / receipt), ``entity_mismatch``,
    ``compression_report`` (optional). ``catalog`` is the stateful-swarm runner catalog; ``module_src`` is the
    concatenated teleon swarm/port module source.
    """
    v: list[str] = []
    entries = record.get("entries", [])

    # ── entry-level governance: a blackboard entry is NEVER served truth ──────────────────
    for e in entries:
        kind = e.get("kind")
        eid = e.get("entry_id", "?")
        if e.get("serves_truth") is True:                       # any entry marked truth (envelope flag)
            v.append(f"entry_serves_truth:{kind}:{eid}")
        body = e.get("body", {})
        if isinstance(body, dict) and body.get("serves_truth") is True:  # typed body marked truth
            v.append(f"entry_body_serves_truth:{kind}:{eid}")
        # A1: an observation promoted to a canonical fact (a fact field / canonical_fact flag on an observation).
        if kind == KIND_OBSERVATION and (body.get("canonical_fact") or body.get("is_canonical_fact")):
            v.append(f"observation_as_canonical_fact:{eid}")
        # A2: an analysis marked a served fact.
        if kind == KIND_ANALYSIS and (body.get("served_fact") or body.get("is_served_fact")):
            v.append(f"analysis_as_served_fact:{eid}")
        # A4 (entry side): an observation with NO source handle/refs is sourceless.
        if kind == KIND_OBSERVATION and not (e.get("source_refs") or body.get("source_refs")):
            v.append(f"sourceless_observation:{eid}")

    # ── synthesis-level governance ────────────────────────────────────────────────────────
    served = record.get("served_answer", "")
    held_out_values = record.get("held_out_values", [])
    # A3: the held-out contradiction LEAKED into the served answer (held-out must stay a warning).
    for hv in held_out_values:
        if hv and hv in served:
            v.append(f"held_out_leaked_into_answer:{hv}")
    synthesis = record.get("synthesis", {})
    # A4 (synthesis side): the synthesis carries no source handles (sourceless answer).
    if not synthesis.get("source_handles"):
        v.append("synthesis_missing_source_handles")
    # the served answer itself must carry a source handle (ctx:// or doc#).
    if served and not re.search(r"(ctx://|doc#)\S+", served):
        v.append("served_answer_missing_source_handle")

    # ── governed-projection governance (the Teleon->Baltor seam) ────────────────────────────
    gov = record.get("governed_entry", {})
    if gov.get("serves_truth") is True:                         # the verdict never makes the entry truth
        v.append("governed_entry_serves_truth")
    # A5: a tenant-private entry's lineage leaked into the PUBLIC projection.
    public_refs = record.get("public_projection_refs", [])
    private_ids = {e.get("entry_id") for e in entries if e.get("tenant_private")}
    if private_ids & set(public_refs):
        v.append("tenant_private_in_public_projection")
    # A6: a benchmark/score was used as promotion authority (score != promotion).
    if gov.get("promotion_eligible") is True and gov.get("promotion_basis") in ("benchmark", "score", "leaderboard"):
        v.append("benchmark_score_as_promotion")

    # ── catalog governance: exactly one ACTIVE runner; Irys is research_candidate ──────────
    runners = catalog.get("entries", [])
    active = [r for r in runners if r.get("status") == "active"]
    if not (len(active) == 1 and active[0].get("provider_id") == _LOCAL_STUB_ID):
        v.append("active_runner_invariant")
    for r in runners:
        rid = r.get("provider_id", "?")
        # A7: the Irys candidate marked active (candidate != active; it needs install + keys + a proof).
        if rid == _IRYS_ID and r.get("status") == "active":
            v.append("irys_marked_active_without_proof")
        if _KEY_RE.search(json.dumps(r)):                       # no raw key anywhere in a catalog card
            v.append(f"raw_key_in_catalog:{rid}")

    # ── worker-turn governance: deterministic local stub + receipts ────────────────────────
    for t in record.get("worker_turns", []):
        wid = t.get("worker_id", "?")
        # A8: a live-LLM / network call symbol in a turn (the local stub is deterministic — no model, no network).
        sig = str(t.get("call_signature", ""))
        if any(sym in sig for sym in _LIVE_LLM_SYMBOLS):
            v.append(f"live_llm_call_in_turn:{wid}")
        # A9: a raw API key literal in a worker receipt (refs are env:// / receipt ids only).
        if _KEY_RE.search(json.dumps(t.get("receipt", {}))):
            v.append(f"raw_key_in_receipt:{wid}")

    # ── lossless distillation: compression preserves held-out + source handles ──────────────
    comp = record.get("compression_report")
    if comp is not None:
        # A10: compression dropped held-out items (omitted != deleted — lossless distillation law).
        before = set(comp.get("held_out_before", []))
        after = set(comp.get("held_out_after", []))
        if before - after:
            v.append("compression_dropped_held_out")
        if not comp.get("source_handles_preserved", True):
            v.append("compression_dropped_source_handles")

    # ── A11: an entity mismatch must be surfaced as a GAP, never silently dropped ───────────
    if record.get("entity_mismatch") and not record.get("entity_mismatch_surfaced_as_gap"):
        v.append("entity_mismatch_not_surfaced")

    # ── dependency law: Teleon never imports Baltor ─────────────────────────────────────────
    if re.search(r"^\s*(from|import)\s+.*\bbaltor\b", module_src, re.MULTILINE):
        v.append("baltor_import")
    return v


def _build_control_record() -> dict:
    """Project a REAL CFPB demo run + the REAL catalog into a clean ``record``. This MUST be clean."""
    r = run_cfpb_evidence_demo(now=_NOW)
    entries = r["signals"] + r["observations"] + r["gaps"] + r["analyses"] + r["synthesis"]
    synth_body = r["synthesis"][0]["body"] if r["synthesis"] else {}
    gov = dict(r["governed_entry"])
    gov.setdefault("promotion_basis", "governance_gate")  # honest: NOT a benchmark/score
    # the public projection exposes only the (non-private) source handles + receipt refs — no private lineage.
    public_refs = list(gov.get("source_handles", [])) + list(gov.get("receipt_refs", []))
    # worker turns: each carries a receipt and NO live-LLM call signature (deterministic stub).
    worker_turns = [
        {"worker_id": wr.worker_id, "call_signature": "", "receipt": _receipt_for(r, wr.receipt_id)}
        for wr in r["worker_results"]
    ]
    # the entity_resolver surfaced no mismatch (the CFPB docs share one entity) — record that honestly.
    gov_detail = next((wr.detail for wr in r["worker_results"] if wr.worker_id == "entity_resolver"), {})
    return {
        "entries": entries,
        "synthesis": synth_body,
        "governed_entry": gov,
        "served_answer": r["served_answer"],
        "held_out_values": r["held_out_values"],
        "public_projection_refs": public_refs,
        "worker_turns": worker_turns,
        "entity_mismatch": bool(gov_detail.get("entity_mismatch")),
        "entity_mismatch_surfaced_as_gap": True,  # the resolver raises a gap WHEN a mismatch exists (none here)
        "compression_report": None,  # the control run did not compress (no lossless-distillation step to check)
    }


def _receipt_for(r: dict, receipt_id: str | None) -> dict:
    for rc in r["receipts"]:
        if rc.get("receipt_id") == receipt_id:
            return rc
    return {}


def _load_catalog() -> dict:
    return json.loads(_SWARM_CATALOG.read_text())


def _module_src() -> str:
    files = [
        _resource("src/teleon/ports/stateful_swarm_provider.py"),
        _resource("src/teleon/stateful_swarms/local_swarm.py"),
        _resource("src/teleon/stateful_swarms/cfpb_evidence_demo.py"),
    ]
    return "\n".join(f.read_text() for f in files)


def main() -> int:
    cat = _load_catalog()
    module_src = _module_src()
    control = _build_control_record()

    fails: list[str] = []
    base = find_violations(control, catalog=cat, module_src=module_src)
    if base:
        fails.append(f"CONTROL must be clean, got {base}")

    def attack(name: str, mutate, *, expect: str, on_catalog=False, on_src=None) -> None:
        rec = copy.deepcopy(control)
        c = cat
        src = module_src
        if on_src is not None:
            src = on_src
        elif on_catalog:
            c = copy.deepcopy(cat)
            mutate(c)
        else:
            mutate(rec)
        viol = find_violations(rec, catalog=c, module_src=src)
        if not any(x.startswith(expect) for x in viol):
            fails.append(f"attack '{name}' NOT caught (expected {expect!r}, got {viol})")

    def first(rec, kind):
        return next(e for e in rec["entries"] if e["kind"] == kind)

    # A1 observation -> CanonicalFact
    attack("A1 observation->CanonicalFact",
           lambda rec: first(rec, KIND_OBSERVATION)["body"].__setitem__("canonical_fact", True),
           expect="observation_as_canonical_fact")
    # A2 analysis -> served_fact
    attack("A2 analysis->served_fact",
           lambda rec: first(rec, KIND_ANALYSIS)["body"].__setitem__("served_fact", True),
           expect="analysis_as_served_fact")
    # A3 synthesis-ignores-held-out (leak "30 days" into the answer)
    attack("A3 synthesis leaks held-out into answer",
           lambda rec: rec.__setitem__("served_answer", rec["served_answer"] + f" Note: some say {HELD_OUT_CONTRADICTION}."),
           expect="held_out_leaked_into_answer")
    # A4 missing-source-handles (strip the synthesis source handles)
    attack("A4 synthesis missing source handles",
           lambda rec: rec["synthesis"].__setitem__("source_handles", []),
           expect="synthesis_missing_source_handles")
    # A5 tenant-private-entry-in-public-projection
    def a5(rec):
        obs = first(rec, KIND_OBSERVATION)
        obs["tenant_private"] = True
        rec["public_projection_refs"] = rec["public_projection_refs"] + [obs["entry_id"]]
    attack("A5 tenant-private entry in public projection", a5, expect="tenant_private_in_public_projection")
    # A6 benchmark/score-as-promotion
    def a6(rec):
        rec["governed_entry"]["promotion_eligible"] = True
        rec["governed_entry"]["promotion_basis"] = "benchmark"
    attack("A6 benchmark score as promotion", a6, expect="benchmark_score_as_promotion")
    # A7 swarm.irys-marked-active-without-proof
    attack("A7 irys marked active",
           lambda c: next(r for r in c["entries"] if r["provider_id"] == _IRYS_ID).__setitem__("status", "active"),
           expect="irys_marked_active_without_proof", on_catalog=True)
    # A8 live-LLM-call-in-self-test
    attack("A8 live-LLM call in a worker turn",
           lambda rec: rec["worker_turns"][0].__setitem__("call_signature", "openai.ChatCompletion.create(...)"),
           expect="live_llm_call_in_turn")
    # A9 raw-key-in-a-receipt
    attack("A9 raw key in a worker receipt",
           lambda rec: rec["worker_turns"][0]["receipt"].__setitem__("llm_route_receipt_ref", _FAKE_LEAKED_KEY),
           expect="raw_key_in_receipt")
    # A10 compression-drops-held-out
    attack("A10 compression drops held-out",
           lambda rec: rec.__setitem__("compression_report",
                                       {"held_out_before": ["he-1", "he-2"], "held_out_after": ["he-1"],
                                        "source_handles_preserved": True}),
           expect="compression_dropped_held_out")
    # A11 entity-mismatch-not-surfaced-as-a-gap
    def a11(rec):
        rec["entity_mismatch"] = True
        rec["entity_mismatch_surfaced_as_gap"] = False
    attack("A11 entity mismatch not surfaced as gap", a11, expect="entity_mismatch_not_surfaced")

    # bonus dependency-law attack via injected source (a Teleon module importing baltor).
    attack("A12 baltor import (dependency law)", lambda rec: None,
           expect="baltor_import", on_src="from src.baltor.experiments import parallel_paths\n")

    # ── sanity: a CLEAN compression report (held-out preserved) is NOT flagged ──────────────
    ok_rec = copy.deepcopy(control)
    ok_rec["compression_report"] = {"held_out_before": ["he-1"], "held_out_after": ["he-1"],
                                    "source_handles_preserved": True}
    if find_violations(ok_rec, catalog=cat, module_src=module_src):
        fails.append("a CLEAN compression report (held-out preserved) must NOT be flagged")

    # ── sanity: an A11 mismatch that IS surfaced as a gap is NOT flagged ────────────────────
    ok_rec2 = copy.deepcopy(control)
    ok_rec2["entity_mismatch"] = True
    ok_rec2["entity_mismatch_surfaced_as_gap"] = True
    if any(x.startswith("entity_mismatch_not_surfaced") for x in
           find_violations(ok_rec2, catalog=cat, module_src=module_src)):
        fails.append("a surfaced entity mismatch (gap raised) must NOT be flagged")

    if fails:
        print("check_stateful_swarm_blackboard_redteam: FAILURES")
        for f in fails:
            print("  -", f)
        return 1
    print("PASS — check_stateful_swarm_blackboard_redteam: control clean; 12 attacks caught (observation->fact / "
          "analysis->served-fact / held-out-leak / missing-source-handles / tenant-private-in-public-projection / "
          "benchmark-as-promotion / irys-active-without-proof / live-LLM-in-turn / raw-key-in-receipt / "
          "compression-drops-held-out / entity-mismatch-not-surfaced / baltor-import); clean compression + surfaced "
          "mismatch NOT flagged.")
    return 0


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--self-test", action="store_true")
    ap.parse_args()
    raise SystemExit(main())
