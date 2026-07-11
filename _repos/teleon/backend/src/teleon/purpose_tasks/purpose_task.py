"""src.teleon.purpose_tasks.purpose_task — minimal PurposeTask controller (PoC) over the built Parallel-Path Engine.

A PurposeTask is declared by INTENT, not code:
    {task_id, purpose, capability_slot, input_contract, output_contract,
     success_criteria, promotion_criteria, eval_suite, current_impl_id, alternatives, rollback_target}

`eval_suite` (a.k.a. the benchmark) is the FIRST-CLASS declared "what DONE means": a user hands Teleon the
evaluation system (an inline `examples` suite OR a `benchmark_ref`) that the gate scores a candidate against —
"the benchmark IS the spec" (see _repos/teleon/backend/src/teleon/purpose_tasks/eval_suite.py + _repos/shared-backend-components/docs/architecture/eval-as-contract.md).
The spec is a plain dict everywhere (provision/run/adapt all take dicts); `PurposeTaskSpec` is a thin builder
that round-trips that dict and attaches/normalizes the eval_suite, and `eval_suite_for(spec)` is the seam the
runtime gate + compiler read instead of a hardcoded example suite.

`provision` binds the highest-priority implementation for the task's capability_slot FROM a registry (the
provision-by-capability surface — no per-task wiring code). `run_current` runs the cheap deterministic hot
path. `evaluate_health` checks the result against success_criteria. `adapt` (on drift) runs the next candidate
implementation SIDE-BY-SIDE against the current one via the governed Parallel-Path Engine and promotes ONLY on a
passing PathPromotionDecision, keeping the prior implementation as a fallback (rollback_target). Agents PROPOSE;
the gate DISPOSES. Pure + deterministic (all inputs injected: registry, input_snapshot, now). No LLM in the hot
path; no second runtime/ledger/registry; a candidate is never served before promotion.
"""
from __future__ import annotations

from typing import Any, Callable

from src.teleon.experiments import parallel_paths as _pp
from src.teleon.experiments import path_comparator as _pc
from src.teleon.experiments import path_promotion as _ppr
from src.teleon.purpose_tasks import eval_suite as _es

#: contract field carrying the eval/benchmark that defines DONE (see eval_suite.py). Named once here.
EVAL_SUITE_FIELD = "eval_suite"

#: registry shape: {capability_slot: [{"impl_id": str, "priority": int|float, "handler": Callable[[input], RunnerResult]}]}
#: handler returns a RunnerResult dict: {output, output_contract, cost, latency_ms, error, source_handles, ...}
Registry = dict[str, list[dict[str, Any]]]


def _impls(registry: Registry, slot: str) -> list[dict[str, Any]]:
    impls = registry.get(slot) or []
    if not impls:
        raise ValueError(f"no implementation registered for capability_slot {slot!r}")
    # provision-by-capability: order by NUMERIC priority (desc), stable by impl_id — not by hard-coded choice.
    return sorted(impls, key=lambda i: (-float(i.get("priority", 0)), i["impl_id"]))


def provision(spec: dict[str, Any], registry: Registry) -> dict[str, Any]:
    """Bind an implementation for spec['capability_slot'] by numeric priority. Returns an updated spec with
    current_impl_id + alternatives. No code is written per task — selection is by capability + priority."""
    ordered = _impls(registry, spec["capability_slot"])
    out = dict(spec)
    out["current_impl_id"] = ordered[0]["impl_id"]
    out["alternatives"] = [i["impl_id"] for i in ordered[1:]]
    out.setdefault("rollback_target", "")   # '' = no promotion yet (kept a string for PurposeTaskSpec)
    return out


def _guarded_call(impl: dict[str, Any], input_snapshot: Any, output_contract: str = "") -> dict[str, Any]:
    """Run ONE implementation's handler, converting a RAISED exception or a non-RunnerResult return into a
    structured failure result (output '', error set, crashed=True) instead of propagating. Shared by the guarded
    hot path AND the side-by-side adapt runner, so neither can be crashed — or fooled into a fabricated success —
    by a misbehaving implementation. Pure + deterministic."""
    try:
        res = impl["handler"](input_snapshot)
    except Exception as e:                       # never propagate → convert to a scored failure / drift signal
        return {"output": "", "output_contract": output_contract, "cost": float(impl.get("error_cost", 0.0)),
                "latency_ms": 0, "error": {"type": type(e).__name__, "message": str(e)}, "source_handles": [],
                "impl_id": impl.get("impl_id"), "crashed": True}
    if not isinstance(res, dict):                # a non-RunnerResult is a contract breach, not a fabricated success
        return {"output": "", "output_contract": output_contract, "cost": 0.0, "latency_ms": 0,
                "error": {"type": "ContractError", "message": "handler did not return a RunnerResult dict"},
                "source_handles": [], "impl_id": impl.get("impl_id"), "crashed": True}
    return res


def _runner(registry: Registry, slot: str) -> Callable[[dict[str, Any], Any], dict[str, Any]]:
    by_id = {i["impl_id"]: i for i in registry[slot]}

    def runner(path: dict[str, Any], input_snapshot: Any) -> dict[str, Any]:
        # GUARDED: a crashing / non-compliant impl becomes a scored failure result — it never aborts the
        # side-by-side run (a crashing baseline still lets a healthy candidate be judged + promoted).
        return _guarded_call(by_id[path["path_id"]], input_snapshot, path.get("output_contract", ""))

    return runner


def run_current(spec: dict[str, Any], registry: Registry, input_snapshot: Any) -> dict[str, Any]:
    """Run the cheap deterministic hot path = the currently-bound implementation. No LLM, no side-by-side.
    Assumes a well-behaved handler (returns a RunnerResult); use run_current_guarded for untrusted handlers."""
    by_id = {i["impl_id"]: i for i in registry[spec["capability_slot"]]}
    return by_id[spec["current_impl_id"]]["handler"](input_snapshot)


def run_current_guarded(spec: dict[str, Any], registry: Registry, input_snapshot: Any) -> dict[str, Any]:
    """ROBUST hot-path entry: run the bound implementation but NEVER let a misbehaving handler crash the
    controller or fabricate a success. A handler that RAISES (bug, timeout, resource error) or returns a
    non-RunnerResult is converted into a structured DRIFT result — `output=''`, `error` set, `crashed=True`,
    `source_handles=[]` — so evaluate_health flags drift (`meets=False`) and adapt/rollback can respond. A raised
    or broken handler can therefore never look like a served answer. Pure + deterministic (no now/IO of its own).

    The hot path stays cheap on the happy path (delegates to the handler directly); the guard only shapes failure."""
    slot = spec["capability_slot"]
    impl = {i["impl_id"]: i for i in registry[slot]}[spec["current_impl_id"]]
    return _guarded_call(impl, input_snapshot, spec.get("output_contract", ""))


def evaluate_health(result: dict[str, Any], success_criteria: dict[str, Any], *,
                    held_out_strings: tuple[str, ...] = ()) -> dict[str, Any]:
    """Deterministic health check of a hot-path result vs success_criteria. Returns {meets, drift:[dims]}."""
    drift: list[str] = []
    if result.get("error"):
        drift.append("error")
    max_cost = success_criteria.get("max_cost")
    if max_cost is not None and float(result.get("cost", 0.0)) > float(max_cost):
        drift.append("cost")
    min_cov = success_criteria.get("min_source_handles")
    if min_cov is not None and len(result.get("source_handles") or []) < int(min_cov):
        drift.append("source_handles")
    text = str(result.get("output", ""))
    for needle in held_out_strings:
        if needle in text:
            drift.append("held_out_leak")
            break
    return {"meets": not drift, "drift": drift}


def adapt(spec: dict[str, Any], registry: Registry, input_snapshot: Any, *, now: str,
          promotion_criteria: dict[str, Any], candidate_impl_id: str | None = None,
          held_out_strings: tuple[str, ...] = ()) -> dict[str, Any]:
    """Self-adapt on drift: run the next candidate implementation SIDE-BY-SIDE vs the current one through the
    Parallel-Path Engine and promote ONLY on a passing PathPromotionDecision. The prior impl is kept as a
    fallback (rollback_target). A candidate is NEVER served before promotion. Returns
    {promoted, decision, run, report, served_path_id, spec}."""
    slot = spec["capability_slot"]
    candidate_id = candidate_impl_id or (spec.get("alternatives") or [None])[0]
    if candidate_id is None:
        return {"promoted": False, "reason": "no alternative implementation to try",
                "served_path_id": spec["current_impl_id"], "spec": dict(spec)}

    runner = _runner(registry, slot)
    oc = spec["output_contract"]
    baseline_path = {"path_id": spec["current_impl_id"], "mode": "baseline", "output_contract": oc}
    candidate_path = {"path_id": candidate_id, "mode": "candidate", "output_contract": oc}

    run = _pp.run_parallel(slot, input_snapshot, baseline_path, [candidate_path], runner=runner, now=now)
    report = _pc.compare(run, now=now, held_out_strings=list(held_out_strings))

    # cost gate computed from the run (candidate must not be more expensive than the baseline, with tolerance)
    base_cost = float(run["baseline_result"]["cost"])
    cand_cost = float(run["candidate_results"][0]["cost"])
    tol = float(promotion_criteria.get("cost_tolerance", 0.0))
    cost_ok = cand_cost <= base_cost * (1.0 + tol)

    decision = _ppr.decide(report, promotion_criteria, candidate_path_id=candidate_id, now=now,
                           cost_acceptable=cost_ok)
    promoted = _ppr.is_promote_authorized(decision)

    new_spec = dict(spec)
    if promoted:
        # promote the candidate; keep the PRIOR current impl as a fallback alternative (rollback_target).
        prior = spec["current_impl_id"]
        new_spec["current_impl_id"] = candidate_id
        new_spec["alternatives"] = [prior] + [a for a in spec.get("alternatives", []) if a != candidate_id]
        new_spec["rollback_target"] = decision["rollback_target"]

    return {"promoted": promoted, "decision": decision, "run": run, "report": report,
            "served_path_id": run["served_path_id"], "spec": new_spec}


def rollback(spec: dict[str, Any], registry: Registry, *, to: str | None = None) -> dict[str, Any]:
    """Revert the bound implementation to a preserved rollback target — promotion is ALWAYS reversible.

    `to` overrides spec['rollback_target'] (roll back to any earlier registered impl, not just the last). The
    currently-served implementation is DEMOTED to the front of `alternatives`, never deleted (lossless — it stays
    re-promotable through `adapt` + the gate). The pending rollback_target is consumed (set to ''); a future
    promotion records a new one.

    Fails CLOSED — returns rolled_back=False with the spec UNCHANGED (never blanks current_impl_id) when:
      * there is no rollback target (nothing recorded and no `to`),
      * the target is not a registered implementation for the slot,
      * the target is already the current implementation (no-op).
    Pure + deterministic (no I/O, no now)."""
    slot = spec["capability_slot"]
    registered = {i["impl_id"] for i in (registry.get(slot) or [])}
    target = to or spec.get("rollback_target") or ""
    current = spec.get("current_impl_id")
    if not target:
        return {"rolled_back": False, "reason": "no rollback target recorded", "spec": dict(spec)}
    if target not in registered:
        return {"rolled_back": False, "reason": f"rollback target {target!r} is not a registered implementation",
                "spec": dict(spec)}
    if target == current:
        return {"rolled_back": False, "reason": "already serving the rollback target", "spec": dict(spec)}
    new_spec = dict(spec)
    new_spec["current_impl_id"] = target
    # demote the regressed impl to the FRONT of alternatives (lossless + first to be re-tried by adapt); drop the
    # target from alternatives (it is current now); dedup, stable order.
    prior_alts = [a for a in spec.get("alternatives", []) if a not in (target, current)]
    new_spec["alternatives"] = ([current] + prior_alts) if current else prior_alts
    new_spec["rollback_target"] = ""   # pending rollback consumed; the next promotion records a fresh target
    return {"rolled_back": True, "from": current, "to": target, "spec": new_spec}


# ---------------------------------------------------------------------------
# eval_suite (the benchmark) as a first-class contract field
# ---------------------------------------------------------------------------

def _is_model_built(spec: dict[str, Any]) -> bool:
    """A capability the MODEL builds/performs (vs a fixed deterministic impl) must be gated on a non-empty
    eval suite. We treat a task as model-built when it declares a `build_mode`/`mode` of 'model' OR carries
    `model_built: true`; absent any signal we assume NOT model-built (so a deterministic PoC spec without an
    eval_suite stays valid — backward compatible). The runtime's own gate still applies regardless."""
    if bool(spec.get("model_built")):
        return True
    return str(spec.get("build_mode") or spec.get("mode") or "").lower() == "model"


def eval_suite_for(spec: dict[str, Any] | "PurposeTaskSpec") -> dict[str, Any] | None:
    """Return the NORMALIZED eval_suite the runtime gate + compiler consume, or None if the task declares no
    eval_suite (backward compatible — older specs simply have no benchmark and fall back to the runtime's
    own hardcoded suite). This is the single seam: instead of reaching into a hardcoded CAPABILITIES suite,
    the gate calls `eval_suite_for(spec)` → uses `eval_suite.eval_pairs(...)` for the (input, expected) rows
    and `gate_threshold`/`holdout_policy`/`judge` for the gate. Raises ValueError (via normalize) if a
    present eval_suite is invalid — an unmeasurable 'done' is fail-closed, never silently dropped."""
    raw = spec.spec if isinstance(spec, PurposeTaskSpec) else spec
    suite = raw.get(EVAL_SUITE_FIELD)
    if suite is None:
        return None
    return _es.normalize_eval_suite(suite, model_built=_is_model_built(raw))


class PurposeTaskSpec:
    """A thin BUILDER/round-trip wrapper around a PurposeTask spec DICT (the spec stays a plain dict for
    provision/run/adapt — this never replaces it). It exists so a caller can attach + normalize the
    `eval_suite` ergonomically and round-trip losslessly: `PurposeTaskSpec.from_dict(d).to_dict()` returns an
    equal dict, and a `with_eval_suite(...)` constructor produces a spec whose eval_suite the gate can read.
    Pure + deterministic."""

    __slots__ = ("spec",)

    def __init__(self, spec: dict[str, Any]) -> None:
        if not isinstance(spec, dict):
            raise TypeError(f"PurposeTaskSpec wraps a dict, got {type(spec).__name__}")
        self.spec = dict(spec)  # defensive copy — the wrapper owns its dict

    # --- round-trip -------------------------------------------------------
    @classmethod
    def from_dict(cls, spec: dict[str, Any]) -> "PurposeTaskSpec":
        return cls(spec)

    def to_dict(self) -> dict[str, Any]:
        """The underlying spec dict (a copy). Round-trips: from_dict(d).to_dict() == d."""
        return dict(self.spec)

    def __eq__(self, other: object) -> bool:
        if isinstance(other, PurposeTaskSpec):
            return self.spec == other.spec
        if isinstance(other, dict):
            return self.spec == other
        return NotImplemented

    def __repr__(self) -> str:
        return f"PurposeTaskSpec(task_id={self.spec.get('task_id')!r}, has_eval_suite={self.eval_suite is not None})"

    # --- eval_suite (the benchmark) --------------------------------------
    @property
    def eval_suite(self) -> dict[str, Any] | None:
        """The RAW declared eval_suite (as stored), or None. Use `normalized_eval_suite()` for the gate-ready
        form with defaults filled."""
        return self.spec.get(EVAL_SUITE_FIELD)

    def normalized_eval_suite(self) -> dict[str, Any] | None:
        """The gate-ready normalized eval_suite (defaults filled from the canonical gate constants), or None."""
        return eval_suite_for(self)

    def with_eval_suite(self, suite: dict[str, Any], *, model_built: bool | None = None,
                        normalize: bool = True) -> "PurposeTaskSpec":
        """Return a NEW PurposeTaskSpec carrying `suite` as its eval_suite. By default the suite is NORMALIZED
        + validated immediately (defaults filled from the canonical gate constants; an invalid suite raises
        ValueError now, not at gate time — fail-closed). Pass normalize=False to store the raw suite verbatim
        (still validated). `model_built` overrides the inferred model-built flag for the non-empty-examples
        rule; when None it is inferred from the spec (build_mode/mode/model_built)."""
        mb = _is_model_built(self.spec) if model_built is None else bool(model_built)
        stored = _es.normalize_eval_suite(suite, model_built=mb) if normalize else suite
        if not normalize:
            errs = _es.validate_eval_suite(suite, model_built=mb)
            if errs:
                raise ValueError("invalid eval_suite: " + "; ".join(errs))
        new = dict(self.spec)
        new[EVAL_SUITE_FIELD] = stored
        return PurposeTaskSpec(new)


__all__ = [
    "provision", "run_current", "run_current_guarded", "evaluate_health", "adapt", "rollback",
    "PurposeTaskSpec", "eval_suite_for", "EVAL_SUITE_FIELD",
]
