"""src.teleon.lift.adoption — the Teleon Lift adoption ladder + baseline preservation.

The legacy workload becomes an ImplementationCandidate (status `imported_baseline`) that IS the rollback target —
never a live/managed PurposeTask. The AdoptionPlan starts at `discover` (read-only). Moving to a managed mode
(level >= MANAGED_MIN_LEVEL, where the platform can affect production) REQUIRES a human-confirmed purpose — this
is the line between safe adoption and an unsafe takeover. Pure + deterministic.
"""
from __future__ import annotations

from typing import Any

from . import model

_ADOPTION_PLAN_SCHEMA = "AdoptionPlan"


def _ladder_by_mode() -> dict[str, dict]:
    return {m["mode"]: m for m in model.ADOPTION_LADDER}


def mode_record(mode: str) -> dict | None:
    return _ladder_by_mode().get(mode)


def next_mode(mode: str) -> str | None:
    modes = [m["mode"] for m in model.ADOPTION_LADDER]
    i = modes.index(mode) if mode in modes else -1
    return modes[i + 1] if 0 <= i < len(modes) - 1 else None


def baseline_implementation(workload: dict, purpose_draft: dict) -> dict[str, Any]:
    """The legacy workload as the imported BASELINE implementation candidate (the rollback target)."""
    return {
        "impl_id": purpose_draft["baseline_implementation_id"],
        "status": "imported_baseline",
        "is_rollback_target": True,
        "source_workload_id": workload["id"],
        "runtime_binding": {
            "class": workload.get("runtime_class_guess"),
            "provider": f'{workload["source"]}:{workload["native_kind"]}:{workload["native_name"]}',
            "is_current": True,
        },
    }


def build_adoption_plan(workload: dict, purpose_draft: dict, *, human_confirmed_purpose: bool = False,
                        current_mode: str = model.ENTRY_MODE) -> dict[str, Any]:
    """Build an AdoptionPlan for a freshly lifted workload. Defaults: read-only `discover`, purpose UNconfirmed,
    not manageable. `may_manage` becomes true only with a human-confirmed purpose AND a managed-level mode."""
    rec = mode_record(current_mode) or mode_record(model.ENTRY_MODE)
    affects = bool(rec["affects_production"])
    may_manage = human_confirmed_purpose and rec["level"] >= model.MANAGED_MIN_LEVEL
    base = baseline_implementation(workload, purpose_draft)
    return {
        "schema_version": _ADOPTION_PLAN_SCHEMA,
        "workload_id": workload["id"],
        "purpose_draft_name": purpose_draft["name"],
        "entry_mode": model.ENTRY_MODE,
        "current_mode": rec["mode"],
        "current_level": rec["level"],
        "reads_only": bool(rec["reads_only"]),
        "affects_production": affects,
        "ladder": model.ADOPTION_LADDER,
        "baseline_implementation": base,
        "rollback_target": base["impl_id"],
        "human_confirmed_purpose": bool(human_confirmed_purpose),
        "may_manage": bool(may_manage),
        "recommended_next": next_mode(rec["mode"]),
    }


def set_mode(plan: dict, mode: str, *, human_confirmed_purpose: bool | None = None) -> dict[str, Any]:
    """Return a copy of the plan moved to `mode`. ENFORCED: a managed mode (level >= MANAGED_MIN_LEVEL, which can
    affect production) is REFUSED unless the purpose is human-confirmed — the plan stays put with a `blocked`
    reason. Read-only modes (discover/model/observe) and shadow are always allowed."""
    rec = mode_record(mode)
    if rec is None:
        out = dict(plan)
        out["blocked"] = f"unknown adoption mode {mode!r}"
        return out
    confirmed = plan["human_confirmed_purpose"] if human_confirmed_purpose is None else bool(human_confirmed_purpose)
    if rec["level"] >= model.MANAGED_MIN_LEVEL and not confirmed:
        out = dict(plan)
        out["blocked"] = (f"cannot enter managed mode {mode!r} (level {rec['level']}, affects production) "
                          f"without a human-confirmed purpose")
        return out
    out = dict(plan)
    out.pop("blocked", None)
    out["current_mode"] = rec["mode"]
    out["current_level"] = rec["level"]
    out["reads_only"] = bool(rec["reads_only"])
    out["affects_production"] = bool(rec["affects_production"])
    out["human_confirmed_purpose"] = confirmed
    out["may_manage"] = confirmed and rec["level"] >= model.MANAGED_MIN_LEVEL
    out["recommended_next"] = next_mode(rec["mode"])
    return out


def may_manage(plan: dict) -> bool:
    """True iff the plan is at a managed level with a human-confirmed purpose."""
    return bool(plan.get("human_confirmed_purpose")) and int(plan.get("current_level", 0)) >= model.MANAGED_MIN_LEVEL


__all__ = ["mode_record", "next_mode", "baseline_implementation", "build_adoption_plan", "set_mode", "may_manage"]
