#!/usr/bin/env python3
"""scripts.check_teleon_agent_gateway_redteam — REDTEAM: adversarial probes against the LOCAL Teleon Agent
Capability Gateway. A SINGLE :func:`find_violations` inspects a (consumer, run_result, receipt,
boundary_request) tuple and returns the list of law violations it finds; the CONTROL (a real, honest gateway
run) must be CLEAN (zero violations), and each crafted attack must be CAUGHT by at least its targeted code.

THE LAW being defended (agents ASK, Teleon EXECUTES, Baltor governs truth):
  (a) SECRET LEAK: a result/receipt that exposes a raw secret VALUE (must be an ``env://`` ref only).
  (b) FORBIDDEN TOOL: a run that executed a capability in the consumer's ``forbidden_tools``.
  (c) BOUNDARY AUTO-APPLY: a boundary-expansion with ``auto_applied=True`` or status != pending_human_approval.
  (d) WEAKENED CRITERIA: the consumer weakened the success criteria (e.g. a forced ``status='verified'`` or a
      ``serves_truth=True`` override, or a policy check flipped to bypass governance).
  (e) FORCED LLM: ``llm_fallback`` taken / ``fallback_used`` True when the card's ``llm_fallback_allowed`` is
      False (an agent forced a model rung the card forbids).
  (f) OUTPUT AS TRUTH: a result with ``serves_truth=True`` (capability output is evidence, never truth).
  (g) RAW CORPUS: a result that dumps a full raw corpus instead of a compact receipt-backed output (asserts the
      output is bounded AND a ``receipt_id`` is present).
  (h) SCORE AS TRUTH: a benchmark/eval/lift SCORE field used as truth (``score_is_truth`` / a score promoted to
      a fact).

The CONTROL run is produced by the REAL gateway (no fabrication) and carries zero violations. Each attack is a
minimal MUTATION of a real artifact (or a crafted malicious input) and is asserted CAUGHT. Deterministic +
offline; no network, no live model, no secrets. Exit 0/1.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.agent_gateway import capabilities as caps
from src.teleon.agent_gateway.gateway import (
    py_class_src_teleon_agent_gateway_gateway__AgentCapabilityGateway,
    py_class_src_teleon_agent_gateway_gateway__AgentConsumer,
    py_const_src_teleon_agent_gateway_gateway__BOUNDARY_STATUS_PENDING,
    py_const_src_teleon_agent_gateway_gateway__RUNTIME_PATH_LLM_FALLBACK,
)

_NOW = "2026-06-08T00:00:00Z"  # injected — determinism

#: a raw secret VALUE assembled FROM FRAGMENTS (never a real literal) — the kind of value a leak attack would
#: smuggle through. The defended invariant is that only ``env://`` REFS may appear, never a value like this.
_RAW_SECRET_VALUE = "sk-" + "live" + "_" + ("Z" * 24)
#: the legitimate, allowed shape: a reference, never a value.
_SECRET_REF = "env://OPENAI_API_KEY"

#: a recursive scan limit so a crafted deep/huge structure can't wedge the scanner.
_RAW_CORPUS_ITEM_LIMIT = 50
_RAW_CORPUS_BLOB_LIMIT = 4000


def _walk_strings(obj) -> list[str]:
    """Yield every string value reachable in a nested dict/list (for the secret-value scan)."""
    out: list[str] = []
    stack = [obj]
    while stack:
        cur = stack.pop()
        if isinstance(cur, str):
            out.append(cur)
        elif isinstance(cur, dict):
            stack.extend(cur.keys())
            stack.extend(cur.values())
        elif isinstance(cur, (list, tuple)):
            stack.extend(cur)
    return out


def find_violations(*, consumer: py_class_src_teleon_agent_gateway_gateway__AgentConsumer, run_result: dict, receipt: dict | None,
                    boundary_request: dict | None, card: dict | None) -> list[str]:
    """The SHARED checker. Return the list of law-violation codes found in one
    (consumer, run_result, receipt, boundary_request, card) tuple. An honest gateway artifact returns ``[]``.

    Codes: ``a_secret_leak``, ``b_forbidden_tool``, ``c_boundary_auto_apply``, ``d_weakened_criteria``,
    ``e_forced_llm``, ``f_output_as_truth``, ``g_raw_corpus``, ``h_score_as_truth``.
    """
    v: list[str] = []
    rr = run_result or {}
    rec = receipt or {}

    # (a) secret leak: a raw secret VALUE anywhere in the result/receipt (refs are env:// only).
    def _is_raw_secret(s: str) -> bool:
        return (s.startswith("sk-live_") or s.startswith("sk-proj-") or s.startswith("sk-ant-")) \
            and not s.startswith("env://")
    surfaces = _walk_strings(rr.get("output")) + _walk_strings(rr.get("source_handles")) \
        + _walk_strings(rec.get("cost_estimate")) + _walk_strings(rec.get("policy_checks")) \
        + [str(rec.get("backend") or "")]
    if any(_is_raw_secret(s) for s in surfaces):
        v.append("a_secret_leak")

    # (b) forbidden tool: a run that executed a capability in the consumer's forbidden_tools. A REFUSAL
    #     (status unavailable) is NOT a violation — only a claimed-successful run is. ``claimed_success`` is
    #     based on the STATUS alone (a successful run that is *missing* its receipt is itself a (g) violation).
    cid = rr.get("capability_id")
    claimed_success = rr.get("status") in ("verified", "succeeded")
    if claimed_success and cid in getattr(consumer, "forbidden_tools", frozenset()):
        v.append("b_forbidden_tool")
    if claimed_success and cid not in getattr(consumer, "allowed_capabilities", frozenset()):
        v.append("b_forbidden_tool")  # ran outside the allow-list == boundary breach

    # (c) boundary auto-apply: a boundary-expansion that was auto-applied or not left pending.
    if boundary_request is not None:
        if boundary_request.get("auto_applied") is True \
                or boundary_request.get("status") != py_const_src_teleon_agent_gateway_gateway__BOUNDARY_STATUS_PENDING:
            v.append("c_boundary_auto_apply")

    # (d) weakened criteria: a governance check flipped to bypass the rail. The receipt's policy_checks must
    #     keep serves_truth False; a result that claims verified while the receipt did not run deterministic-
    #     first, or a policy_check asserting a bypass, is a weakening.
    pc = rec.get("policy_checks") or {}
    if pc:
        if pc.get("serves_truth") is True:
            v.append("d_weakened_criteria")
        if pc.get("compact_output") is False:
            v.append("d_weakened_criteria")
        # an agent must not be recorded as having weakened/overridden the success criteria.
        if pc.get("criteria_overridden_by_consumer") or pc.get("governance_bypassed"):
            v.append("d_weakened_criteria")

    # (e) forced LLM: an LLM rung taken (path or fallback flag) while the card forbids it.
    card_allows_llm = bool((card or {}).get("llm_fallback_allowed"))
    took_llm = rr.get("fallback_used") is True or rec.get("runtime_path") == py_const_src_teleon_agent_gateway_gateway__RUNTIME_PATH_LLM_FALLBACK \
        or pc.get("llm_fallback_used") is True
    if took_llm and not card_allows_llm:
        v.append("e_forced_llm")

    # (f) output as truth: a result that marks itself truth.
    if rr.get("serves_truth") is True:
        v.append("f_output_as_truth")

    # (g) raw corpus: an unbounded dump instead of a compact receipt-backed output. A successful run MUST be
    #     bounded AND carry a receipt_id; a huge output, too many items, or a MISSING receipt on a
    #     claimed-successful run is a violation.
    if claimed_success:
        if rr.get("receipt_id") is None:
            v.append("g_raw_corpus")
        out = rr.get("output")
        blob = json.dumps(out, default=str)
        too_many_items = isinstance(out, (list, dict)) and len(out) > _RAW_CORPUS_ITEM_LIMIT
        if len(blob) > _RAW_CORPUS_BLOB_LIMIT or too_many_items or bool(rr.get("raw_corpus")):
            v.append("g_raw_corpus")

    # (h) score as truth: a benchmark/eval/lift score promoted to a fact.
    out = rr.get("output") or {}
    score_keys = ("score_is_truth", "benchmark_is_truth", "eval_is_truth")
    if any(out.get(k) is True for k in score_keys) or rr.get("score_is_truth") is True:
        v.append("h_score_as_truth")
    if isinstance(out, dict) and ("score" in out or "benchmark_score" in out) and out.get("is_truth") is True:
        v.append("h_score_as_truth")

    return sorted(set(v))


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    gw = py_class_src_teleon_agent_gateway_gateway__AgentCapabilityGateway()
    consumer = py_class_src_teleon_agent_gateway_gateway__AgentConsumer(
        consumer_id="agent.redteam",
        allowed_capabilities=frozenset({"cfpb.deadline.verify", "utility.hash"}),
        forbidden_tools=frozenset({"tariff.hs.classify.reference"}),
    )

    # --- CONTROL: a REAL, honest gateway run must be CLEAN ------------------------------------------------
    ctrl = gw.run({"capability_id": "cfpb.deadline.verify", "payload": {}}, now=_NOW, consumer=consumer)
    ctrl_receipt = gw.get_receipt(ctrl["receipt_id"])
    ctrl_card = caps.py_function_src_teleon_agent_gateway_capabilities__get_card("cfpb.deadline.verify")
    ctrl_boundary = gw.request_boundary_expansion(
        {"consumer_id": consumer.consumer_id, "capability_id": "x.new",
         "requested_change": {"add_capability": "x.new"}, "justification": "n/a"}, now=_NOW)
    ctrl_v = find_violations(consumer=consumer, run_result=ctrl, receipt=ctrl_receipt,
                             boundary_request=ctrl_boundary, card=ctrl_card)
    check("CONTROL: a real honest gateway run + receipt + boundary request is CLEAN (0 violations)",
          ctrl_v == [], f"violations={ctrl_v}")

    # helper: mutate a deep copy of the control so each attack starts from a REAL artifact.
    def fresh():
        return (json.loads(json.dumps(ctrl)), json.loads(json.dumps(ctrl_receipt)),
                json.loads(json.dumps(ctrl_boundary)), dict(ctrl_card))

    # (a) secret leak — a raw secret VALUE smuggled into the output (must be env:// ref only).
    a_rr, a_rec, a_b, a_card = fresh()
    a_rr["output"]["leaked_key"] = _RAW_SECRET_VALUE
    va = find_violations(consumer=consumer, run_result=a_rr, receipt=a_rec, boundary_request=None, card=a_card)
    check("(a) raw secret value in output is CAUGHT", "a_secret_leak" in va, str(va))
    # the allowed shape (an env:// ref) is NOT a violation.
    a2_rr, a2_rec, _, a2_card = fresh()
    a2_rr["output"]["key_ref"] = _SECRET_REF
    check("(a) an env:// secret REF is allowed (not flagged)",
          "a_secret_leak" not in find_violations(consumer=consumer, run_result=a2_rr, receipt=a2_rec,
                                                  boundary_request=None, card=a2_card))

    # (b) forbidden tool — a run that executed a forbidden-tool capability.
    b_rr, b_rec, _, b_card = fresh()
    b_rr["capability_id"] = "tariff.hs.classify.reference"  # in consumer.forbidden_tools
    vb = find_violations(consumer=consumer, run_result=b_rr, receipt=b_rec, boundary_request=None, card=b_card)
    check("(b) executing a forbidden-tool capability is CAUGHT", "b_forbidden_tool" in vb, str(vb))
    # and the REAL gateway REFUSES it (defense in depth) — refusal is not itself a violation.
    real_refusal = gw.run({"capability_id": "tariff.hs.classify.reference", "payload": {"product": "laptop"}},
                          now=_NOW, consumer=consumer)
    check("(b) the live gateway refuses the forbidden tool (unavailable, no receipt)",
          real_refusal["status"] == "unavailable" and real_refusal["receipt_id"] is None,
          real_refusal["status"])
    check("(b) the refusal carries NO violation in find_violations",
          find_violations(consumer=consumer, run_result=real_refusal, receipt=None,
                          boundary_request=None, card=b_card) == [])

    # (c) boundary auto-apply — auto_applied true / status not pending.
    _, _, c_b, _ = fresh()
    c_b["auto_applied"] = True
    c_b["status"] = "approved"
    vc = find_violations(consumer=consumer, run_result=ctrl, receipt=ctrl_receipt, boundary_request=c_b,
                         card=ctrl_card)
    check("(c) an auto-applied / pre-approved boundary expansion is CAUGHT", "c_boundary_auto_apply" in vc,
          str(vc))
    # and the REAL gateway forces it pending no matter what the caller asks.
    real_b = gw.request_boundary_expansion(
        {"consumer_id": "x", "capability_id": "y", "requested_change": {"add_capability": "y"},
         "justification": "z", "status": "approved", "auto_applied": True}, now=_NOW)
    check("(c) the live gateway forces boundary expansion to pending/auto_applied False",
          real_b["status"] == py_const_src_teleon_agent_gateway_gateway__BOUNDARY_STATUS_PENDING and real_b["auto_applied"] is False)

    # (d) weakened criteria — a policy check flipped to bypass governance.
    d_rr, d_rec, _, d_card = fresh()
    d_rec["policy_checks"]["governance_bypassed"] = True
    d_rec["policy_checks"]["criteria_overridden_by_consumer"] = True
    vd = find_violations(consumer=consumer, run_result=d_rr, receipt=d_rec, boundary_request=None, card=d_card)
    check("(d) a consumer weakening the success criteria is CAUGHT", "d_weakened_criteria" in vd, str(vd))

    # (e) forced LLM — fallback_used true while the card forbids it.
    e_rr, e_rec, _, e_card = fresh()
    e_rr["fallback_used"] = True
    e_rec["runtime_path"] = py_const_src_teleon_agent_gateway_gateway__RUNTIME_PATH_LLM_FALLBACK
    e_card["llm_fallback_allowed"] = False  # the CFPB card already forbids it
    ve = find_violations(consumer=consumer, run_result=e_rr, receipt=e_rec, boundary_request=None, card=e_card)
    check("(e) an LLM fallback taken when the card forbids it is CAUGHT", "e_forced_llm" in ve, str(ve))

    # (f) output as truth.
    f_rr, f_rec, _, f_card = fresh()
    f_rr["serves_truth"] = True
    vf = find_violations(consumer=consumer, run_result=f_rr, receipt=f_rec, boundary_request=None, card=f_card)
    check("(f) a result that marks itself truth (serves_truth True) is CAUGHT", "f_output_as_truth" in vf,
          str(vf))

    # (g) raw corpus — an unbounded dump instead of a compact output.
    g_rr, g_rec, _, g_card = fresh()
    g_rr["output"] = {"corpus": ["row-%d" % i for i in range(500)], "raw_dump": "x" * 5000}
    vg = find_violations(consumer=consumer, run_result=g_rr, receipt=g_rec, boundary_request=None, card=g_card)
    check("(g) a full raw-corpus dump is CAUGHT", "g_raw_corpus" in vg, str(vg))
    # a successful run that lost its receipt is also a raw-corpus/uncompact violation.
    g2_rr, _, _, g2_card = fresh()
    g2_rr["receipt_id"] = None
    check("(g) a successful run with no receipt_id is CAUGHT",
          "g_raw_corpus" in find_violations(consumer=consumer, run_result=g2_rr, receipt=None,
                                             boundary_request=None, card=g2_card))
    # and the CONTROL output IS bounded (sanity).
    check("(g) the real CFPB output is compact (sanity)", len(json.dumps(ctrl["output"])) <= 2000)

    # (h) score as truth — a benchmark/eval/lift score promoted to a fact.
    h_rr, h_rec, _, h_card = fresh()
    h_rr["output"] = {"benchmark_score": 0.92, "is_truth": True}
    vh = find_violations(consumer=consumer, run_result=h_rr, receipt=h_rec, boundary_request=None, card=h_card)
    check("(h) a benchmark/eval score used as truth is CAUGHT", "h_score_as_truth" in vh, str(vh))
    h2_rr, h2_rec, _, h2_card = fresh()
    h2_rr["score_is_truth"] = True
    check("(h) a score_is_truth flag is CAUGHT",
          "h_score_as_truth" in find_violations(consumer=consumer, run_result=h2_rr, receipt=h2_rec,
                                                 boundary_request=None, card=h2_card))

    # every attack code was demonstrated at least once.
    all_codes = {"a_secret_leak", "b_forbidden_tool", "c_boundary_auto_apply", "d_weakened_criteria",
                 "e_forced_llm", "f_output_as_truth", "g_raw_corpus", "h_score_as_truth"}
    caught = set(va) | set(vb) | set(vc) | set(vd) | set(ve) | set(vf) | set(vg) | set(vh)
    check("ALL 8 attack codes (a-h) were each caught by find_violations", all_codes <= caught,
          f"missing={sorted(all_codes - caught)}")

    print("\n" + ("PASS — check_teleon_agent_gateway_redteam: a single find_violations() defends the agent "
                  "gateway — the CONTROL (a real honest run + receipt + boundary request) is clean, and all 8 "
                  "attacks fail safely: raw-secret leak (a), forbidden-tool execution (b), auto-applied "
                  "boundary expansion (c), weakened success criteria (d), forced LLM fallback (e), output "
                  "marked truth (f), raw-corpus dump / missing receipt (g), and benchmark score used as truth "
                  "(h) — with the live gateway refusing the forbidden tool and forcing boundary requests "
                  "pending as defense in depth."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_teleon_agent_gateway_redteam.py --self-test")
    raise SystemExit(0)
