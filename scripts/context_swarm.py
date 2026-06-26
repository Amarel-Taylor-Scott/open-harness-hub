#!/usr/bin/env python3
"""scripts.context_swarm — swarm-verify a context object (deterministic-first, governed).

The "Swarm this object" product surface: a user (or agent) points at any context object and a swarm
of BOUNDED agents spins up to robustly **verify / expand / improve / validate / challenge** it using
internal context (its graph neighborhood + source handles) and, behind a seam, external context.

This is built on the graph engine (`scripts.context_graph`) — the agents reuse `ContextGraph` and
its deterministic `find_contradictions` rather than re-deriving structure. Each agent is a small,
auditable function that emits structured `SwarmFinding`s; a controller aggregates them into a
`SwarmConsensus` and a `SwarmRun`.

GOVERNANCE (hard rules, enforced by construction):
  * The swarm **never overwrites a canonical object.** It PROPOSES a `context_pack_patch`
    (`applied: false`) and, for any HIGH/CRITICAL finding, ROUTES a steward-review-request (reusing
    `schemas/governance/steward-review-request.schema.json`). Application is a separate, human/policy-
    gated step — not part of the swarm.
  * Deterministic-first: the offline default agents call no model and no network; they are pure
    functions of the graph. A live model route (`model_gateway`) and external evidence fetch are
    SEAMS (recorded as not-run offline), never silent fabrication.

CLI / self-test (swarms the demo's stale runbook claim; no model, no network):
    python3 scripts/context_swarm.py --self-test
    python3 scripts/context_swarm.py --swarm obj-runbook --purpose verify
"""
from __future__ import annotations

import argparse
import json
from hashlib import sha256
from typing import Any, Callable

# Make the repo root importable when run *directly* (the repo has no top-level scripts/__init__.py;
# it is a namespace package run via -m from the root). This module COMPOSES scripts.context_graph,
# so it cannot be self-contained. Stdlib only; no-op under -m / when scripts is already importable.
if __name__ == "__main__" and __package__ in (None, ""):  # pragma: no cover
    import os
    import sys

    _REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _REPO_ROOT not in sys.path:
        sys.path.insert(0, _REPO_ROOT)

from scripts.context_graph import ContextGraph, load_seed, DEMO_SEED

#: severity ladder (single source) → used for risk aggregation + ordering.
SEVERITY = ("info", "low", "medium", "high", "critical")
_SEV_RANK = {s: i for i, s in enumerate(SEVERITY)}
#: risk levels that force a human review (and block low-risk auto-application).
HUMAN_REVIEW_RISKS = ("high", "critical")
#: swarm purposes (recorded; all agents run regardless — purpose tunes emphasis/labels).
PURPOSES = ("verify", "expand", "improve", "validate", "challenge")


def _finding(agent: str, finding_type: str, severity: str, summary: str,
             evidence: list[str] | None = None, suggestion: str | None = None) -> dict:
    assert severity in SEVERITY, f"bad severity {severity!r}"
    return {"agent": agent, "finding_type": finding_type, "severity": severity, "summary": summary,
            "evidence": evidence or [], "suggestion": suggestion}


# ── the bounded agents (each: (graph, oid, ctx) -> list[finding]) ───────────────
def _subject_assertions(graph: ContextGraph, oid: str) -> list[dict]:
    return [a for a in graph.assertions if a["subject_id"] == oid]


def source_handle_validator(graph: ContextGraph, oid: str, ctx: dict) -> list[dict]:
    handles = graph.objects[oid].get("source_handles", [])
    if not handles:
        return [_finding("SourceHandleValidator", "missing_source_handle", "high",
                         f"{oid} has NO ctx:// source handle — claims are unverifiable")]
    bad = [h for h in handles if not h.startswith("ctx://")]
    if bad:
        return [_finding("SourceHandleValidator", "malformed_handle", "medium",
                         f"{oid} has malformed handles: {bad}", evidence=handles)]
    return [_finding("SourceHandleValidator", "handles_ok", "info",
                     f"{oid} has {len(handles)} valid ctx:// handle(s)", evidence=handles)]


def internal_evidence_finder(graph: ContextGraph, oid: str, ctx: dict) -> list[dict]:
    out: list[dict] = []
    for a in _subject_assertions(graph, oid):
        others = [o for o in graph.assertions if o["predicate"] == a["predicate"] and o["subject_id"] != oid]
        agree = [o for o in others if o.get("value") == a.get("value")]
        disagree = [o for o in others if o.get("value") != a.get("value")]
        if disagree:
            out.append(_finding("InternalEvidenceFinder", "internal_disagreement", "high",
                                f"'{a['predicate']}'={a.get('value')} on {oid} disagrees with "
                                + ", ".join(f"{o['subject_id']}={o.get('value')}" for o in disagree),
                                evidence=[h for o in disagree for h in o.get("evidence", [])]))
        elif agree:
            out.append(_finding("InternalEvidenceFinder", "internal_corroboration", "info",
                                f"'{a['predicate']}'={a.get('value')} on {oid} corroborated by "
                                + ", ".join(o["subject_id"] for o in agree),
                                evidence=[h for o in agree for h in o.get("evidence", [])]))
    if not out:
        out.append(_finding("InternalEvidenceFinder", "no_internal_claims", "low",
                            f"{oid} carries no assertions to corroborate"))
    return out


def external_evidence_finder(graph: ContextGraph, oid: str, ctx: dict) -> list[dict]:
    # SEAM: external (web/registry) corroboration. Offline + external not allowed → recorded not-run.
    if ctx.get("external_allowed") and ctx.get("external_fetcher"):
        try:
            res = ctx["external_fetcher"](oid)  # live seam — only when explicitly wired
            return [_finding("ExternalEvidenceFinder", "external_evidence", "info",
                             f"external corroboration: {res}", evidence=[])]
        except Exception as e:  # never let a flaky fetch break the swarm
            return [_finding("ExternalEvidenceFinder", "external_error", "low", f"external fetch failed: {e}")]
    return [_finding("ExternalEvidenceFinder", "external_not_run", "info",
                     "external corroboration NOT run (offline / external_allowed=false) — labeled seam")]


def contradiction_hunter(graph: ContextGraph, oid: str, ctx: dict) -> list[dict]:
    out: list[dict] = []
    preds = {a["predicate"] for a in _subject_assertions(graph, oid)}
    for c in graph.find_contradictions():
        touches = (c.get("kind") == "assertion"
                   and (c["authority"]["subject_id"] == oid
                        or any(x["subject_id"] == oid for x in c.get("conflicting", []))
                        or c.get("predicate") in preds))
        if c.get("kind") == "edge":
            touches = oid in c.get("between", [])
        if touches:
            losers = ", ".join(f"{x['subject_id']}={x['value']}" for x in c.get("conflicting", []))
            out.append(_finding("ContradictionHunter", "contradiction", "high",
                                f"contradiction on '{c.get('predicate')}': authority "
                                f"{c.get('authority', {}).get('subject_id')}={c.get('authority', {}).get('value')}"
                                f" vs {losers}", evidence=c.get("source_handles", []),
                                suggestion=f"align {oid} with the authority"))
    return out


def graph_neighbor_explorer(graph: ContextGraph, oid: str, ctx: dict) -> list[dict]:
    nbrs = graph.neighbors(oid)
    rels = [f"{r['relationship_type']}→{r['to_id']}" for r in graph.relationships if r["from_id"] == oid]
    rels += [f"{r['from_id']}→{r['relationship_type']}" for r in graph.relationships if r["to_id"] == oid]
    return [_finding("GraphNeighborExplorer", "neighborhood", "info",
                     f"{oid} has {len(nbrs)} neighbor(s); edges: {sorted(rels)}")]


def claim_normalizer(graph: ContextGraph, oid: str, ctx: dict) -> list[dict]:
    out: list[dict] = []
    for a in _subject_assertions(graph, oid):
        if a.get("confidence") is None:
            out.append(_finding("ClaimNormalizer", "missing_confidence", "low",
                                f"assertion '{a['predicate']}' on {oid} has no confidence"))
    if not out:
        out.append(_finding("ClaimNormalizer", "claims_normalized", "info", f"{oid} assertions are well-formed"))
    return out


def freshness_checker(graph: ContextGraph, oid: str, ctx: dict) -> list[dict]:
    stale = graph._staleness(oid)
    if stale == "stale":
        eff = (graph.objects[oid].get("freshness") or {}).get("effective_date", "?")
        return [_finding("FreshnessChecker", "stale", "high",
                         f"{oid} is STALE (effective {eff}) — do not rely on it for a write action",
                         evidence=graph.objects[oid].get("source_handles", []))]
    if stale == "dated":
        return [_finding("FreshnessChecker", "dated", "medium", f"{oid} is DATED — re-validate before use")]
    return [_finding("FreshnessChecker", "fresh", "info", f"{oid} freshness={stale}")]


def policy_checker(graph: ContextGraph, oid: str, ctx: dict) -> list[dict]:
    pol = graph.objects[oid].get("policy") or {}
    out: list[dict] = []
    if pol.get("requires_refresh"):
        out.append(_finding("PolicyChecker", "requires_refresh", "medium", f"{oid} policy.requires_refresh=true"))
    if pol.get("promotion_allowed") is False:
        out.append(_finding("PolicyChecker", "promotion_blocked", "medium", f"{oid} is not promotion-eligible"))
    if not out:
        out.append(_finding("PolicyChecker", "policy_ok", "info", f"{oid} policy gates pass"))
    return out


#: agent registry — order is the run order (deterministic). Risk-review + pack-improver +
#: human-review-router are CONTROLLER stages that read findings, so they run after these.
AGENTS: tuple[tuple[str, Callable], ...] = (
    ("SourceHandleValidator", source_handle_validator),
    ("InternalEvidenceFinder", internal_evidence_finder),
    ("ExternalEvidenceFinder", external_evidence_finder),
    ("ContradictionHunter", contradiction_hunter),
    ("GraphNeighborExplorer", graph_neighbor_explorer),
    ("ClaimNormalizer", claim_normalizer),
    ("FreshnessChecker", freshness_checker),
    ("PolicyChecker", policy_checker),
)


def _max_severity(findings: list[dict]) -> str:
    return max((f["severity"] for f in findings), key=lambda s: _SEV_RANK[s], default="info")


def _risk_from_severity(sev: str) -> str:
    # info/low → low; medium → medium; high → high; critical → critical.
    return {"info": "low", "low": "low", "medium": "medium", "high": "high", "critical": "critical"}[sev]


def _owner_of(graph: ContextGraph, oid: str) -> str | None:
    for r in graph.relationships:
        if r["from_id"] == oid and r["relationship_type"] == "OWNED_BY":
            return r["to_id"]
    return None


def _pack_improver(graph: ContextGraph, oid: str, contradictions: list[dict]) -> dict | None:
    """PROPOSE (never apply) a patch that aligns a contradicted object with its authority."""
    for c in contradictions:
        # find the assertion conflict that names this object as a (losing) party
        for full in graph.find_contradictions():
            if full.get("kind") != "assertion":
                continue
            losers = {x["subject_id"]: x for x in full.get("conflicting", [])}
            if oid in losers:
                return {
                    "op": "update_claim", "subject_id": oid, "predicate": full["predicate"],
                    "from_value": losers[oid]["value"], "to_value": full["authority"]["value"],
                    "authority": full["authority"]["subject_id"], "applied": False,
                    "reason": f"align {oid} with authoritative {full['authority']['subject_id']} "
                              f"(={full['authority']['value']}); requires human/policy approval before apply",
                }
    return None


def _human_review_request(graph: ContextGraph, oid: str, risk: str, findings: list[dict],
                          has_contradiction: bool) -> dict:
    trigger = "high_conflict_claim" if has_contradiction else (
        "stale_pack_for_write" if any(f["finding_type"] == "stale" for f in findings) else "policy_exception")
    handles = sorted({h for f in findings for h in f.get("evidence", []) if h.startswith("ctx://")})
    seed = json.dumps({"o": oid, "t": trigger, "r": risk}, sort_keys=True)
    return {
        "kind": "baltor.steward-review-request",
        "review_request_id": "rr-" + sha256(seed.encode("utf-8")).hexdigest()[:16],
        "trigger": trigger,
        "subject": oid,
        "risk": risk,
        "requested_by": "context_object_swarm",
        "owner": _owner_of(graph, oid),
        "evidence": handles,
        "status": "open",
        "created_at": "1970-01-01T00:00:00Z",
    }


def swarm_object(graph: ContextGraph, object_id: str, *, purpose: str = "verify",
                 internal_allowed: bool = True, external_allowed: bool = False,
                 external_fetcher: Callable | None = None, max_agents: int = len(AGENTS),
                 model_route: Callable | None = None, bus=None) -> dict[str, Any]:
    """Swarm-verify `object_id`. Deterministic offline; returns a SwarmRun (no canonical mutation).

    If `bus` (a scripts.context_events.EventBus, duck-typed) is passed, emit swarm.started →
    swarm.agent.completed (per bounded agent) → swarm.consensus.created for the live dashboard —
    non-breaking + deterministic when omitted (default None → no events, identical output)."""
    if object_id not in graph.objects:
        raise ValueError(f"unknown object_id {object_id!r}")
    if purpose not in PURPOSES:
        raise ValueError(f"purpose must be one of {PURPOSES}, got {purpose!r}")

    _cid = "swarm-" + object_id
    if bus is not None:
        bus.publish("swarm.started", component="context_swarm", stage="Anti-Fragility",
                    correlation_id=_cid, object_ref=object_id, payload={"purpose": purpose})

    ctx = {"purpose": purpose, "internal_allowed": internal_allowed,
           "external_allowed": external_allowed, "external_fetcher": external_fetcher}

    findings: list[dict] = []
    agents_run: list[str] = []
    for name, fn in AGENTS[:max(1, max_agents)]:
        agents_run.append(name)
        produced = fn(graph, object_id, ctx)
        findings.extend(produced)
        if bus is not None:
            bus.publish("swarm.agent.completed", component="context_swarm", stage="Anti-Fragility",
                        correlation_id=_cid, object_ref=object_id,
                        payload={"agent": name, "findings": len(produced),
                                 "max_severity": _max_severity(produced)})

    # controller stages (read findings) ---
    contradictions = [f for f in findings if f["finding_type"] == "contradiction"]
    rot_signals = [f for f in findings if f["finding_type"] in ("stale", "dated")]
    policy_risks = [f for f in findings if f["finding_type"] in ("requires_refresh", "promotion_blocked")]
    has_contradiction = bool(contradictions) or any(
        f["finding_type"] == "internal_disagreement" for f in findings)

    risk = _risk_from_severity(_max_severity(findings))
    requires_human_review = risk in HUMAN_REVIEW_RISKS
    agents_run.append("RiskReviewer")

    pack_patch = _pack_improver(graph, object_id, contradictions)
    if pack_patch:
        agents_run.append("PackImprover")

    review_requests: list[dict] = []
    if requires_human_review:
        review_requests.append(_human_review_request(graph, object_id, risk, findings, has_contradiction))
        agents_run.append("HumanReviewRouter")

    # verified / rejected claims (deterministic, from the internal-evidence findings)
    verified_claims = [{"subject_id": object_id, "summary": f["summary"]}
                       for f in findings if f["finding_type"] == "internal_corroboration"]
    rejected_claims = [{"subject_id": object_id, "summary": f["summary"]}
                       for f in findings if f["finding_type"] == "internal_disagreement"]

    # confidence: fraction of agents whose findings were non-negative (info/low), deterministic.
    non_negative = sum(1 for f in findings if _SEV_RANK[f["severity"]] <= _SEV_RANK["low"])
    confidence = round(non_negative / len(findings), 4) if findings else 0.0

    consensus = {
        "kind": "baltor.swarm-consensus",
        "object_ref": object_id,
        "risk_level": risk,
        "requires_human_review": requires_human_review,
        "verified_claims": verified_claims,
        "rejected_claims": rejected_claims,
        "contradictions": [f["summary"] for f in contradictions],
        "rot_signals": [f["summary"] for f in rot_signals],
        "policy_risks": [f["summary"] for f in policy_risks],
        "suggested_relationships": ([f"{object_id} REQUIRES_REFRESH (per authority)"] if rot_signals and has_contradiction else []),
        "context_pack_patch": pack_patch,
        "confidence": confidence,
        "canonical_mutated": False,
    }

    if bus is not None:
        bus.publish("swarm.consensus.created", component="context_swarm", stage="Anti-Fragility",
                    correlation_id=_cid, object_ref=object_id,
                    payload={"risk_level": risk, "requires_human_review": requires_human_review,
                             "proposed_fix": (f"{pack_patch['from_value']}→{pack_patch['to_value']}" if pack_patch else None)})

    used_model = False  # model_route is a phrasing/triage seam; offline default never calls it
    run_seed = json.dumps({"o": object_id, "p": purpose,
                           "f": [f["summary"] for f in findings]}, sort_keys=True)
    return {
        "kind": "baltor.swarm-run",
        "swarm_run_id": "swarm-" + sha256(run_seed.encode("utf-8")).hexdigest()[:16],
        "object_ref": object_id,
        "purpose": purpose,
        "agents_run": agents_run,
        "findings": findings,
        "consensus": consensus,
        "review_requests": review_requests,
        "canonical_mutated": False,
        "receipt": {
            "kind": "baltor.swarm-receipt",
            "swarm_receipt_id": "swrc-" + sha256(run_seed.encode("utf-8")).hexdigest()[:16],
            "object_ref": object_id, "findings_count": len(findings), "risk_level": risk,
            "requires_human_review": requires_human_review, "review_requests": [r["review_request_id"] for r in review_requests],
            "deterministic": not used_model,
        },
        "deterministic": not used_model,
        "llm_used": used_model,
        "created_at": "1970-01-01T00:00:00Z",
    }


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    g = ContextGraph(load_seed())
    # snapshot to prove the swarm NEVER mutates canonical state
    before = json.dumps({"o": g.objects, "a": g.assertions, "r": g.relationships}, sort_keys=True)

    run = swarm_object(g, "obj-runbook", purpose="verify")

    check("all bounded agents ran", {"SourceHandleValidator", "ContradictionHunter", "FreshnessChecker",
                                     "PolicyChecker", "InternalEvidenceFinder"} <= set(run["agents_run"]))
    check("swarm detected the 5-vs-3 contradiction", bool(run["consensus"]["contradictions"]),
          str(run["consensus"]["contradictions"]))
    check("risk is high (stale + contradicted)", run["consensus"]["risk_level"] == "high",
          run["consensus"]["risk_level"])
    check("human review is required", run["consensus"]["requires_human_review"] is True)
    check("a steward-review-request was routed", len(run["review_requests"]) == 1, str(len(run["review_requests"])))

    rr = run["review_requests"][0] if run["review_requests"] else {}
    check("review request trigger=high_conflict_claim, subject=obj-runbook, risk=high",
          rr.get("trigger") == "high_conflict_claim" and rr.get("subject") == "obj-runbook" and rr.get("risk") == "high")
    check("review request routed to the owning team", rr.get("owner") == "obj-billing-team", str(rr.get("owner")))

    patch = run["consensus"]["context_pack_patch"]
    check("pack patch PROPOSES the fix 3→5 from the ADR authority",
          patch and patch["from_value"] == 3 and patch["to_value"] == 5 and patch["authority"] == "obj-adr-014",
          json.dumps(patch))
    check("pack patch is NOT applied (proposal only)", patch and patch["applied"] is False)
    check("rejected_claims include the stale runbook value", bool(run["consensus"]["rejected_claims"]))

    # GOVERNANCE: the swarm must not have mutated any canonical object/assertion/relationship
    after = json.dumps({"o": g.objects, "a": g.assertions, "r": g.relationships}, sort_keys=True)
    check("swarm did NOT mutate canonical state (proposes only)", before == after)
    check("run + receipt + consensus all flag canonical_mutated=False",
          run["canonical_mutated"] is False and run["consensus"]["canonical_mutated"] is False)

    # determinism
    g2 = ContextGraph(load_seed())
    run2 = swarm_object(g2, "obj-runbook", purpose="verify")
    check("byte-identical on re-run (deterministic, no clock/RNG/model)", run2 == run)
    check("deterministic + no LLM by default", run["deterministic"] is True and run["llm_used"] is False)

    # external evidence is a labeled seam, not faked
    ext = [f for f in run["findings"] if f["agent"] == "ExternalEvidenceFinder"]
    check("external evidence is a labeled not-run seam offline", ext and ext[0]["finding_type"] == "external_not_run")

    # a genuinely clean object (fresh, no assertions, not party to any contradiction) → no review, no
    # patch. NB: the ADR is NOT clean — it is a party to the active 5-vs-3 contradiction, so swarming
    # it correctly flags review; billing-team is the uninvolved, fresh control.
    run_ok = swarm_object(ContextGraph(load_seed()), "obj-billing-team", purpose="validate")
    check("swarming a clean uninvolved object needs no human review + proposes no patch",
          run_ok["consensus"]["requires_human_review"] is False and run_ok["consensus"]["context_pack_patch"] is None,
          f"risk={run_ok['consensus']['risk_level']}")
    # ...and swarming the ADR (a party to the contradiction) DOES flag it — proving the swarm follows
    # the conflict regardless of which end you point it at.
    run_adr = swarm_object(ContextGraph(load_seed()), "obj-adr-014", purpose="verify")
    check("swarming the ADR (party to the conflict) also surfaces the contradiction",
          bool(run_adr["consensus"]["contradictions"]) and run_adr["consensus"]["requires_human_review"] is True)

    # the routed review request validates against the canonical steward-review-request schema
    try:
        import json as _j
        from pathlib import Path
        from jsonschema import Draft202012Validator
        schema = _j.loads((Path(__file__).resolve().parents[1]
                           / "schemas/governance/steward-review-request.schema.json").read_text())
        errs = list(Draft202012Validator(schema).iter_errors(rr))
        check("routed review request validates against steward-review-request.schema.json", not errs,
              "; ".join(e.message for e in errs[:2]))
    except ImportError:
        print("  [skip] jsonschema not installed — schema validation of the review request skipped")

    print(f"\n{'PASS — context_swarm: bounded agents verify obj-runbook, find the 5-vs-3 contradiction, flag it stale + high-risk, ROUTE a steward review to the owning team, and PROPOSE (not apply) the 3→5 fix; canonical state untouched; deterministic.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


def _main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="Swarm-verify a context object (deterministic, governed).")
    p.add_argument("--self-test", action="store_true")
    p.add_argument("--swarm", metavar="OBJECT_ID", help="swarm a context object in the demo graph")
    p.add_argument("--purpose", default="verify", choices=PURPOSES)
    p.add_argument("--seed", default=str(DEMO_SEED))
    args = p.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.swarm:
        g = ContextGraph(load_seed(args.seed))
        print(json.dumps(swarm_object(g, args.swarm, purpose=args.purpose), indent=2))
        return 0
    p.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(_main())
