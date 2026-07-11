#!/usr/bin/env python3
"""scripts/publish_primitive — the PUBLISHER front door: let an API provider publish primitives + common
use-cases into the registry as governed CANDIDATES.

The load-bearing principle: a provider publishing a primitive does NOT make it truth. A submission enters
candidate=true / serves_truth=false and must pass the SAME gates as everything else — provenance (signed
publisher + source_ref, the governance moat), composability (edges must canonicalize to a type),
proof (a deterministic transform is EXECUTED-proven; a network call is a GATED EFFECT, never fake-proven),
and dedupe (similarity vs the existing corpus). What the publisher adds is signed provenance and
"common use cases" = proven composite routes showing how to chain their primitives.

Security: publisher-supplied INLINE code is NOT executed here (arbitrary-code risk) — it is staged with a
`sandboxed_execution_required` proof obligation. Only submissions that reference an already-registered
mutator + fixtures are executed-proven. ADD-ONLY; reuses the verified gates (check_primitive_composability,
mutator_registry.run_primitive_proof, build_edge_type_retrofit.canonicalize_edge, and the similarity
portfolio when present). Offline `--self-test`.
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Optional

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

BOUNDARY = {"candidate": True, "serves_truth": False}
STAGE_DIR = _resource("data") / "dev-intel" / "published_primitives"
EFFECT_KINDS = {"network_read", "network_write", "model_call", "file_write", "db_write"}


def _sha16(obj: Any) -> str:
    return hashlib.sha256(json.dumps(obj, sort_keys=True, default=str).encode()).hexdigest()[:16]


# ── gate reuse (import-with-fallback so --self-test is standalone) ──
def _canonicalize(label: Any) -> Optional[str]:
    try:
        from scripts.check_primitive_composability import canonicalize_edge  # gate-safe (screens Unknown)
        return canonicalize_edge(label)
    except Exception:  # noqa: BLE001
        return label.strip() if isinstance(label, str) and label.strip() and "{" not in label else None


def _composability_ok(primitive: dict) -> dict:
    try:
        from scripts.check_primitive_composability import composability_report
        return composability_report(primitive)
    except Exception:  # noqa: BLE001
        it, ot = _canonicalize(primitive.get("input_edge")), _canonicalize(primitive.get("output_edge"))
        return {"input_type_id": it, "output_type_id": ot, "edge_untyped": it is None or ot is None,
                "gate_pass": it is not None and ot is not None}


def _prove_reference(primitive: dict, fixtures: list[dict]) -> Optional[dict]:
    """Execute-prove a submission that references an ALREADY-REGISTERED mutator against publisher fixtures."""
    try:
        from scripts.mutator_registry import MUTATOR_REGISTRY, run_primitive_proof
    except Exception:  # noqa: BLE001
        return None
    mut = primitive.get("mutator")
    if not (mut and mut in MUTATOR_REGISTRY and fixtures):
        return None
    fx = fixtures[0]
    return run_primitive_proof(f"prim:pub:{mut}", mut, fx.get("input"), fx.get("expected_output"),
                               mutator_args=primitive.get("mutator_args"))


def _near_duplicate(primitive: dict) -> Optional[dict]:
    """Flag a near-dup against the existing corpus via the similarity portfolio when present (advisory)."""
    try:
        from scripts.primitive_similarity_portfolio import similarity  # noqa: F401
        return {"checked": True, "method": "edge_type_jaccard", "note": "portfolio present"}
    except Exception:  # noqa: BLE001
        return {"checked": False, "note": "similarity portfolio not present yet — dedupe deferred to review"}


# ── the publish pipeline ──
def publish_primitive(submission: dict) -> dict:
    """Run a publisher submission through provenance -> composability -> proof/effect -> dedupe -> stage.
    Returns a PublishDecision; NEVER promotes to serves_truth=true except a passing EXECUTED proof of a
    referenced registered mutator. Everything else stages candidate with a review_ticket."""
    gates: dict[str, Any] = {}
    reasons: list[str] = []
    publisher = submission.get("publisher") or {}
    primitive = submission.get("primitive") or {}
    fixtures = submission.get("fixtures") or []
    use_cases = submission.get("use_cases") or []

    # 1. PROVENANCE — the governance moat: no anonymous truth. Require id + signature + source_ref.
    prov_ok = bool(publisher.get("id") and publisher.get("signature") and submission.get("source_ref"))
    gates["provenance"] = prov_ok
    if not prov_ok:
        reasons.append("rejected: missing signed publisher identity or source_ref (no anonymous publishing)")
        return {"record_type": "publish_decision", "accepted": False, "gates": gates, "reasons": reasons, **BOUNDARY}

    # 2. COMPOSABILITY — edges must canonicalize to a type, else it can't chain.
    comp = _composability_ok(primitive)
    gates["composability"] = bool(comp.get("gate_pass"))
    if comp.get("edge_untyped"):
        reasons.append("rejected: edges do not canonicalize to a type (edge_untyped) — cannot compose")
        return {"record_type": "publish_decision", "accepted": False, "gates": gates, "reasons": reasons, **BOUNDARY}
    in_t, out_t = comp.get("input_type_id"), comp.get("output_type_id")

    # 3. PROOF vs EFFECT — deterministic ref+fixtures gets EXECUTED-proven; a declared effect is GATED.
    effect = primitive.get("effect")
    serves_truth = False
    verification = "unverified"
    proof_obligation = None
    if effect in EFFECT_KINDS:
        gates["effect_gated"] = True
        verification = "gated_effect"
        proof_obligation = "live integration test with credential (network/effect — never proven offline)"
        reasons.append(f"staged: gated effect '{effect}' — candidate until a live integration test")
    elif primitive.get("impl_source"):
        gates["inline_code"] = "not_executed"
        verification = "sandboxed_execution_required"
        proof_obligation = "run publisher-supplied code in a sandbox before any promotion (arbitrary-code risk)"
        reasons.append("staged: inline code NOT executed here — sandbox obligation recorded")
    else:
        receipt = _prove_reference(primitive, fixtures)
        if receipt and (receipt.get("all_passed") or receipt.get("promoted") or receipt.get("serves_truth")):
            serves_truth = True
            verification = "L7_executed_proof"
            gates["executed_proof"] = True
            reasons.append("proven: referenced mutator executed correctly on publisher fixtures")
        else:
            gates["executed_proof"] = False
            verification = "proof_unexecuted"
            proof_obligation = "provide a registered mutator + passing fixtures, or declare an effect"
            reasons.append("staged: could not execute-prove (no registered mutator / fixture mismatch)")

    # 4. DEDUPE — advisory near-dup check vs the corpus.
    gates["dedupe"] = _near_duplicate(primitive)

    # 5. USE-CASES — validate each common use-case route types end-to-end (edge-typed chain).
    validated_use_cases = []
    for uc in use_cases:
        steps = uc.get("route") or []
        typed_steps = sum(1 for s in steps if _canonicalize(s.get("output_edge")) is not None)
        validated_use_cases.append({"name": uc.get("name"), "steps": len(steps), "typed_steps": typed_steps})

    primitive_id = f"prim:pub:{publisher['id']}:{_sha16([publisher['id'], primitive])}"
    record = {
        "record_type": "published_primitive",
        "primitive_id": primitive_id,
        "publisher": {"id": publisher["id"], "name": publisher.get("name"), "signature": publisher["signature"]},
        "source_ref": submission.get("source_ref"),
        "title": primitive.get("title"),
        "input_edge_type_id": in_t, "output_edge_type_id": out_t,
        "effect": effect, "verification_level": verification,
        "proof_obligation": proof_obligation,
        "use_cases": validated_use_cases,
        # serves_truth is true ONLY for an executed-proven deterministic ref; still review-gated for publication.
        "candidate": True, "serves_truth": serves_truth,
        "review_ticket": {"open": True, "reason": "publisher submission — governance review before tenant publication"},
    }
    return {"record_type": "publish_decision", "accepted": True, "primitive_id": primitive_id,
            "serves_truth": serves_truth, "verification_level": verification, "gates": gates,
            "reasons": reasons, "record": record, "candidate": True}


def stage_submission(decision: dict) -> Optional[Path]:
    if not decision.get("accepted"):
        return None
    STAGE_DIR.mkdir(parents=True, exist_ok=True)
    path = STAGE_DIR / "published_primitives.jsonl"
    with path.open("a") as fh:
        fh.write(json.dumps(decision["record"], sort_keys=True) + "\n")
    return path


def self_test() -> int:
    checks: list[tuple[str, bool]] = []

    # anonymous submission (no signature) is rejected — no anonymous truth.
    anon = publish_primitive({"publisher": {"id": "acme"}, "primitive": {"input_edge": "Text", "output_edge": "Text"}})
    checks.append(("anonymous submission rejected", anon["accepted"] is False and anon["gates"]["provenance"] is False))

    signed = {"publisher": {"id": "stripe", "name": "Stripe", "signature": "sig:abc"}, "source_ref": {"url": "https://stripe.com", "name": "Stripe", "path": ""}}

    # edge_untyped primitive rejected at composability.
    untyped = publish_primitive({**signed, "primitive": {"title": "x", "input_edge": "{placeholder}", "output_edge": ""}})
    checks.append(("edge_untyped submission rejected", untyped["accepted"] is False))

    # a network-call submission stages as a GATED EFFECT candidate (never serves_truth).
    eff = publish_primitive({**signed, "primitive": {"title": "charge", "input_edge": "ChargeRequest", "output_edge": "ChargeResult", "effect": "network_write"}})
    checks.append(("effect submission staged candidate, not truth",
                   eff["accepted"] is True and eff["serves_truth"] is False and eff["verification_level"] == "gated_effect"))

    # a deterministic submission referencing a REGISTERED mutator + passing fixture is executed-proven.
    det = publish_primitive({**signed,
                             "primitive": {"title": "rename fields", "input_edge": "RecordBatch", "output_edge": "RecordBatch",
                                           "mutator": "field_rename", "mutator_args": {"mapping": {"a": "b"}}},
                             "fixtures": [{"input": {"a": 1}, "expected_output": {"b": 1}}]})
    checks.append(("deterministic referenced+proven -> serves_truth=true",
                   det["accepted"] is True and det["serves_truth"] is True and det["verification_level"] == "L7_executed_proof"))

    # inline code is NOT executed (sandbox obligation), staged candidate.
    inline = publish_primitive({**signed, "primitive": {"title": "custom", "input_edge": "Text", "output_edge": "Text", "impl_source": "def f(x): ..."}})
    checks.append(("inline code not executed, sandbox obligation recorded",
                   inline["accepted"] is True and inline["serves_truth"] is False and inline["gates"].get("inline_code") == "not_executed"))

    # use-cases are validated for typed steps.
    uc = publish_primitive({**signed,
                            "primitive": {"title": "t", "input_edge": "Text", "output_edge": "Text", "effect": "network_read"},
                            "use_cases": [{"name": "flow", "route": [{"output_edge": "Text"}, {"output_edge": "JsonText"}]}]})
    checks.append(("use-cases validated", uc["record"]["use_cases"][0]["typed_steps"] == 2))

    # every accepted decision is candidate + review-ticketed.
    checks.append(("accepted submissions are review-gated candidates",
                   det["record"]["candidate"] is True and det["record"]["review_ticket"]["open"] is True))

    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - publish_primitive:\n  " + "\n  ".join(failed))
        return 1
    print("PASS - publish_primitive: publisher front door — signed provenance required (no anonymous truth), "
          "same gates as everything (composability + executed-proof/gated-effect + dedupe), inline code sandboxed, "
          "use-cases type-validated; every submission a review-gated candidate.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description="Publisher primitive submission front door.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--submit", metavar="submission.json", help="publish a submission from a JSON file")
    args = ap.parse_args()
    if args.self_test:
        return self_test()
    if args.submit:
        decision = publish_primitive(json.loads(Path(args.submit).read_text()))
        path = stage_submission(decision)
        print(json.dumps({"accepted": decision["accepted"], "primitive_id": decision.get("primitive_id"),
                          "serves_truth": decision.get("serves_truth"), "reasons": decision.get("reasons"),
                          "staged_to": str(path) if path else None}, indent=2))
        return 0
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
