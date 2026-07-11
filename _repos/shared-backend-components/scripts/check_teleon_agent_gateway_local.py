#!/usr/bin/env python3
"""scripts.check_teleon_agent_gateway_local — PROOF: the LOCAL Teleon Agent Capability Gateway runs
deterministic, receipt-backed capabilities for AI-agent customers, offline, with agents-ASK / Teleon-EXECUTES
/ Baltor-governs-truth enforced.

Asserts:
  A. CATALOG: the gateway lists >= 4 stable capability cards (~5, not 300); each card carries the P0 contract
     fields, ``deterministic_first=True`` and ``receipt_required=True``.
  B. GOVERNED EVIDENCE (CFPB): an agent consumer runs ``cfpb.deadline.verify`` → status ``verified``; the
     output is COMPACT (bounded); the authoritative value "10 business days" is present; a ``source_handles``
     handle is present; the held-out "30 days" contradiction is present BUT SEPARATE (in ``held_out``, never
     in the served answer); ``tokens_saved_estimate`` > 0; ``serves_truth`` is False.
  C. RECEIPT: the CFPB run wrote a receipt with ``runtime_path == 'deterministic'`` (deterministic-first), a
     backend chosen by the binding delegate, content-addressed input/output hashes, and policy checks.
  D. DETERMINISM: ``utility.hash`` on the same payload + same ``now`` yields the same ``output_hash`` and the
     same (idempotent) receipt id; key-order does not matter (canonical bytes).
  E. BOUNDARY (allow-list): a capability NOT in the consumer's ``allowed_capabilities`` is REFUSED
     (``unavailable``, no receipt) — an agent cannot call outside its boundary.
  F. FORBIDDEN TOOL (deny-list): a capability whose id is in the consumer's ``forbidden_tools`` is REFUSED.
  G. NO SELF-EXPANSION: a boundary-expansion request is ALWAYS ``pending_human_approval`` /
     ``auto_applied=False`` — even when the caller asks for ``status='approved', auto_applied=True``.
  H. NO LLM FORCED: with a card that allows an LLM fallback but no deterministic handler, the agent CANNOT
     force a live model (refused) unless card AND consumer policy AND the owner-gated live switch all agree;
     the self-test never sets the live switch.
  I. DEPENDENCY LAW: no module under _repos/teleon/backend/src/teleon/agent_gateway imports ``src.baltor`` (line-anchored).
  J. NO RAW KEYS: the gateway package contains no raw secret-key value (refs are ``env://`` only).

Deterministic + offline; no network, no live model, no secrets. Exit 0/1.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource  # noqa: E402

import json
import os
import re
import sys
from pathlib import Path

_REPO = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.agent_gateway import capabilities as caps
from src.teleon.agent_gateway.gateway import (
    py_class_src_teleon_agent_gateway_gateway__AgentCapabilityCard,
    py_class_src_teleon_agent_gateway_gateway__AgentCapabilityGateway,
    py_class_src_teleon_agent_gateway_gateway__AgentConsumer,
    py_const_src_teleon_agent_gateway_gateway__RUNTIME_PATH_DETERMINISTIC,
)

_NOW = "2026-06-08T00:00:00Z"  # injected — determinism
_PKG = _resource("src/teleon/agent_gateway")

#: the P0 card contract fields every card must expose.
_CARD_FIELDS = set(py_class_src_teleon_agent_gateway_gateway__AgentCapabilityCard.__dataclass_fields__)
#: a fake provider key assembled FROM FRAGMENTS (never a real literal) — proves the scanner would catch a
#: leaked value but this test plants none in the package.
_FAKE_KEY = "sk-" + "live" + "_" + ("A" * 20)


def _self_test() -> int:
    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    gw = py_class_src_teleon_agent_gateway_gateway__AgentCapabilityGateway()

    # A. catalog -------------------------------------------------------------------------------------------
    cards = gw.list_capabilities()
    check("A: gateway lists >= 4 capability cards", len(cards) >= 4, f"got {len(cards)}")
    check("A: catalog is small/stable (~5, not 300)", len(cards) <= 12, f"got {len(cards)}")
    for c in cards:
        cid = c.get("capability_id", "?")
        check(f"A: {cid} card carries all P0 contract fields", set(c) == _CARD_FIELDS,
              f"diff={set(c) ^ _CARD_FIELDS}")
        check(f"A: {cid} deterministic_first + receipt_required",
              c.get("deterministic_first") is True and c.get("receipt_required") is True)

    # B. governed evidence (CFPB) --------------------------------------------------------------------------
    agent = py_class_src_teleon_agent_gateway_gateway__AgentConsumer(
        consumer_id="agent.compliance-helper",
        allowed_capabilities=frozenset({"cfpb.deadline.verify", "utility.hash", "json.schema.validate"}),
    )
    cfpb = gw.run({"capability_id": "cfpb.deadline.verify", "payload": {}}, now=_NOW, consumer=agent)
    check("B: CFPB run status == verified", cfpb["status"] == "verified", cfpb["status"])
    served_blob = json.dumps(cfpb["output"])
    check("B: CFPB output is compact (bounded)", len(served_blob) <= 2000, f"len={len(served_blob)}")
    check("B: authoritative '10 business days' present in answer",
          "10 business days" in json.dumps(cfpb["output"].get("answer", "")))
    check("B: source_handles present", bool(cfpb["source_handles"]), str(cfpb["source_handles"]))
    held_values = [str(h.get("value", h)) for h in cfpb["held_out"]]
    check("B: held-out '30 days' present BUT SEPARATE (in held_out, not the served answer)",
          any("30 days" in v for v in held_values) and "30 days" not in served_blob,
          f"held={held_values} served_has_30={'30 days' in served_blob}")
    check("B: tokens_saved_estimate > 0", cfpb["tokens_saved_estimate"] > 0, str(cfpb["tokens_saved_estimate"]))
    check("B: serves_truth is False (evidence, not truth)", cfpb["serves_truth"] is False)

    # C. receipt -------------------------------------------------------------------------------------------
    rec = gw.get_receipt(cfpb["receipt_id"])
    check("C: CFPB run wrote a receipt", rec is not None and cfpb["receipt_id"] is not None)
    if rec:
        check("C: receipt runtime_path == 'deterministic'", rec["runtime_path"] == py_const_src_teleon_agent_gateway_gateway__RUNTIME_PATH_DETERMINISTIC,
              rec["runtime_path"])
        check("C: receipt backend chosen by binding delegate", bool(rec["backend"]), str(rec["backend"]))
        check("C: receipt has content-addressed input/output hashes",
              len(rec["input_hash"]) == 64 and len(rec["output_hash"]) == 64)
        check("C: receipt policy_checks recorded (serves_truth False, deterministic_first)",
              rec["policy_checks"]["serves_truth"] is False
              and rec["policy_checks"]["deterministic_first"] is True
              and rec["policy_checks"]["llm_fallback_used"] is False)

    # D. determinism ---------------------------------------------------------------------------------------
    hasher = py_class_src_teleon_agent_gateway_gateway__AgentConsumer(consumer_id="agent.hasher", allowed_capabilities=frozenset({"utility.hash"}))
    r1 = gw.run({"capability_id": "utility.hash", "payload": {"payload": {"a": 1, "b": 2}}},
                now=_NOW, consumer=hasher)
    r2 = gw.run({"capability_id": "utility.hash", "payload": {"payload": {"b": 2, "a": 1}}},
                now=_NOW, consumer=hasher)
    rec1, rec2 = gw.get_receipt(r1["receipt_id"]), gw.get_receipt(r2["receipt_id"])
    check("D: same payload + now -> same output_hash (key-order irrelevant)",
          rec1["output_hash"] == rec2["output_hash"], f'{rec1["output_hash"][:8]} vs {rec2["output_hash"][:8]}')
    check("D: same call -> same (idempotent) receipt id", r1["receipt_id"] == r2["receipt_id"])
    check("D: utility.hash output carries a sha256 + algorithm",
          r1["output"].get("algorithm") == "sha256" and len(r1["output"].get("sha256", "")) == 64)

    # E. boundary (allow-list) -----------------------------------------------------------------------------
    refused = gw.run({"capability_id": "tariff.hs.classify.reference", "payload": {"product": "laptop"}},
                     now=_NOW, consumer=hasher)  # hasher may only call utility.hash
    check("E: capability outside allowed_capabilities is REFUSED (unavailable, no receipt)",
          refused["status"] == "unavailable" and refused["receipt_id"] is None, refused["status"])

    # F. forbidden tool (deny-list) ------------------------------------------------------------------------
    denied_consumer = py_class_src_teleon_agent_gateway_gateway__AgentConsumer(consumer_id="agent.denied",
                                    allowed_capabilities=frozenset({"utility.hash"}),
                                    forbidden_tools=frozenset({"utility.hash"}))
    denied = gw.run({"capability_id": "utility.hash", "payload": {}}, now=_NOW, consumer=denied_consumer)
    check("F: a forbidden-tool capability is REFUSED even if allow-listed",
          denied["status"] == "unavailable" and denied["receipt_id"] is None, denied["status"])

    # G. no self-expansion ---------------------------------------------------------------------------------
    boundary = gw.request_boundary_expansion(
        {"consumer_id": "agent.hasher", "capability_id": "browser.fetch",
         "requested_change": {"add_capability": "browser.fetch"}, "justification": "I want to browse",
         "status": "approved", "auto_applied": True},  # malicious ask
        now=_NOW)
    check("G: boundary-expansion is pending_human_approval (caller cannot pre-approve)",
          boundary["status"] == "pending_human_approval", boundary["status"])
    check("G: boundary-expansion auto_applied is False (NEVER auto-applied)",
          boundary["auto_applied"] is False)
    check("G: boundary-expansion uses schema field names (capability_id/requested_change/justification)",
          boundary.get("capability_id") == "browser.fetch"
          and isinstance(boundary.get("requested_change"), dict)
          and boundary.get("justification") == "I want to browse"
          and "requested_capability" not in boundary and "rationale" not in boundary,
          str(sorted(boundary)))
    # back-compat: the LEGACY field names are still accepted as INPUT aliases (mapped to the schema names).
    legacy = gw.request_boundary_expansion(
        {"consumer_id": "agent.hasher", "requested_capability": "browser.fetch",
         "rationale": "legacy caller"}, now=_NOW)
    check("G: legacy requested_capability/rationale inputs are mapped to schema field names (back-compat)",
          legacy.get("capability_id") == "browser.fetch" and legacy.get("justification") == "legacy caller"
          and legacy["status"] == "pending_human_approval" and legacy["auto_applied"] is False,
          str(sorted(legacy)))

    # H. no LLM forced -------------------------------------------------------------------------------------
    # register a transient card that ALLOWS an llm fallback but has NO deterministic handler.
    llm_only_id = "transient.llm.only.test"
    caps.py_const_src_teleon_agent_gateway_capabilities__CAPABILITIES[llm_only_id] = {
        "card": {**caps.py_function_src_teleon_agent_gateway_capabilities__get_card("utility.hash"), "capability_id": llm_only_id, "llm_fallback_allowed": True,
                 "deterministic_first": True},
        "handler": None,
    }
    try:
        gw2 = py_class_src_teleon_agent_gateway_gateway__AgentCapabilityGateway()
        llm_consumer = py_class_src_teleon_agent_gateway_gateway__AgentConsumer(consumer_id="agent.llm", allowed_capabilities=frozenset({llm_only_id}),
                                     llm_fallback_permitted=True)  # consumer permits — still must not go live
        # agent can NEVER force a live model: the owner-gated live switch is NOT set here.
        forced = gw2.run({"capability_id": llm_only_id, "payload": {}}, now=_NOW, consumer=llm_consumer)
        check("H: agent cannot force a live LLM rung (refused without owner-gated live switch)",
              forced["status"] == "unavailable" and forced["receipt_id"] is None, forced["status"])
        # and a consumer that does NOT permit the fallback is refused regardless.
        no_perm = py_class_src_teleon_agent_gateway_gateway__AgentConsumer(consumer_id="agent.noperm", allowed_capabilities=frozenset({llm_only_id}),
                                llm_fallback_permitted=False)
        forced2 = gw2.run({"capability_id": llm_only_id, "payload": {}}, now=_NOW, consumer=no_perm,
                          allow_live_llm=True)  # even with live switch, consumer policy forbids
        check("H: consumer policy can still forbid the LLM rung",
              forced2["status"] == "unavailable", forced2["status"])
    finally:
        del caps.py_const_src_teleon_agent_gateway_capabilities__CAPABILITIES[llm_only_id]  # leave the registry as we found it

    # I. dependency law ------------------------------------------------------------------------------------
    bad_imports: list[str] = []
    for py in sorted(_PKG.rglob("*.py")):
        for line in py.read_text().splitlines():
            s = line.strip()
            if s.startswith("import src.baltor") or s.startswith("from src.baltor"):
                bad_imports.append(str(py.relative_to(_REPO)))
    check("I: no _repos/teleon/backend/src/teleon/agent_gateway module imports src.baltor (dependency law)",
          not bad_imports, "; ".join(bad_imports))

    # J. no raw keys ---------------------------------------------------------------------------------------
    key_pat = re.compile(r"\bsk-(?:live|proj|ant)[-_][A-Za-z0-9]{12,}")
    leaks: list[str] = []
    for py in sorted(_PKG.rglob("*.py")):
        text = py.read_text()
        if key_pat.search(text):
            leaks.append(str(py.relative_to(_REPO)))
    check("J: gateway package contains no raw secret-key value (env:// refs only)", not leaks,
          "; ".join(leaks))
    # sanity: the scanner WOULD catch a leaked value (the fragment-assembled fake key matches the pattern).
    check("J: leak scanner is wired (matches a fragment-assembled fake key)", bool(key_pat.search(_FAKE_KEY)))

    print("\n" + ("PASS — check_teleon_agent_gateway_local: the local Teleon Agent Capability Gateway runs a "
                  "small stable catalog of deterministic, receipt-backed capabilities for AI-agent customers — "
                  "CFPB returns the authoritative '10 business days' as compact governed EVIDENCE with the "
                  "'30 days' contradiction held out SEPARATELY, every run is deterministic-first + receipted "
                  "(runtime_path 'deterministic'), out-of-boundary/forbidden capabilities are refused, boundary "
                  "expansion is never auto-applied, an agent cannot force a live LLM, serves_truth is False, "
                  "no src.baltor import, no raw keys."
                  if not fails else f"{len(fails)} FAILURES: {fails}"))
    return 0 if not fails else 1


if __name__ == "__main__":
    if "--self-test" in sys.argv:
        raise SystemExit(_self_test())
    print("usage: python3 scripts/check_teleon_agent_gateway_local.py --self-test")
    raise SystemExit(0)
