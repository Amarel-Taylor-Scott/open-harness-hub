"""src.baltor.runtime.registry.preference_graph — NUMERIC, non-fragile preference graph for capability-slot
adapter selection.

WHY: hard-coded string roles ('primary'/'fallback'/'candidate') + exact-string matches are fragile — adding
an adapter, relabeling a role, or enriching a provider string breaks selection/proofs (this bit us twice on
2026-06-06). This layer makes selection NUMERIC: each adapter carries a `priority` number; the order is by
priority (desc). Adding/renaming/relabeling an adapter never changes the order unless its NUMBER changes.

GRAPH: nodes = adapters; edges are induced by the numeric priorities — a higher-priority node `falls_back_to`
the next lower one, OR is an `alternative_of` it when their priorities are within TIE_BAND (interchangeable).
The resolved `order` is the preference chain (a monotone-non-increasing path → a DAG, never a cycle).

NON-FRAGILE / backward-compatible: roles remain ADVISORY labels. When an adapter declares no numeric
`priority`, one is DERIVED from its role (ROLE_DEFAULT_PRIORITY); an unknown/missing role yields 0 (sorts to
the bottom) instead of raising. So slots migrate gradually — add numbers where the role-derived default is
wrong (e.g. prefer a reversible compressor over a token-pruner even if the latter is labeled 'primary').
Pure + deterministic (all inputs injected; stable tie-break by adapter_id).
"""
import json
from scripts._repo_paths import resource as _resource
from pathlib import Path

#: advisory roles → a DEFAULT numeric priority (used only when an adapter declares no explicit `priority`).
#: Spread out so an explicit number can sit cleanly between two role tiers.
ROLE_DEFAULT_PRIORITY = {"primary": 80, "fallback": 50, "stub": 20, "foil": 0, "reference": 0}
_UNKNOWN_ROLE_PRIORITY = 0.0
#: adapters whose priorities are within this delta are ALTERNATIVES (interchangeable), not strict fallbacks.
TIE_BAND = 5.0

_ARCH = _resource("architecture")
#: edge-type numeric codes (display label → code) — control logic uses the CODE, never the label string.
EDGE_TYPE_CODE = {"falls_back_to": 160, "alternative_of": 120}  # FALLBACK_AFTER_FAILURE / ALTERNATIVE_TO
#: legacy catalog status labels → numeric code (bridge while slots migrate to numeric `status_code`). The new
#: vocabulary's own labels are loaded from _repos/shared-backend-components/architecture/provider_status_codes.json (single source).
_LEGACY_STATUS_CODE = {"active": 50, "candidate": 30, "experimental": 20, "deprecated": 80,
                       "quarantined": 10, "replaced": 80, "foil": 10, "reference": 10}
_STATUS_CODE_CACHE: dict | None = None


def _status_label_to_code() -> dict:
    """label → numeric status code, sourced from _repos/shared-backend-components/architecture/provider_status_codes.json (the single source),
    merged with the legacy-catalog compat labels. Cached; never raises (falls back to legacy map alone)."""
    global _STATUS_CODE_CACHE
    if _STATUS_CODE_CACHE is None:
        m = dict(_LEGACY_STATUS_CODE)
        try:
            data = json.loads((_ARCH / "provider_status_codes.json").read_text(encoding="utf-8"))
            for entry in data.get("codes", []):
                if isinstance(entry.get("label"), str) and isinstance(entry.get("code"), int):
                    m[entry["label"]] = entry["code"]
        except Exception:
            pass  # non-fragile: a missing/garbled vocabulary file degrades to the legacy map, never crashes
        _STATUS_CODE_CACHE = m
    return _STATUS_CODE_CACHE


def status_code(adapter: dict) -> int:
    """Numeric status of one adapter for control logic. Explicit `status_code` wins; else map the `status`
    LABEL via the vocabulary; else 0 (never branch on the label string itself)."""
    sc = adapter.get("status_code")
    if isinstance(sc, int) and not isinstance(sc, bool):
        return sc
    return int(_status_label_to_code().get(adapter.get("status"), 0))


def adapter_priority(adapter: dict) -> float:
    """The numeric preference of one adapter. Explicit `priority` wins; else derive from the advisory role;
    unknown/missing role → 0 (never raises — that is the non-fragility)."""
    p = adapter.get("priority")
    if isinstance(p, (int, float)) and not isinstance(p, bool):
        return float(p)
    return float(ROLE_DEFAULT_PRIORITY.get(adapter.get("role"), _UNKNOWN_ROLE_PRIORITY))


def _runnable(adapter: dict, available: set | None, health: dict | None) -> bool:
    aid = adapter.get("adapter_id")
    if available is not None and aid not in available:
        return False
    if health is not None and health.get(aid, True) is False:
        return False
    return True


def resolve_order(adapters: list[dict], *, health: dict | None = None, available: set | None = None,
                  runnable_only: bool = False) -> list[dict]:
    """Adapters ordered by preference: priority DESC, then healthy-first, then stable adapter_id. No string-role
    gating, no exact-name match — only the numbers (and optional availability/health) decide. Deterministic."""
    items = list(adapters)
    if runnable_only:
        items = [a for a in items if _runnable(a, available, health)]

    def _key(a: dict):
        unhealthy = 0 if (health or {}).get(a.get("adapter_id"), True) else 1
        return (-adapter_priority(a), unhealthy, a.get("adapter_id", ""))

    return sorted(items, key=_key)


def preference_graph(adapters: list[dict]) -> dict:
    """A numeric graph view: nodes (adapter_id, priority, role, status) in preference order + edges between
    consecutive nodes (`falls_back_to` when the priority gap exceeds TIE_BAND, else `alternative_of`) carrying
    the numeric weight = priority delta. The order is a monotone-non-increasing chain → acyclic by construction.
    `primary` = the top node; `alternatives` = each tie-band group of interchangeable adapters."""
    order = resolve_order(adapters)
    nodes = [{"adapter_id": a.get("adapter_id"), "priority": adapter_priority(a),
              "role": a.get("role"), "status": a.get("status"), "status_code": status_code(a)} for a in order]
    edges = []
    for hi, lo in zip(nodes, nodes[1:]):
        delta = round(hi["priority"] - lo["priority"], 3)
        kind = "alternative_of" if delta <= TIE_BAND else "falls_back_to"
        edges.append({"from": hi["adapter_id"], "to": lo["adapter_id"], "kind": kind,
                      "edge_type_code": EDGE_TYPE_CODE[kind], "weight": delta})
    # group adapters that are mutually within TIE_BAND of the top of their run = interchangeable alternatives
    alternatives: list[list[str]] = []
    run: list[dict] = []
    for n in nodes:
        if run and (run[0]["priority"] - n["priority"]) <= TIE_BAND:
            run.append(n)
        else:
            if len(run) > 1:
                alternatives.append([x["adapter_id"] for x in run])
            run = [n]
    if len(run) > 1:
        alternatives.append([x["adapter_id"] for x in run])
    return {"nodes": nodes, "edges": edges, "order": [n["adapter_id"] for n in nodes],
            "primary": nodes[0]["adapter_id"] if nodes else None, "alternatives": alternatives,
            "acyclic": all(e["weight"] >= 0 for e in edges)}


__all__ = ["adapter_priority", "status_code", "resolve_order", "preference_graph",
           "ROLE_DEFAULT_PRIORITY", "TIE_BAND", "EDGE_TYPE_CODE"]
