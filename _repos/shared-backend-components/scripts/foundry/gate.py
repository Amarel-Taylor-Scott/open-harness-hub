#!/usr/bin/env python3
"""Foundry gate — Stage 6 (the admission decision).

Admit a candidate as a real component **iff all hold**:

  1. **measured lift** — ``delta > lift_floor`` (a real, computed bare-vs-pipeline
     gain; this is the decision, not a heuristic);
  2. **provenance** — a real licensed source (gap + source pillars, via
     ``Candidate.evidence_status``);
  3. **novelty** — not a near-duplicate (Stage 4 already dropped dups; re-checked);
  4. **durability** — has a durability class; in ``require_structural`` mode, must
     be structural (the moat).

The cheap structural heuristic (`capability_lift_gate.lift_score`) is reused as a
**pre-filter signal** (and a hard-filler-marker veto) — recorded, but the *measured*
delta is what promotes. Uncertain candidates (lift unmeasured, provenance
incomplete, non-structural in structural-only mode) are routed to **review**, never
silently promoted — the promotion-boundary rule from `_repos/_shared/codex/master-goal.md`.

Durability + decay come from the single source (`scripts.eval.reason_codes`).
stdlib-only. Run ``python -m scripts.foundry.gate`` for the offline self-test.
"""
from __future__ import annotations

from typing import Any

from scripts.eval.reason_codes import durability_class, gap_durability_score, is_structural
from scripts.factory.capability_lift_gate import HARD_FILLER_MARKS, lift_score
from scripts.foundry.contracts import CULL, PROMOTED, REVIEW, BaseStage, Candidate, FoundryContext


def evaluate(c: Candidate, *, lift_floor: float = 0.0, require_structural: bool = False,
             human_approval_types: frozenset = frozenset(),
             human_approval_for_llm_only_gaps: bool = False) -> dict[str, Any]:
    """Pure decision for one candidate. Returns {decision, reasons, record}.

    Gate-passing components are PROMOTED but stamped an ``approval_status``:
    ``pending_human`` (a human approves before tenant-visible) for the configured
    sensitive types (knowledge/dataset) or gaps confirmed ONLY by an LLM probe —
    "the LLM doesn't know what it doesn't know"; otherwise ``auto``."""
    record: dict[str, Any] = {}

    # belt-and-suspenders: a duplicate must never promote even if Stage 4 was skipped
    if c.novelty and c.novelty.get("is_duplicate"):
        return {"decision": CULL, "reasons": ["near-duplicate (failed novelty)"], "record": record}

    # cheap structural/quality heuristic (recorded; NOT the decision) + hard-filler veto
    if c.body:
        heuristic, signals, marks = lift_score(c.body)
        record["heuristic_lift"] = round(heuristic, 3)
        record["filler_markers"] = marks
        hard = sorted(set(marks) & HARD_FILLER_MARKS)
        if hard:
            return {"decision": CULL, "reasons": ["filler markers: " + ", ".join(hard)], "record": record}

    # the three evidence pillars (gap + source + measured positive lift)
    ok, missing = c.evidence_status(lift_floor=lift_floor)
    if not ok:
        lift = c.lift or {}
        # a measured delta that did NOT clear the floor is a definitive "model already does it"
        if lift.get("delta") is not None and float(lift["delta"]) <= lift_floor:
            return {"decision": CULL,
                    "reasons": [f"no capability gain (delta {float(lift['delta']):+.3f} ≤ floor {lift_floor:.3f})"],
                    "record": record}
        if any(m.startswith("lift:") for m in missing):
            return {"decision": REVIEW, "reasons": ["lift not measured — route to Stage 5 (measure)"], "record": record}
        if any(m.startswith("source:") for m in missing):
            return {"decision": REVIEW, "reasons": ["provenance incomplete — resolve in review"], "record": record}
        if any(m.startswith("gap:") for m in missing):
            return {"decision": CULL, "reasons": ["no measured gap (no evidence it should exist)"], "record": record}
        return {"decision": REVIEW, "reasons": missing, "record": record}

    # durability (the second axis): does the lift survive the next model?
    reason = (c.gap or {}).get("lift_reason")
    dclass = durability_class(reason)
    dscore = gap_durability_score(
        reason_codes=[reason] if reason else [],
        retrievability_tier=(c.gap or {}).get("retrievability_tier"),
        adversarial=bool((c.gap or {}).get("adversarial")),
        mechanisms=(c.gap or {}).get("mechanisms") or [],
    )
    record["durability_class"] = dclass
    record["durability_score"] = dscore
    if require_structural and dclass != "structural":
        return {"decision": REVIEW,
                "reasons": [f"non-structural lift ({dclass}) — structural-only mode routes to review"],
                "record": record}

    # Passed the MEASURED gate. Decide auto-visible vs. pending human approval — the
    # human-in-the-loop check, since LLM-found gaps can't be self-certified.
    record["gate_passed"] = True
    csource = (c.gap or {}).get("confirmation_source")
    pending = (c.target_type in human_approval_types) or (
        human_approval_for_llm_only_gaps and csource == "llm_probe")
    record["approval_status"] = "pending_human" if pending else "auto"
    note = "structural lift (the moat)" if dclass == "structural" else f"{dclass} lift — watch decay"
    if pending:
        why = ("knowledge needs human approval" if c.target_type in human_approval_types
               else "LLM-found gap needs human confirmation")
        note += f"; pending human approval ({why})"
    return {"decision": PROMOTED, "reasons": [note], "record": record}


class GateStage(BaseStage):
    """Apply ``evaluate`` to the batch; promote / cull / route-to-review."""

    name = "gate"

    def run(self, batch: list[Candidate], ctx: FoundryContext) -> list[Candidate]:
        floor = ctx.config.lift_floor
        req_structural = ctx.config.require_structural
        for c in batch:
            if not c.alive:
                continue
            verdict = evaluate(c, lift_floor=floor, require_structural=req_structural,
                               human_approval_types=ctx.config.human_approval_types,
                               human_approval_for_llm_only_gaps=ctx.config.human_approval_for_llm_only_gaps)
            decision, reasons, record = verdict["decision"], verdict["reasons"], verdict["record"]
            # stamp durability/decay + approval status onto the measured lift so it travels with the row
            if c.lift is not None:
                if "durability_class" in record:
                    c.lift.setdefault("durability_class", record["durability_class"])
                    c.lift.setdefault("durability_score", record["durability_score"])
                    c.lift.setdefault("decay_signal", "none" if record["durability_class"] == "structural" else "watch")
                if "approval_status" in record:
                    c.lift["approval_status"] = record["approval_status"]
                    c.lift["gate_passed"] = record.get("gate_passed", False)
            c.mark(self.name, decision, "; ".join(reasons))
            if decision == PROMOTED:
                # mint at the first real lifecycle tier
                if isinstance(c.body, dict):
                    c.body["lifecycle"] = "experimental"
                c.promote(self.name)
            else:
                c.drop(self.name, reasons[0] if reasons else decision, decision=decision)
        return batch


# --------------------------------------------------------------------------- #
# self-test (offline)
# --------------------------------------------------------------------------- #
def _make(**lift_over) -> Candidate:
    """A fully-evidenced candidate; override the lift dict via kwargs."""
    lift = {"bare_score": 0.42, "pipeline_score": 0.83, "delta": 0.41, "n": 20}
    lift.update(lift_over)
    return Candidate(
        target_type="knowledge-pack",
        component_id="knowledge-pack/csddd-articles-abcd1234",
        body={"id": "knowledge-pack/csddd-articles-abcd1234", "type": "knowledge-pack",
              "name": "CSDDD article corpus",
              "description": "Reference extracts of CSDDD articles for supply-chain due diligence "
                             "with citations across 13 languages and exact article anchors.",
              "industry": ["esg", "supply_chain"], "license": "CC-BY-4.0",
              "data": [{"x": 1}]},
        gap={"id": "gap/csddd", "lift_reason": "esoteric_rule", "model_independent_score": 0.8,
             "retrievability_tier": 3, "failure_samples": [{"task": "cite art 8", "correct": False}]},
        source={"source_url": "https://eur-lex.europa.eu/csddd", "author": "EU", "license": "CC-BY-4.0"},
        lift=lift,
    )


def _self_test() -> int:
    failures: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            failures.append(name)

    ctx = FoundryContext()

    # positive measured lift, fully evidenced, novel ⇒ promoted at experimental
    good = _make()
    good.novelty = {"is_duplicate": False}
    GateStage().run([good], ctx)
    check("evidenced + positive delta ⇒ promoted", good.decision == PROMOTED, good.short())
    check("promoted minted at experimental", good.body.get("lifecycle") == "experimental")
    check("decay signal stamped (transient→watch)", good.lift.get("decay_signal") == "watch", str(good.lift))

    # zero / negative measured delta ⇒ cull "no capability gain"
    nogain = _make(delta=0.0)
    nogain.novelty = {"is_duplicate": False}
    GateStage().run([nogain], FoundryContext())
    check("zero delta ⇒ culled", nogain.decision == CULL)
    check("cull reason names capability gain", any("capability gain" in r for r in nogain.reasons), str(nogain.reasons))

    # missing provenance ⇒ review (resolvable), not cull
    nosrc = _make()
    nosrc.source = {"source_url": "https://x/y"}  # missing author + license
    nosrc.novelty = {"is_duplicate": False}
    GateStage().run([nosrc], FoundryContext())
    check("incomplete provenance ⇒ review", nosrc.decision == REVIEW, str(nosrc.reasons))

    # duplicate ⇒ cull even if everything else is strong
    dup = _make()
    dup.novelty = {"is_duplicate": True}
    GateStage().run([dup], FoundryContext())
    check("duplicate ⇒ culled", dup.decision == CULL)

    # structural-only mode: a transient lift is routed to review
    transient = _make()
    transient.novelty = {"is_duplicate": False}
    strict = FoundryContext()
    strict.config.require_structural = True
    GateStage().run([transient], strict)
    check("structural-only: transient ⇒ review", transient.decision == REVIEW, str(transient.reasons))

    # structural lift in structural-only mode ⇒ promoted, decay none
    structural = _make()
    structural.gap["lift_reason"] = "no_addressable_source"   # structural
    structural.novelty = {"is_duplicate": False}
    strict2 = FoundryContext()
    strict2.config.require_structural = True
    GateStage().run([structural], strict2)
    check("structural lift promotes in strict mode", structural.decision == PROMOTED)
    check("structural ⇒ decay none", structural.lift.get("decay_signal") == "none", str(structural.lift))
    check("structural durability recorded", structural.is_structural_lift)

    # lift_floor respected: a small positive delta below floor is culled
    small = _make(delta=0.05)
    small.novelty = {"is_duplicate": False}
    fctx = FoundryContext()
    fctx.config.lift_floor = 0.10
    GateStage().run([small], fctx)
    check("delta below configured floor ⇒ culled", small.decision == CULL, str(small.reasons))

    # HUMAN APPROVAL — knowledge passes the measured gate but is pending_human (not auto-visible)
    kp = _make(); kp.novelty = {"is_duplicate": False}
    GateStage().run([kp], FoundryContext())   # default config: knowledge ⇒ pending_human
    check("knowledge promotes BUT pending human approval",
          kp.decision == PROMOTED and kp.lift.get("approval_status") == "pending_human", str(kp.lift))
    check("gate_passed recorded", kp.lift.get("gate_passed") is True)
    # non-knowledge from a RECORDED gap ⇒ auto-approved
    rp = _make(); rp.target_type = "rule-pack"; rp.body["type"] = "rule-pack"; rp.novelty = {"is_duplicate": False}
    GateStage().run([rp], FoundryContext())
    check("non-knowledge (recorded gap) ⇒ auto-approved",
          rp.decision == PROMOTED and rp.lift.get("approval_status") == "auto", str(rp.lift))
    # LLM-probe-only gap ⇒ pending even for non-knowledge ("doesn't know what it doesn't know")
    llm = _make(); llm.target_type = "rule-pack"; llm.body["type"] = "rule-pack"
    llm.gap["confirmation_source"] = "llm_probe"; llm.novelty = {"is_duplicate": False}
    GateStage().run([llm], FoundryContext())
    check("LLM-found gap ⇒ pending human confirmation", llm.lift.get("approval_status") == "pending_human", str(llm.lift))

    print(f"\n{'all gate self-tests passed.' if not failures else f'{len(failures)} FAILURES: {failures}'}")
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(_self_test())
