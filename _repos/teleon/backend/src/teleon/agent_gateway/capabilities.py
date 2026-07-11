"""src.teleon.agent_gateway.capabilities — the LOCAL, DETERMINISTIC capability cards + handlers.

This module is the gateway's catalog: a SMALL set (~5, not 300) of stable, receipt-backed capabilities an
agent calls instead of burning tokens. Each entry is a ``(card, handler)`` pair where:

* the **card** is an :class:`~src.teleon.agent_gateway.gateway.AgentCapabilityCard`-shaped dict (the public
  contract the agent sees — purpose, input/output contract, allowed/forbidden use, expected cost/latency,
  freshness policy, ``deterministic_first=True``, ``llm_fallback_allowed`` flag, ``receipt_required``);
* the **handler** is a pure, deterministic, OFFLINE function ``handler(request_payload, *, now) -> dict`` that
  returns a COMPACT result body: ``{output, source_handles, held_out, tokens_saved_estimate, [detail]}``. It
  NEVER calls a model, the network, or the disk for secrets; it NEVER dumps a raw corpus.

The CFPB capability reuses the Teleon-infra governed environment
(:mod:`src.teleon.environments.baltor_cfpb_context_governance`) — it returns the authoritative "10 business
days" value, the source handle, AND the held-out "30 days" contradiction held SEPARATELY. Teleon returns that
as EVIDENCE (``serves_truth=False`` at the gateway); Baltor's rail is what governs it as truth.

The ``context.governed_answer.evidence`` capability makes that TRUTH BOUNDARY explicit. Given a governed-context
question it returns a compact candidate answer that is plainly marked EVIDENCE, not served truth: it carries a
real ``source_handle``, holds the contradicting/stale claim SEPARATELY in ``held_out`` (never blended into the
answer), and stamps a ``governance`` marker on the body — ``served_truth_owner='baltor'``,
``teleon_role='evidence_only'``, ``requires_baltor_governance=True``. Teleon PRODUCES the evidence; Baltor's rail
DISPOSES of it as served truth. It reuses the CFPB governed fixture and a second inline governed fixture (a
synthetic GDPR Art. 33 breach-notification deadline, with its own stale held-out claim) so the answer always
carries a genuine source handle plus a held-out contradiction; it NEVER imports ``src.baltor``.

Stdlib only; deterministic when ``now`` is injected; offline; never imports ``src.baltor``.
"""
from __future__ import annotations

from typing import Any, Callable

from src.teleon.environments.baltor_cfpb_context_governance import (
    AUTHORITATIVE_ANSWER,
    AUTHORITATIVE_SOURCE_HANDLE,
    HELD_OUT_CONTRADICTION,
    load_fixture,
)
from src.teleon.experiments.ids import sha256_hex

#: every handler here is deterministic-first (no model on the hot path) — the single source for the flag the
#: cards carry and the proofs assert.
py_const_src_teleon_agent_gateway_capabilities__DETERMINISTIC_FIRST = True

#: a deterministic reference HS-code table (a tiny synthetic stub, NOT a live customs feed). Keyed by a
#: lower-cased product keyword → (hs_code, description, source_handle). The handler does an exact keyword
#: lookup only — no model, no inference, no network. Unknown keywords return an honest "no_match".
py_var_src_teleon_agent_gateway_capabilities___HS_REFERENCE_TABLE: dict[str, tuple[str, str, str]] = {
    "laptop": ("8471.30", "Portable automatic data-processing machines, <= 10 kg",
               "ref://hs-reference/8471.30#portable-adp"),
    "smartphone": ("8517.13", "Smartphones",
                   "ref://hs-reference/8517.13#smartphones"),
    "coffee": ("0901.21", "Coffee, roasted, not decaffeinated",
               "ref://hs-reference/0901.21#coffee-roasted"),
    "t-shirt": ("6109.10", "T-shirts, singlets and other vests, knitted, of cotton",
                "ref://hs-reference/6109.10#cotton-tshirt"),
}

#: the governance marker stamped on every ``context.governed_answer.evidence`` body — THE truth-boundary
#: contract, single-sourced here so the handler and the proof read one definition. It says, in data: Teleon
#: returns EVIDENCE ONLY and Baltor owns served truth (the evidence is not finalised until Baltor's rail
#: governs it). ``serves_truth`` stays False everywhere; this marker names WHO governs the eventual truth.
py_const_src_teleon_agent_gateway_capabilities__TELEON_ROLE_EVIDENCE_ONLY = "evidence_only"
py_const_src_teleon_agent_gateway_capabilities__SERVED_TRUTH_OWNER_BALTOR = "baltor"
py_const_src_teleon_agent_gateway_capabilities__GOVERNANCE_MARKER: dict[str, Any] = {
    "served_truth_owner": py_const_src_teleon_agent_gateway_capabilities__SERVED_TRUTH_OWNER_BALTOR,   # Baltor's rail is what governs the eventual served truth
    "teleon_role": py_const_src_teleon_agent_gateway_capabilities__TELEON_ROLE_EVIDENCE_ONLY,          # Teleon only PRODUCES evidence; it never serves truth
    "requires_baltor_governance": True,                # the candidate is not finalised until Baltor governs it
}

#: a SECOND inline governed fixture (synthetic, deterministic, NOT a live feed) so the governed-answer capability
#: is genuinely topic-routed evidence, not a CFPB alias. A GDPR Art. 33 breach-notification deadline: the
#: authoritative value is "72 hours"; a stale internal wiki claim says "30 days" — held out, never served. Each
#: entry: keyword(s) -> {question, authoritative_answer, source_handle, held_out_value, held_out_reason, note}.
py_var_src_teleon_agent_gateway_capabilities___GDPR_BREACH_FIXTURE: dict[str, Any] = {
    "topic": "gdpr.breach_notification",
    "question": "Under GDPR Article 33, within how long must a controller notify the supervisory authority of a "
                "personal-data breach (where feasible)?",
    "authoritative_answer": "72 hours",
    "source_handle": "ctx://gdpr-sample/regs/GDPR-Art33-breach-notification.md#decision",
    "held_out_value": "30 days",
    "held_out_reason": "stale internal wiki note; superseded by GDPR Art. 33 (72-hour authority notification)",
    "note": "Notify the supervisory authority without undue delay and, where feasible, within 72 hours of "
            "becoming aware; affected data subjects are informed separately without undue delay.",
}


def py_function_src_teleon_agent_gateway_capabilities___bounded(py_arg_src_teleon_agent_gateway_capabilities__py_function_src_teleon_agent_gateway_capabilities__bounded__value: Any, *, py_arg_src_teleon_agent_gateway_capabilities__py_function_src_teleon_agent_gateway_capabilities__bounded__limit: int = 512) -> Any:
    """Return ``value`` if it is small; otherwise a bounded marker. Keeps a handler's output COMPACT — a
    capability returns a receipt-backed answer, never a raw-corpus dump. Strings are truncated with a marker;
    over-long containers are summarised by length (never inlined)."""
    if isinstance(py_arg_src_teleon_agent_gateway_capabilities__py_function_src_teleon_agent_gateway_capabilities__bounded__value, str):
        return py_arg_src_teleon_agent_gateway_capabilities__py_function_src_teleon_agent_gateway_capabilities__bounded__value if len(py_arg_src_teleon_agent_gateway_capabilities__py_function_src_teleon_agent_gateway_capabilities__bounded__value) <= py_arg_src_teleon_agent_gateway_capabilities__py_function_src_teleon_agent_gateway_capabilities__bounded__limit else py_arg_src_teleon_agent_gateway_capabilities__py_function_src_teleon_agent_gateway_capabilities__bounded__value[:py_arg_src_teleon_agent_gateway_capabilities__py_function_src_teleon_agent_gateway_capabilities__bounded__limit] + f"…[+{len(py_arg_src_teleon_agent_gateway_capabilities__py_function_src_teleon_agent_gateway_capabilities__bounded__value) - py_arg_src_teleon_agent_gateway_capabilities__py_function_src_teleon_agent_gateway_capabilities__bounded__limit} chars omitted]"
    if isinstance(py_arg_src_teleon_agent_gateway_capabilities__py_function_src_teleon_agent_gateway_capabilities__bounded__value, (list, tuple, dict)) and len(py_arg_src_teleon_agent_gateway_capabilities__py_function_src_teleon_agent_gateway_capabilities__bounded__value) > 64:
        return {"_bounded": True, "kind": type(py_arg_src_teleon_agent_gateway_capabilities__py_function_src_teleon_agent_gateway_capabilities__bounded__value).__name__, "len": len(py_arg_src_teleon_agent_gateway_capabilities__py_function_src_teleon_agent_gateway_capabilities__bounded__value)}
    return py_arg_src_teleon_agent_gateway_capabilities__py_function_src_teleon_agent_gateway_capabilities__bounded__value


# --------------------------------------------------------------------------------------------------------- #
# Handlers — pure, deterministic, offline. Signature: handler(payload, *, now) -> compact result body.
# --------------------------------------------------------------------------------------------------------- #
def py_function_src_teleon_agent_gateway_capabilities___handle_utility_hash(py_arg_src_teleon_agent_gateway_capabilities__py_function_src_teleon_agent_gateway_capabilities__handle_utility_hash__payload: dict, *, now: str) -> dict:
    """``utility.hash`` — return the canonical sha256 of ``payload['payload']`` (or the whole payload). Pure;
    the same payload always hashes identically (``now`` is recorded for the receipt but does not change the
    digest — a hash is content-addressed, not time-addressed)."""
    py_local_src_teleon_agent_gateway_capabilities__handle_utility_hash__subject = py_arg_src_teleon_agent_gateway_capabilities__py_function_src_teleon_agent_gateway_capabilities__handle_utility_hash__payload.get("payload", py_arg_src_teleon_agent_gateway_capabilities__py_function_src_teleon_agent_gateway_capabilities__handle_utility_hash__payload)
    py_local_src_teleon_agent_gateway_capabilities__handle_utility_hash__digest = sha256_hex(py_local_src_teleon_agent_gateway_capabilities__handle_utility_hash__subject)
    return {
        "output": {"sha256": py_local_src_teleon_agent_gateway_capabilities__handle_utility_hash__digest, "algorithm": "sha256"},
        "source_handles": [],
        "held_out": [],
        "tokens_saved_estimate": 40,
        "detail": {"hashed": "payload" if "payload" in py_arg_src_teleon_agent_gateway_capabilities__py_function_src_teleon_agent_gateway_capabilities__handle_utility_hash__payload else "whole_request_payload"},
    }


def py_function_src_teleon_agent_gateway_capabilities___handle_cfpb_deadline_verify(py_arg_src_teleon_agent_gateway_capabilities__py_function_src_teleon_agent_gateway_capabilities__handle_cfpb_deadline_verify__payload: dict, *, now: str) -> dict:
    """``cfpb.deadline.verify`` — return the authoritative Reg E §1005.11 EFT-error resolution deadline as
    EVIDENCE, reusing the Teleon-infra governed fixture. The compact body carries the authoritative value
    ("10 business days") + its source handle, and holds the stale contradiction ("30 days") SEPARATELY in
    ``held_out`` (surfaced, never blended into the answer). serves_truth is pinned False at the gateway —
    Baltor's governance rail is what governs this as truth."""
    py_local_src_teleon_agent_gateway_capabilities__handle_cfpb_deadline_verify__fx = load_fixture()
    return {
        "output": {
            "question": py_function_src_teleon_agent_gateway_capabilities___bounded(py_local_src_teleon_agent_gateway_capabilities__handle_cfpb_deadline_verify__fx["question"]),
            "answer": py_local_src_teleon_agent_gateway_capabilities__handle_cfpb_deadline_verify__fx["authoritative_answer"],          # the authoritative value, returned as evidence
            "regulation": "Reg E §1005.11",
            "note": "10 business days to investigate/resolve; extendable to 45 calendar days with "
                    "provisional credit.",
        },
        "source_handles": [py_local_src_teleon_agent_gateway_capabilities__handle_cfpb_deadline_verify__fx["source_handle"]],
        # the stale contradiction is HELD OUT and surfaced separately — never served as the answer.
        "held_out": [{"value": py_local_src_teleon_agent_gateway_capabilities__handle_cfpb_deadline_verify__fx["held_out_contradiction"], "reason": "stale FAQ; superseded by Reg E"}],
        "tokens_saved_estimate": 1200,
        "detail": {"governed_by": "baltor", "evidence_only": True},
    }


def py_function_src_teleon_agent_gateway_capabilities___handle_json_schema_validate(py_arg_src_teleon_agent_gateway_capabilities__py_function_src_teleon_agent_gateway_capabilities__handle_json_schema_validate__payload: dict, *, now: str) -> dict:
    """``json.schema.validate`` — a deterministic REQUIRED-KEYS check (a tiny offline validator, not a full
    JSON-Schema engine). ``payload['document']`` is the object under test; ``payload['required']`` is the list
    of keys it must contain. Returns ``valid`` + the list of missing keys (bounded)."""
    py_local_src_teleon_agent_gateway_capabilities__handle_json_schema_validate__document = py_arg_src_teleon_agent_gateway_capabilities__py_function_src_teleon_agent_gateway_capabilities__handle_json_schema_validate__payload.get("document", {})
    py_local_src_teleon_agent_gateway_capabilities__handle_json_schema_validate__required = py_arg_src_teleon_agent_gateway_capabilities__py_function_src_teleon_agent_gateway_capabilities__handle_json_schema_validate__payload.get("required", [])
    if not isinstance(py_local_src_teleon_agent_gateway_capabilities__handle_json_schema_validate__document, dict):
        return {
            "output": {"valid": False, "error": "document is not an object", "missing": []},
            "source_handles": [], "held_out": [], "tokens_saved_estimate": 30,
        }
    py_local_src_teleon_agent_gateway_capabilities__handle_json_schema_validate__missing = [k for k in py_local_src_teleon_agent_gateway_capabilities__handle_json_schema_validate__required if k not in py_local_src_teleon_agent_gateway_capabilities__handle_json_schema_validate__document]
    return {
        "output": {"valid": not py_local_src_teleon_agent_gateway_capabilities__handle_json_schema_validate__missing, "missing": py_function_src_teleon_agent_gateway_capabilities___bounded(py_local_src_teleon_agent_gateway_capabilities__handle_json_schema_validate__missing), "checked_keys": py_function_src_teleon_agent_gateway_capabilities___bounded(list(py_local_src_teleon_agent_gateway_capabilities__handle_json_schema_validate__required))},
        "source_handles": [],
        "held_out": [],
        "tokens_saved_estimate": 60,
        "detail": {"required_count": len(py_local_src_teleon_agent_gateway_capabilities__handle_json_schema_validate__required), "missing_count": len(py_local_src_teleon_agent_gateway_capabilities__handle_json_schema_validate__missing)},
    }


def py_function_src_teleon_agent_gateway_capabilities___handle_tariff_hs_classify_reference(py_arg_src_teleon_agent_gateway_capabilities__py_function_src_teleon_agent_gateway_capabilities__handle_tariff_hs_classify_reference__payload: dict, *, now: str) -> dict:
    """``tariff.hs.classify.reference`` — a DETERMINISTIC reference-table lookup (a synthetic stub, NOT a live
    customs classification). ``payload['product']`` is matched (lower-cased, exact keyword) against the
    reference table. A hit returns the HS code + description + a ``ref://`` source handle; a miss returns an
    honest ``no_match`` (it never guesses — guessing would require a model, which this rung forbids)."""
    py_local_src_teleon_agent_gateway_capabilities__handle_tariff_hs_classify_reference__product = str(py_arg_src_teleon_agent_gateway_capabilities__py_function_src_teleon_agent_gateway_capabilities__handle_tariff_hs_classify_reference__payload.get("product", "")).strip().lower()
    py_local_src_teleon_agent_gateway_capabilities__handle_tariff_hs_classify_reference__hit = py_var_src_teleon_agent_gateway_capabilities___HS_REFERENCE_TABLE.get(py_local_src_teleon_agent_gateway_capabilities__handle_tariff_hs_classify_reference__product)
    if py_local_src_teleon_agent_gateway_capabilities__handle_tariff_hs_classify_reference__hit is None:
        return {
            "output": {"matched": False, "product": py_function_src_teleon_agent_gateway_capabilities___bounded(py_local_src_teleon_agent_gateway_capabilities__handle_tariff_hs_classify_reference__product), "hs_code": None,
                       "note": "no exact reference-table match; classification not guessed"},
            "source_handles": [],
            "held_out": [],
            "tokens_saved_estimate": 25,
            "detail": {"table": "hs-reference-stub", "known_products": sorted(py_var_src_teleon_agent_gateway_capabilities___HS_REFERENCE_TABLE)},
        }
    py_local_src_teleon_agent_gateway_capabilities__handle_tariff_hs_classify_reference__hs_code, py_local_src_teleon_agent_gateway_capabilities__handle_tariff_hs_classify_reference__description, py_local_src_teleon_agent_gateway_capabilities__handle_tariff_hs_classify_reference__source_handle = py_local_src_teleon_agent_gateway_capabilities__handle_tariff_hs_classify_reference__hit
    return {
        "output": {"matched": True, "product": py_function_src_teleon_agent_gateway_capabilities___bounded(py_local_src_teleon_agent_gateway_capabilities__handle_tariff_hs_classify_reference__product), "hs_code": py_local_src_teleon_agent_gateway_capabilities__handle_tariff_hs_classify_reference__hs_code,
                   "description": py_local_src_teleon_agent_gateway_capabilities__handle_tariff_hs_classify_reference__description},
        "source_handles": [py_local_src_teleon_agent_gateway_capabilities__handle_tariff_hs_classify_reference__source_handle],
        "held_out": [],
        "tokens_saved_estimate": 90,
        "detail": {"table": "hs-reference-stub"},
    }


def py_function_src_teleon_agent_gateway_capabilities___resolve_governed_fixture(py_arg_src_teleon_agent_gateway_capabilities__py_function_src_teleon_agent_gateway_capabilities__resolve_governed_fixture__question: str) -> dict:
    """Pick the governed fixture for ``question`` and normalise it to a single shape
    ``{topic, question, answer, source_handle, held_out_value, held_out_reason, note}``. GDPR keywords route to
    the inline GDPR Art. 33 fixture; everything else DEFAULTS to the reused CFPB governed fixture (Reg E
    §1005.11). Pure deterministic keyword routing — no model, no network."""
    py_local_src_teleon_agent_gateway_capabilities__resolve_governed_fixture__q = py_arg_src_teleon_agent_gateway_capabilities__py_function_src_teleon_agent_gateway_capabilities__resolve_governed_fixture__question.lower()
    if "gdpr" in py_local_src_teleon_agent_gateway_capabilities__resolve_governed_fixture__q or "breach" in py_local_src_teleon_agent_gateway_capabilities__resolve_governed_fixture__q or "article 33" in py_local_src_teleon_agent_gateway_capabilities__resolve_governed_fixture__q or "art. 33" in py_local_src_teleon_agent_gateway_capabilities__resolve_governed_fixture__q or "art 33" in py_local_src_teleon_agent_gateway_capabilities__resolve_governed_fixture__q:
        py_local_src_teleon_agent_gateway_capabilities__resolve_governed_fixture__fx = py_var_src_teleon_agent_gateway_capabilities___GDPR_BREACH_FIXTURE
        return {
            "topic": py_local_src_teleon_agent_gateway_capabilities__resolve_governed_fixture__fx["topic"], "question": py_local_src_teleon_agent_gateway_capabilities__resolve_governed_fixture__fx["question"], "answer": py_local_src_teleon_agent_gateway_capabilities__resolve_governed_fixture__fx["authoritative_answer"],
            "source_handle": py_local_src_teleon_agent_gateway_capabilities__resolve_governed_fixture__fx["source_handle"], "held_out_value": py_local_src_teleon_agent_gateway_capabilities__resolve_governed_fixture__fx["held_out_value"],
            "held_out_reason": py_local_src_teleon_agent_gateway_capabilities__resolve_governed_fixture__fx["held_out_reason"], "note": py_local_src_teleon_agent_gateway_capabilities__resolve_governed_fixture__fx["note"],
            "regulation": "GDPR Art. 33",
        }
    # default: reuse the CFPB governed fixture (Reg E §1005.11) — the same planted seed the CFPB capability uses.
    py_local_src_teleon_agent_gateway_capabilities__resolve_governed_fixture__cf = load_fixture()
    return {
        "topic": "cfpb.regE.error_resolution_deadline", "question": py_local_src_teleon_agent_gateway_capabilities__resolve_governed_fixture__cf["question"],
        "answer": py_local_src_teleon_agent_gateway_capabilities__resolve_governed_fixture__cf["authoritative_answer"], "source_handle": py_local_src_teleon_agent_gateway_capabilities__resolve_governed_fixture__cf["source_handle"],
        "held_out_value": py_local_src_teleon_agent_gateway_capabilities__resolve_governed_fixture__cf["held_out_contradiction"],
        "held_out_reason": "stale FAQ; superseded by Reg E §1005.11 (10 business days)",
        "note": "10 business days to investigate/resolve; extendable to 45 calendar days with provisional "
                "credit.",
        "regulation": "Reg E §1005.11",
    }


def py_function_src_teleon_agent_gateway_capabilities___handle_context_governed_answer_evidence(py_arg_src_teleon_agent_gateway_capabilities__py_function_src_teleon_agent_gateway_capabilities__handle_context_governed_answer_evidence__payload: dict, *, now: str) -> dict:
    """``context.governed_answer.evidence`` — answer a governed-context QUESTION as compact EVIDENCE, never as
    served truth. ``payload['question']`` selects a governed fixture (GDPR Art. 33 keywords → the inline GDPR
    fixture; anything else → the reused CFPB Reg E fixture). The body carries:

      * ``output`` — a CANDIDATE answer (``answer`` + ``regulation`` + ``note``) plus the ``governance`` marker
        (:data:`GOVERNANCE_MARKER`: ``served_truth_owner='baltor'``, ``teleon_role='evidence_only'``,
        ``requires_baltor_governance=True``) and an explicit ``serves_truth=False`` and ``status='candidate'``;
      * ``source_handles`` — the authoritative provenance handle (a real ``ctx://`` handle);
      * ``held_out`` — the contradicting/stale claim, kept SEPARATE and NEVER merged into ``answer``.

    Teleon PRODUCES this evidence; Baltor's rail DISPOSES of it as served truth. Pure deterministic fixture
    reuse — no model, no network, no Baltor import. ``now`` is recorded for the receipt only."""
    py_local_src_teleon_agent_gateway_capabilities__handle_context_governed_answer_evidence__question = str(py_arg_src_teleon_agent_gateway_capabilities__py_function_src_teleon_agent_gateway_capabilities__handle_context_governed_answer_evidence__payload.get("question", "")).strip()
    py_local_src_teleon_agent_gateway_capabilities__handle_context_governed_answer_evidence__fx = py_function_src_teleon_agent_gateway_capabilities___resolve_governed_fixture(py_local_src_teleon_agent_gateway_capabilities__handle_context_governed_answer_evidence__question)
    # The held-out claim is its own object, surfaced beside the answer — NEVER concatenated into the answer.
    py_local_src_teleon_agent_gateway_capabilities__handle_context_governed_answer_evidence__held_out = [{"value": py_local_src_teleon_agent_gateway_capabilities__handle_context_governed_answer_evidence__fx["held_out_value"], "reason": py_local_src_teleon_agent_gateway_capabilities__handle_context_governed_answer_evidence__fx["held_out_reason"], "served": False}]
    return {
        "output": {
            "question": py_function_src_teleon_agent_gateway_capabilities___bounded(py_local_src_teleon_agent_gateway_capabilities__handle_context_governed_answer_evidence__fx["question"]),
            "answer": py_local_src_teleon_agent_gateway_capabilities__handle_context_governed_answer_evidence__fx["answer"],            # the CANDIDATE authoritative value, returned as evidence only
            "regulation": py_local_src_teleon_agent_gateway_capabilities__handle_context_governed_answer_evidence__fx["regulation"],
            "note": py_function_src_teleon_agent_gateway_capabilities___bounded(py_local_src_teleon_agent_gateway_capabilities__handle_context_governed_answer_evidence__fx["note"]),
            "topic": py_local_src_teleon_agent_gateway_capabilities__handle_context_governed_answer_evidence__fx["topic"],
            # explicit, machine-readable truth-boundary markers ON the agent-visible body:
            "serves_truth": False,             # this capability NEVER marks anything as final served truth
            "status": "candidate",             # Teleon returns a candidate/evidence, not a finalised truth
            "governance": dict(py_const_src_teleon_agent_gateway_capabilities__GOVERNANCE_MARKER),  # WHO governs the eventual served truth (Baltor), Teleon=evidence
        },
        "source_handles": [py_local_src_teleon_agent_gateway_capabilities__handle_context_governed_answer_evidence__fx["source_handle"]],
        "held_out": py_local_src_teleon_agent_gateway_capabilities__handle_context_governed_answer_evidence__held_out,                  # the contradiction, held SEPARATELY (never inside `answer`)
        "tokens_saved_estimate": 1400,
        "detail": {"governed_by": py_const_src_teleon_agent_gateway_capabilities__SERVED_TRUTH_OWNER_BALTOR, "teleon_role": py_const_src_teleon_agent_gateway_capabilities__TELEON_ROLE_EVIDENCE_ONLY,
                   "fixture_topic": py_local_src_teleon_agent_gateway_capabilities__handle_context_governed_answer_evidence__fx["topic"]},
    }


# --------------------------------------------------------------------------------------------------------- #
# Capability cards — the public contracts. Field names match AgentCapabilityCard EXACTLY.
# --------------------------------------------------------------------------------------------------------- #
def py_function_src_teleon_agent_gateway_capabilities___card(py_arg_src_teleon_agent_gateway_capabilities__py_function_src_teleon_agent_gateway_capabilities__card__capability_id: str, *, purpose: str, input_contract: dict, output_contract: dict,
          allowed_use: list[str], forbidden_use: list[str], expected_cost: dict, expected_latency: dict,
          freshness_policy: dict, policy_notes: str, py_arg_src_teleon_agent_gateway_capabilities__py_function_src_teleon_agent_gateway_capabilities__card__llm_fallback_allowed: bool = False) -> dict:
    """Build an AgentCapabilityCard-shaped dict. ``deterministic_first`` and ``receipt_required`` are pinned
    True for every local capability (the contract the proofs assert); ``llm_fallback_allowed`` defaults False
    (these rungs never need a model — the agent cannot force one)."""
    return {
        "capability_id": py_arg_src_teleon_agent_gateway_capabilities__py_function_src_teleon_agent_gateway_capabilities__card__capability_id,
        "purpose": purpose,
        "input_contract": input_contract,
        "output_contract": output_contract,
        "allowed_use": list(allowed_use),
        "forbidden_use": list(forbidden_use),
        "expected_cost": dict(expected_cost),
        "expected_latency": dict(expected_latency),
        "freshness_policy": dict(freshness_policy),
        "policy_notes": policy_notes,
        "deterministic_first": py_const_src_teleon_agent_gateway_capabilities__DETERMINISTIC_FIRST,
        "llm_fallback_allowed": bool(py_arg_src_teleon_agent_gateway_capabilities__py_function_src_teleon_agent_gateway_capabilities__card__llm_fallback_allowed),
        "receipt_required": True,
    }


#: the capability registry: capability_id -> {"card": <dict>, "handler": <callable>}. The SINGLE source of the
#: gateway's catalog (list/describe/quote/run all read this). Small + stable on purpose (~5, not 300).
py_const_src_teleon_agent_gateway_capabilities__CAPABILITIES: dict[str, dict[str, Any]] = {
    "utility.hash": {
        "card": py_function_src_teleon_agent_gateway_capabilities___card(
            "utility.hash",
            purpose="Return the canonical sha256 of an arbitrary JSON payload (stable content address).",
            input_contract={"payload": "any JSON-serialisable value (or wrap under key 'payload')"},
            output_contract={"sha256": "hex string", "algorithm": "const 'sha256'"},
            allowed_use=["content-addressing", "dedupe keys", "cache keys", "integrity checks"],
            forbidden_use=["treating the digest as a secret", "password hashing (use a KDF)"],
            expected_cost={"tier": "deterministic", "usd": 0.0, "tokens": 0},
            expected_latency={"tier": "deterministic", "p95_ms": 1},
            freshness_policy={"kind": "pure", "ttl_s": None, "note": "content-addressed; never stale"},
            policy_notes="pure deterministic stdlib hash; no model, no network, no secrets.",
        ),
        "handler": py_function_src_teleon_agent_gateway_capabilities___handle_utility_hash,
    },
    "cfpb.deadline.verify": {
        "card": py_function_src_teleon_agent_gateway_capabilities___card(
            "cfpb.deadline.verify",
            purpose="Return the authoritative Reg E §1005.11 EFT-error resolution deadline as receipt-backed "
                    "EVIDENCE, with the stale contradiction held out separately. Baltor governs it as truth.",
            input_contract={"question": "optional free-text (the canonical Reg E question is used)"},
            output_contract={"answer": "authoritative value string", "regulation": "string",
                             "source_handles": "list[str]", "held_out": "list of surfaced contradictions"},
            allowed_use=["compliance drafting support", "citing the authoritative deadline as evidence"],
            forbidden_use=["serving the answer as adjudicated truth without Baltor governance",
                           "serving the held-out '30 days' value", "dumping the raw corpus"],
            expected_cost={"tier": "deterministic", "usd": 0.0, "tokens": 0},
            expected_latency={"tier": "deterministic", "p95_ms": 2},
            freshness_policy={"kind": "governed", "ttl_s": 86400,
                              "note": "Reg E value is governed by Baltor's freshness/CDC rail; held-out "
                                      "contradiction is surfaced, never served."},
            policy_notes="evidence only at the gateway (serves_truth False); Baltor's rail governs truth; "
                         "deterministic fixture reuse — no model, no network.",
        ),
        "handler": py_function_src_teleon_agent_gateway_capabilities___handle_cfpb_deadline_verify,
    },
    "context.governed_answer.evidence": {
        "card": py_function_src_teleon_agent_gateway_capabilities___card(
            "context.governed_answer.evidence",
            purpose="Answer a governed-context question as compact, receipt-backed EVIDENCE (candidate answer + "
                    "real source handle + held-out contradiction held separately). Teleon returns evidence "
                    "ONLY; Baltor's rail governs it as served truth (governance marker on the body).",
            input_contract={"question": "the governed-context question (free text); routes to a governed "
                                        "fixture — GDPR Art. 33 keywords -> GDPR breach fixture, else CFPB Reg E"},
            output_contract={"answer": "candidate authoritative value (evidence, not truth)",
                             "regulation": "string", "serves_truth": "const False",
                             "status": "const 'candidate'",
                             "governance": "{served_truth_owner:'baltor', teleon_role:'evidence_only', "
                                           "requires_baltor_governance:true}",
                             "source_handles": "list[str]", "held_out": "list of surfaced-but-separate "
                                                                        "contradictions (never in the answer)"},
            allowed_use=["compliance/context drafting support", "citing the candidate answer as EVIDENCE",
                         "feeding the evidence + source handle + held-out into Baltor's governance rail"],
            forbidden_use=["serving the answer as adjudicated/served truth without Baltor governance",
                           "serving or blending the held-out contradiction into the answer",
                           "treating Teleon's evidence as final truth", "dumping the raw corpus"],
            expected_cost={"tier": "deterministic", "usd": 0.0, "tokens": 0},
            expected_latency={"tier": "deterministic", "p95_ms": 2},
            freshness_policy={"kind": "governed", "ttl_s": 86400,
                              "note": "the authoritative value is governed by Baltor's freshness/CDC rail; "
                                      "Teleon returns it as candidate evidence, held-out contradiction surfaced "
                                      "separately and never served."},
            policy_notes="EVIDENCE ONLY at the gateway (serves_truth False, status 'candidate'); the governance "
                         "marker names Baltor as the served-truth owner (teleon_role 'evidence_only', "
                         "requires_baltor_governance True); deterministic fixture reuse — no model, no network, "
                         "no src.baltor import.",
        ),
        "handler": py_function_src_teleon_agent_gateway_capabilities___handle_context_governed_answer_evidence,
    },
    "json.schema.validate": {
        "card": py_function_src_teleon_agent_gateway_capabilities___card(
            "json.schema.validate",
            purpose="Deterministically check that a JSON document contains a set of required keys.",
            input_contract={"document": "object under test", "required": "list[str] of required keys"},
            output_contract={"valid": "bool", "missing": "list[str]"},
            allowed_use=["pre-flight payload validation", "contract checks before a downstream call"],
            forbidden_use=["claiming full JSON-Schema conformance (this is a required-keys check only)"],
            expected_cost={"tier": "deterministic", "usd": 0.0, "tokens": 0},
            expected_latency={"tier": "deterministic", "p95_ms": 1},
            freshness_policy={"kind": "pure", "ttl_s": None, "note": "pure function of its inputs"},
            policy_notes="deterministic required-keys validator; no model, no network.",
        ),
        "handler": py_function_src_teleon_agent_gateway_capabilities___handle_json_schema_validate,
    },
    "tariff.hs.classify.reference": {
        "card": py_function_src_teleon_agent_gateway_capabilities___card(
            "tariff.hs.classify.reference",
            purpose="Deterministic reference-table HS-code lookup for a product keyword (synthetic stub).",
            input_contract={"product": "product keyword string"},
            output_contract={"matched": "bool", "hs_code": "string|null", "description": "string"},
            allowed_use=["reference HS lookup", "draft classification support (human/Baltor confirms)"],
            forbidden_use=["binding customs classification", "guessing a code on a miss",
                           "treating the stub table as a live authoritative tariff feed"],
            expected_cost={"tier": "deterministic", "usd": 0.0, "tokens": 0},
            expected_latency={"tier": "deterministic", "p95_ms": 1},
            freshness_policy={"kind": "reference_stub", "ttl_s": None,
                              "note": "synthetic reference table; a live tariff feed would be a governed source"},
            policy_notes="deterministic exact-keyword table lookup; never guesses; no model, no network.",
        ),
        "handler": py_function_src_teleon_agent_gateway_capabilities___handle_tariff_hs_classify_reference,
    },
}


def py_function_src_teleon_agent_gateway_capabilities__capability_ids() -> list[str]:
    """The sorted list of registered capability ids (stable ordering for deterministic listing)."""
    return sorted(py_const_src_teleon_agent_gateway_capabilities__CAPABILITIES)


def py_function_src_teleon_agent_gateway_capabilities__get_card(py_arg_src_teleon_agent_gateway_capabilities__py_function_src_teleon_agent_gateway_capabilities__get_card__capability_id: str) -> dict | None:
    """Return a COPY of the public card dict for ``capability_id`` (or ``None`` if unknown). A copy so a
    caller can never mutate the registry's source-of-truth card."""
    py_local_src_teleon_agent_gateway_capabilities__get_card__entry = py_const_src_teleon_agent_gateway_capabilities__CAPABILITIES.get(py_arg_src_teleon_agent_gateway_capabilities__py_function_src_teleon_agent_gateway_capabilities__get_card__capability_id)
    return dict(py_local_src_teleon_agent_gateway_capabilities__get_card__entry["card"]) if py_local_src_teleon_agent_gateway_capabilities__get_card__entry else None


def py_function_src_teleon_agent_gateway_capabilities__get_handler(py_arg_src_teleon_agent_gateway_capabilities__py_function_src_teleon_agent_gateway_capabilities__get_handler__capability_id: str) -> Callable[..., dict] | None:
    """Return the deterministic handler callable for ``capability_id`` (or ``None`` if unknown)."""
    py_local_src_teleon_agent_gateway_capabilities__get_handler__entry = py_const_src_teleon_agent_gateway_capabilities__CAPABILITIES.get(py_arg_src_teleon_agent_gateway_capabilities__py_function_src_teleon_agent_gateway_capabilities__get_handler__capability_id)
    return py_local_src_teleon_agent_gateway_capabilities__get_handler__entry["handler"] if py_local_src_teleon_agent_gateway_capabilities__get_handler__entry else None


__all__ = [
    "py_const_src_teleon_agent_gateway_capabilities__CAPABILITIES",
    "py_const_src_teleon_agent_gateway_capabilities__DETERMINISTIC_FIRST",
    "py_const_src_teleon_agent_gateway_capabilities__GOVERNANCE_MARKER",
    "py_const_src_teleon_agent_gateway_capabilities__SERVED_TRUTH_OWNER_BALTOR",
    "py_const_src_teleon_agent_gateway_capabilities__TELEON_ROLE_EVIDENCE_ONLY",
    "py_function_src_teleon_agent_gateway_capabilities__capability_ids",
    "py_function_src_teleon_agent_gateway_capabilities__get_card",
    "py_function_src_teleon_agent_gateway_capabilities__get_handler",
]
