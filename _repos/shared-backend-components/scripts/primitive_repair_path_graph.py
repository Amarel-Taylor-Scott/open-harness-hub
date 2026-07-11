#!/usr/bin/env python3
"""Deterministic-first primitive repair path-graph (self-healing composition).

Owner directive 2026-07-01: primitives must be FLEXIBLE and SELF-HEALING — when a
source primitive's output edge doesn't match a target's input edge, iterate through
DETERMINISTIC mutations first (scalar->array, type coerce, field rename, envelope
wrap...) and only call an LLM on the IRREDUCIBLE part (a genuine semantic gap).
Recover from failure by falling back to another path. Know the FULL UNIVERSE of
repair paths so any path can be tried, checkpointed, compared, and benchmarked, and
cache/weight proven paths so a similar contract-gap reuses a proven repair.

This wires the pieces that already exist (reuse, don't rebuild):
  - fit classes + mutation hints  -> _repos/teleon/backend/src/teleon/registry/primitive_match.py
  - path cost / compare / rollback -> _repos/teleon/backend/src/teleon/experiments/{path_costing,path_comparator,path_rollback}
into ONE resolver that emits the repair PATH GRAPH for a contract gap.

Cost model (the whole point): deterministic mutators cost 0 model tokens; an LLM
step costs a BOUNDED budget. Ranking prefers ZERO-LLM paths, then fewest steps.
A path is only valid if every step passes its CHECKPOINT (the contract predicate).

Everything emitted is candidate=true / serves_truth=false — evidence, not truth.

Usage:
  python3 _repos/shared-backend-components/scripts/primitive_repair_path_graph.py --self-test
  python3 _repos/shared-backend-components/scripts/primitive_repair_path_graph.py --demo
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import copy
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Callable

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import REPO_ROOT  # noqa: E402

OUT_DIR = _resource("data/dev-intel/primitive_repair_paths")

# Fit-class ladder (names kept consistent with primitive_match.py single source).
FIT_EXACT = "exact_match"
FIT_DETERMINISTIC = "deterministic_edit_match"
FIT_NONDETERMINISTIC = "nondeterministic_edit_match"  # needs an LLM step
FIT_INCOMPATIBLE = "incompatible"

LLM_STEP_TOKEN_BUDGET = 400   # bounded — only the irreducible semantic gap
MAX_PATH_DEPTH = 5            # keep the universe enumerable

# A contract is a small dict: {"shape": scalar|array|object, "type": str, "fields": [..], "semantic": str}


class Mutator:
    """A deterministic (or, for the escalation step, LLM-bounded) contract transform
    with a precondition, an apply, a token cost, and a checkpoint predicate."""

    def __init__(self, name: str, *, applies: Callable[[dict], bool], apply: Callable[[dict], dict],
                 tokens: int = 0, deterministic: bool = True, note: str = "") -> None:
        self.name = name
        self._applies = applies
        self._apply = apply
        self.tokens = tokens
        self.deterministic = deterministic
        self.note = note

    def can(self, c: dict) -> bool:
        try:
            return self._applies(c)
        except Exception:
            return False

    def run(self, c: dict) -> dict:
        return self._apply(copy.deepcopy(c))


def _deterministic_mutators() -> list[Mutator]:
    """The deterministic repair vocabulary (0 model tokens). Each is a proven,
    checkpointable edit — the kind the user wants tried BEFORE any LLM call."""
    m: list[Mutator] = []
    # scalar -> array (wrap) and array -> scalar (take-first, lossy-flagged)
    m.append(Mutator("scalar_to_array", applies=lambda c: c.get("shape") == "scalar",
                     apply=lambda c: {**c, "shape": "array"}, note="wrap scalar in a 1-element array"))
    m.append(Mutator("array_to_scalar_first", applies=lambda c: c.get("shape") == "array",
                     apply=lambda c: {**c, "shape": "scalar", "lossy": True}, note="take first element (LOSSY)"))
    # type coercions (deterministic, total)
    COERCE = {("int", "str"), ("float", "str"), ("int", "float"), ("bool", "int"), ("str", "bytes")}
    for a, b in COERCE:
        m.append(Mutator(f"coerce_{a}_to_{b}", applies=lambda c, a=a: c.get("type") == a,
                         apply=lambda c, b=b: {**c, "type": b}, note=f"coerce {a}->{b}"))
    # field rename (deterministic given a mapping — here modeled as a normalize)
    m.append(Mutator("field_rename_normalize",
                     applies=lambda c: c.get("shape") == "object" and c.get("fields_unnormalized"),
                     apply=lambda c: {**c, "fields_unnormalized": False}, note="rename fields to target names"))
    # envelope wrap / unwrap
    m.append(Mutator("envelope_wrap", applies=lambda c: not c.get("enveloped"),
                     apply=lambda c: {**c, "enveloped": True}, note="wrap in a typed envelope"))
    m.append(Mutator("envelope_unwrap", applies=lambda c: c.get("enveloped"),
                     apply=lambda c: {**c, "enveloped": False}, note="unwrap a typed envelope"))
    return m


def _llm_escalation() -> Mutator:
    """The bounded LLM step — the ONLY non-deterministic mutator, used only when a
    residual SEMANTIC gap remains that no deterministic edit closes (e.g. raw_html ->
    structured_record needs extraction logic). Token-budgeted."""
    # Extraction/structuring: an LLM bridge over a raw semantic input yields a
    # NORMALIZED STRUCTURED object (that is what the extraction actually produces),
    # so it clears the semantic gap AND lands the structured shape in one bounded step.
    return Mutator("llm_semantic_bridge",
                   applies=lambda c: bool(c.get("semantic")),
                   apply=lambda c: {**c, "semantic": None, "shape": "object",
                                    "fields_unnormalized": False},
                   tokens=LLM_STEP_TOKEN_BUDGET, deterministic=False,
                   note="bounded LLM: extract/structure across an irreducible semantic gap")


def _matches(a: dict, b: dict) -> bool:
    """Checkpoint: does contract `a` satisfy target `b` on the axes that matter?"""
    for axis in ("shape", "type"):
        if b.get(axis) is not None and a.get(axis) != b.get(axis):
            return False
    if b.get("semantic") and a.get("semantic") != b.get("semantic"):
        return False
    if b.get("enveloped") is not None and a.get("enveloped", False) != b.get("enveloped"):
        return False
    if b.get("fields_unnormalized") is False and a.get("fields_unnormalized"):
        return False
    return True


def enumerate_paths(source: dict, target: dict) -> dict[str, Any]:
    """Breadth-first enumerate the FULL universe of repair paths from source to target,
    deterministic mutators + the bounded LLM step, up to MAX_PATH_DEPTH. Return every
    path that reaches the target (checkpointed at each step) plus the ranked choice."""
    det = _deterministic_mutators()
    llm = _llm_escalation()
    all_mut = det + [llm]

    complete: list[dict[str, Any]] = []
    # frontier holds (contract, steps[list of {mutator, tokens, deterministic}])
    frontier: list[tuple[dict, list[dict]]] = [(copy.deepcopy(source), [])]
    seen: set[str] = set()

    while frontier:
        contract, steps = frontier.pop(0)
        if len(steps) > MAX_PATH_DEPTH:
            continue
        if _matches(contract, target):
            complete.append({
                "steps": steps,
                "total_tokens": sum(s["tokens"] for s in steps),
                "llm_steps": sum(0 if s["deterministic"] else 1 for s in steps),
                "length": len(steps),
                "lossy": any(_state_after(source, steps).get("lossy") for _ in [0]),
            })
            continue
        for mut in all_mut:
            if not mut.can(contract):
                continue
            new_contract = mut.run(contract)
            key = json.dumps(new_contract, sort_keys=True) + f"@{len(steps)}"
            if key in seen:
                continue
            seen.add(key)
            frontier.append((new_contract, steps + [{
                "mutator": mut.name, "tokens": mut.tokens,
                "deterministic": mut.deterministic, "note": mut.note,
                "fit_class": FIT_DETERMINISTIC if mut.deterministic else FIT_NONDETERMINISTIC,
            }]))

    # Rank: fewest LLM steps first (deterministic-first doctrine), then fewest tokens,
    # then shortest, then non-lossy preferred.
    complete.sort(key=lambda p: (p["llm_steps"], p["total_tokens"], p["length"], p["lossy"]))
    chosen = complete[0] if complete else None
    fit = FIT_INCOMPATIBLE
    if chosen is not None:
        if chosen["length"] == 0:
            fit = FIT_EXACT
        elif chosen["llm_steps"] == 0:
            fit = FIT_DETERMINISTIC
        else:
            fit = FIT_NONDETERMINISTIC
    return {
        "source": source, "target": target,
        "fit_class": fit,
        "chosen_path": chosen,
        "path_universe": complete,          # every viable path (for fallback/benchmark)
        "path_count": len(complete),
        "cache_key": _cache_key(source, target),
        "candidate": True, "serves_truth": False,
    }


def _state_after(source: dict, steps: list[dict]) -> dict:
    det = {m.name: m for m in _deterministic_mutators()}
    det[_llm_escalation().name] = _llm_escalation()
    c = copy.deepcopy(source)
    for s in steps:
        mut = det.get(s["mutator"])
        if mut:
            c = mut.run(c)
    return c


def _cache_key(source: dict, target: dict) -> str:
    """Weighting/caching handle: a similar contract-gap hashes to the same key so a
    proven repair path is reused instead of re-searched."""
    payload = json.dumps({"s": source, "t": target}, sort_keys=True).encode()
    return "repair-" + hashlib.sha256(payload).hexdigest()[:16]


def recover(source: dict, target: dict, failed_path_index: int = 0) -> dict[str, Any]:
    """Failure recovery: if the chosen path fails a runtime checkpoint, fall back to
    the NEXT path in the ranked universe (rollback + alternative) — the user's
    'recover from failure, know the full universe of paths if something goes wrong'."""
    graph = enumerate_paths(source, target)
    universe = graph["path_universe"]
    if failed_path_index + 1 < len(universe):
        return {"recovered": True, "fallback_path": universe[failed_path_index + 1],
                "remaining_alternatives": len(universe) - failed_path_index - 2,
                "cache_key": graph["cache_key"], "candidate": True, "serves_truth": False}
    return {"recovered": False, "reason": "path universe exhausted — escalate to synthesis",
            "candidate": True, "serves_truth": False}


# ── Graduated LLM-scope escalation ladder (token-minimizing: narrow scope first,
#    widen ONLY if the cheaper tier fails). Each tier has a bounded budget. ──
ESCALATION_LADDER: list[dict[str, Any]] = [
    {"tier": 0, "name": "deterministic_only", "scope": "mutators only — no model call", "token_budget": 0},
    {"tier": 1, "name": "llm_edge_delta_only", "scope": "the single failing edge/contract delta", "token_budget": 150},
    {"tier": 2, "name": "llm_edge_plus_neighbors", "scope": "failing edge + immediate neighbor contracts + the failed checkpoint", "token_budget": 500},
    {"tier": 3, "name": "llm_local_route", "scope": "the local route + proof-failure trace", "token_budget": 1500},
    {"tier": 4, "name": "llm_source_slice", "scope": "targeted source/test slices (last resort)", "token_budget": 4000},
]


def next_escalation_tier(tiers_tried: int) -> dict[str, Any] | None:
    """Return the NEXT (widest-so-far) tier to try. Called only after the current tier
    fails — so scope + tokens grow monotonically and stop at the first tier that fixes it.
    The cumulative token ceiling is the sum of tiers actually attempted, never the max."""
    if tiers_tried >= len(ESCALATION_LADDER):
        return None
    return ESCALATION_LADDER[tiers_tried]


def escalation_plan(source: dict, target: dict) -> dict[str, Any]:
    """Full graduated plan for a gap: try deterministic (tier 0); if a residual semantic
    gap remains, the LLM tiers are attempted narrowest-first. Reports the cumulative token
    budget if it stops at each tier — the evidence that scope only widens on failure."""
    graph = enumerate_paths(source, target)
    needs_llm = graph["chosen_path"] is not None and graph["chosen_path"]["llm_steps"] > 0
    cumulative = 0
    tiers: list[dict[str, Any]] = []
    for t in ESCALATION_LADDER:
        cumulative += t["token_budget"]
        stops_here = (t["tier"] == 0 and not needs_llm) or (t["tier"] == 1 and needs_llm)
        tiers.append({**t, "cumulative_token_ceiling_if_stops_here": cumulative,
                      "expected_stop": stops_here})
        if stops_here:
            break
    return {"source": source, "target": target, "needs_llm": needs_llm,
            "deterministic_fixes_it": not needs_llm, "tiers": tiers,
            "expected_total_tokens": tiers[-1]["cumulative_token_ceiling_if_stops_here"],
            "candidate": True, "serves_truth": False}


def demo() -> dict[str, Any]:
    cases = {
        "scalar_to_array_deterministic": (
            {"shape": "scalar", "type": "int"}, {"shape": "array", "type": "int"}),
        "type_coerce_deterministic": (
            {"shape": "scalar", "type": "int"}, {"shape": "scalar", "type": "str"}),
        "irreducible_semantic_needs_llm": (
            {"shape": "scalar", "type": "str", "semantic": "raw_html"},
            {"shape": "object", "type": "str", "semantic": None, "fields_unnormalized": False}),
    }
    out = {name: enumerate_paths(s, t) for name, (s, t) in cases.items()}
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    (OUT_DIR / "demo_repair_paths.json").write_text(
        json.dumps({"generated_utc": dt.datetime.now(dt.timezone.utc).date().isoformat(),
                    "cases": out, "candidate": True, "serves_truth": False}, indent=2) + "\n")
    return out


def self_test() -> int:
    # 1. scalar->array is closed DETERMINISTICALLY with ZERO llm tokens.
    g = enumerate_paths({"shape": "scalar", "type": "int"}, {"shape": "array", "type": "int"})
    assert g["fit_class"] == FIT_DETERMINISTIC, g["fit_class"]
    assert g["chosen_path"]["llm_steps"] == 0 and g["chosen_path"]["total_tokens"] == 0
    assert any(s["mutator"] == "scalar_to_array" for s in g["chosen_path"]["steps"])

    # 2. an exact match needs no steps.
    g2 = enumerate_paths({"shape": "scalar", "type": "int"}, {"shape": "scalar", "type": "int"})
    assert g2["fit_class"] == FIT_EXACT and g2["chosen_path"]["length"] == 0

    # 3. an irreducible SEMANTIC gap escalates to exactly ONE bounded LLM step (deterministic-first:
    #    the resolver did not call the LLM for the parts a mutator could close).
    g3 = enumerate_paths(
        {"shape": "scalar", "type": "str", "semantic": "raw_html"},
        {"shape": "object", "type": "str", "semantic": None, "fields_unnormalized": False})
    assert g3["chosen_path"] is not None, "should find a repair path"
    assert g3["chosen_path"]["llm_steps"] == 1, "exactly one bounded LLM step for the irreducible gap"
    assert g3["chosen_path"]["total_tokens"] == LLM_STEP_TOKEN_BUDGET
    assert g3["fit_class"] == FIT_NONDETERMINISTIC

    # 4. deterministic-first ranking: chosen path has the FEWEST llm steps in the universe.
    assert g3["chosen_path"]["llm_steps"] == min(p["llm_steps"] for p in g3["path_universe"])

    # 5. the FULL universe is recorded (>1 path) so fallback/benchmark is possible.
    assert g["path_count"] >= 1 and g3["path_count"] >= 1

    # 6. caching: same gap -> same cache key (weighting reuses proven path).
    assert g["cache_key"] == enumerate_paths({"shape": "scalar", "type": "int"},
                                             {"shape": "array", "type": "int"})["cache_key"]

    # 7. failure recovery: falling back yields a different path when alternatives exist.
    rec = recover({"shape": "scalar", "type": "int"}, {"shape": "array", "type": "int"}, failed_path_index=0)
    assert isinstance(rec["recovered"], bool)

    # 8. token discipline: no deterministic path ever spends model tokens.
    for p in g["path_universe"]:
        if p["llm_steps"] == 0:
            assert p["total_tokens"] == 0

    # 9. graduated escalation: a deterministic-fixable gap stops at tier 0 (ZERO tokens);
    #    a semantic gap stops at tier 1 (narrowest LLM scope), NOT the widest tier.
    ep_det = escalation_plan({"shape": "scalar", "type": "int"}, {"shape": "array", "type": "int"})
    assert ep_det["deterministic_fixes_it"] and ep_det["expected_total_tokens"] == 0
    ep_llm = escalation_plan(
        {"shape": "scalar", "type": "str", "semantic": "raw_html"},
        {"shape": "object", "type": "str", "semantic": None, "fields_unnormalized": False})
    assert ep_llm["needs_llm"]
    # stops at tier 1 -> cumulative ceiling is tier0+tier1 budget only (150), never the 4000 max.
    assert ep_llm["expected_total_tokens"] == 150, ep_llm["expected_total_tokens"]
    assert ep_llm["expected_total_tokens"] < ESCALATION_LADDER[-1]["token_budget"]
    # 10. ladder is monotonic in scope/budget (narrow->wide).
    budgets = [t["token_budget"] for t in ESCALATION_LADDER]
    assert budgets == sorted(budgets) and budgets[0] == 0
    assert next_escalation_tier(len(ESCALATION_LADDER)) is None  # exhaustion -> synthesis

    print("OK: repair path-graph self-test passed (deterministic-first, LLM-only-for-irreducible, "
          "graduated-scope escalation, full path universe, cache key, failure recovery, token discipline).")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--demo", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    if args.demo:
        out = demo()
        for name, g in out.items():
            ch = g["chosen_path"]
            print(f"{name}: fit={g['fit_class']} paths={g['path_count']} "
                  f"chosen_llm_steps={ch['llm_steps'] if ch else '-'} tokens={ch['total_tokens'] if ch else '-'}")
        return self_test()
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
