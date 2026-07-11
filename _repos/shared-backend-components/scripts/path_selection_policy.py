#!/usr/bin/env python3
"""scripts.path_selection_policy — turn the path bake-off leaderboard into an automatic per-task ROUTING decision.

The path bake-off (``_repos/shared-backend-components/scripts/run_path_bakeoff.py``) races N processing paths on ~24 tasks and emits a per-task-class
leaderboard (``data/dev-intel/path_bakeoff/bakeoff_leaderboard_<date>.json``). A leaderboard is analysis — it does
not, by itself, route anything. This module is the missing DECISION layer: it reads the leaderboard, derives a
ROUTING TABLE ``{task_class -> ranked_path_ids (+ rationale)}``, and exposes ``select_path(task_features)`` which
classifies a task by simple deterministic features and returns the leaderboard winner PLUS ordered fallbacks — so it
is always a PORTFOLIO decision (never a lock-in), and every decision is recorded to a policy ledger for later
refinement. As the bake-off re-runs, the routing table (and therefore every future decision) updates automatically:
"find what makes the most sense" made durable + adaptive.

Repo law kept: a routing table / policy ledger is candidate analysis, not truth — every emitted row is
``candidate=true / serves_truth=false`` (mirroring the leaderboard it reads). This module is ADD-ONLY and REUSES
existing machinery (it imports the bake-off leaderboard, the retrieval-backend portfolio resolver, and — when the
concurrent runtime modules are present — the primitive composer/search/edge/composability/proof helpers) rather than
reinventing any of them. Every code path is offline + deterministic (pass a fixed ``now`` string; no wall-clock/RNG
in ``--self-test``). CLI: ``--self-test`` (pure/offline) | ``--run [--date D]`` (writes the pack + appends a demo
decision to the ledger) | ``--explain`` (prints the routing table as markdown).
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import datetime as dt
import hashlib
import json
import sys
from pathlib import Path
from typing import Any

REPO = Path(__file__).resolve().parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

# ── canonical locations (single source; never hand-duplicated elsewhere) ──
BAKEOFF_DIR = _resource("data") / "dev-intel" / "path_bakeoff"
DEFAULT_LEADERBOARD = BAKEOFF_DIR / "bakeoff_leaderboard_2026-07-03.json"
POLICY_DIR = _resource("data") / "dev-intel" / "path_selection_policy"
DEFAULT_LEDGER = POLICY_DIR / "path_selection_ledger.jsonl"
BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
FIXED_NOW = "2026-07-03T00:00:00Z"  # deterministic clock for self-test / reproducible builds

# ── REUSE existing machinery (import, don't reinvent) ──
# retrieval-backend portfolio: the single source for which search methods exist + their wired/planned status.
try:  # pragma: no cover - import shape guard
    from scripts.build_retrieval_backend_portfolio import (  # type: ignore
        backends_of as _backends_of,
        dim_compatible as _dim_compatible,
        resolve_active_backends as _resolve_active_backends,
    )
    _RETRIEVAL_PORTFOLIO_AVAILABLE = True
except Exception:  # noqa: BLE001
    _backends_of = _dim_compatible = _resolve_active_backends = None  # type: ignore
    _RETRIEVAL_PORTFOLIO_AVAILABLE = False

# mutator substrate: proof-runner (used only to confirm the substrate is importable + honest reuse reporting).
try:  # pragma: no cover
    from scripts.mutator_registry import (  # type: ignore
        MUTATOR_REGISTRY as _MUTATOR_REGISTRY,
        apply_mutator as _apply_mutator,
        run_primitive_proof as _run_primitive_proof,
    )
    _MUTATOR_SUBSTRATE_AVAILABLE = True
except Exception:  # noqa: BLE001
    _MUTATOR_REGISTRY = None  # type: ignore
    _apply_mutator = _run_primitive_proof = None  # type: ignore
    _MUTATOR_SUBSTRATE_AVAILABLE = False

# concurrent-workflow modules — may not exist yet; import with graceful fallback so --self-test always passes.
try:  # pragma: no cover
    from scripts.primitive_runtime import compose_solution as _compose_solution  # type: ignore
except Exception:  # noqa: BLE001
    _compose_solution = None  # type: ignore
try:  # pragma: no cover
    from scripts.build_primitive_search_index import fast_search as _fast_search  # type: ignore
except Exception:  # noqa: BLE001
    _fast_search = None  # type: ignore
try:  # pragma: no cover
    from scripts.build_edge_type_retrofit import canonicalize_edge as _canonicalize_edge  # type: ignore
except Exception:  # noqa: BLE001
    _canonicalize_edge = None  # type: ignore
try:  # pragma: no cover
    from scripts.check_primitive_composability import composability_report as _composability_report  # type: ignore
except Exception:  # noqa: BLE001
    _composability_report = None  # type: ignore
try:  # pragma: no cover
    from scripts.prove_leaf_primitives import proven_primitive_index as _proven_primitive_index  # type: ignore
except Exception:  # noqa: BLE001
    _proven_primitive_index = None  # type: ignore


def reuse_availability() -> dict[str, Any]:
    """Honest report of which reused machinery is importable in this environment (never fabricated)."""
    return {
        "retrieval_backend_portfolio": _RETRIEVAL_PORTFOLIO_AVAILABLE,
        "mutator_substrate": _MUTATOR_SUBSTRATE_AVAILABLE,
        "compose_solution": _compose_solution is not None,
        "fast_search": _fast_search is not None,
        "canonicalize_edge": _canonicalize_edge is not None,
        "composability_report": _composability_report is not None,
        "proven_primitive_index": _proven_primitive_index is not None,
    }


# ──────────────────────────────────────────────────────────────────────────────
# Task classification — deterministic features -> task_class (the 5 bake-off classes + "unknown")
# ──────────────────────────────────────────────────────────────────────────────
MAIN_CLASSES: tuple[str, ...] = ("string_transform", "data_pipeline", "algorithm", "extraction", "agentic")
UNKNOWN_CLASS = "unknown"

# ordered most-specific-first so a generic token ("text") never shadows a specific one ("extract").
DOMAIN_KEYWORDS: list[tuple[str, tuple[str, ...]]] = [
    ("extraction", ("extract", "document", "parse", "ocr", "segment", "span", "entity", "field", "blob")),
    ("agentic", ("agent", "tool", "orchestrate", "autonomous", "goal", "action", "workflow")),
    ("data_pipeline", ("pipeline", "ingest", "etl", "load", "dedupe", "normalize", "records", "batch", "join")),
    ("algorithm", ("algorithm", "solve", "plan", "optimize", "search", "compute", "verify", "route")),
    ("string_transform", ("string", "text", "transform", "rewrite", "clean", "format", "reply")),
]


def _truthy(features: dict[str, Any], key: str, *fallback_keys: str) -> bool:
    """Read a boolean-ish feature, treating the presence of a non-empty ``*_type`` sibling as evidence."""
    if key in features:
        return bool(features[key])
    for fk in fallback_keys:
        if features.get(fk):
            return True
    return False


def classify_task(task_features: dict[str, Any]) -> str:
    """Map task features to one of the 5 bake-off task-classes, or ``"unknown"``.

    Features honored (all optional): ``domain`` (str), ``has_input_type``/``input_type``,
    ``has_output_type``/``output_type``, ``is_multi_step`` (bool). Pure + deterministic — same features in,
    same class out, no wall-clock/RNG."""
    domain = str(task_features.get("domain", "") or "").lower()
    # 1) explicit class name in the domain wins outright.
    for cls in MAIN_CLASSES:
        if cls in domain or cls.replace("_", " ") in domain:
            return cls
    # 2) keyword map (specificity-ordered).
    for cls, kws in DOMAIN_KEYWORDS:
        if any(kw in domain for kw in kws):
            return cls
    # 3) structural fallback — only when there is a real type signal to classify on.
    has_in = _truthy(task_features, "has_input_type", "input_type")
    has_out = _truthy(task_features, "has_output_type", "output_type")
    multi = bool(task_features.get("is_multi_step"))
    if has_in or has_out:
        return "data_pipeline" if multi else "string_transform"
    # 4) nothing to go on -> unknown (routes to the safe deterministic baseline).
    return UNKNOWN_CLASS


# ──────────────────────────────────────────────────────────────────────────────
# Leaderboard loading (real file if present, else a clearly-labelled synthetic fallback)
# ──────────────────────────────────────────────────────────────────────────────
def _synthetic_leaderboard() -> dict[str, Any]:
    """A deterministic, clearly-labelled fallback used ONLY when no real bake-off leaderboard exists yet. Its stats
    are synthetic placeholders (marked ``synthetic=true``), never presented as measured metrics."""
    # (path_id, name, search_method, role) — mirrors the bake-off path portfolio.
    paths = [
        ("P0", "deterministic_table_row", "exact_edge", "baseline"),
        ("P1", "lexical_search", "blocking_lexical", "candidate"),
        ("P2", "edge_typed_compose", "edge_type_constrained", "candidate"),
        ("P3", "hybrid_rrf", "hybrid_rrf", "candidate"),
        ("P4", "llm_assisted_peelback", "dense_ann", "candidate"),
    ]
    # a safe, defensible default routing when nothing has been measured yet.
    default_winners = {
        "string_transform": "P0", "data_pipeline": "P2", "algorithm": "P3",
        "extraction": "P4", "agentic": "P2",
    }
    order = ["P0", "P1", "P2", "P3", "P4"]

    def _stats(win: str) -> dict[str, Any]:
        out = {}
        for pid in order:
            is_win = pid == win
            out[pid] = {
                "path_id": pid, "within_budget": True,
                "contract_pass_rate": 1.0 if is_win else 0.5,
                "mean_composability": 1.0 if is_win else 0.5,
                "proven_route_pct": 0.0, "median_tokens": float(order.index(pid) * 40),
                "p50_latency_ms": float(1 + order.index(pid) * 10), "n_tasks": 0, **BOUNDARY,
            }
        return out

    classes = {
        cls: {
            "eligible_paths": list(order), "winner": win,
            "winner_rationale": f"[synthetic default] {win} pre-seeded for {cls} until a real bake-off runs.",
            "path_stats": _stats(win), "latency_budget_ms": 400.0, "token_budget": 400.0,
        }
        for cls, win in default_winners.items()
    }
    wc: dict[str, int] = {}
    for win in default_winners.values():
        wc[win] = wc.get(win, 0) + 1
    return {
        "record_type": "path_bakeoff_leaderboard", "pack_id": "path-bakeoff", "synthetic": True,
        "generated_utc": "synthetic", "ran_at": FIXED_NOW,
        "paths": [{"path_id": p, "name": n, "portfolio_search_method": m, "role": r, **BOUNDARY}
                  for p, n, m, r in paths],
        "classes": classes,
        "overall": {"winner_counts": wc, "note": "synthetic fallback — no bake-off leaderboard on disk."},
        **BOUNDARY,
    }


def load_leaderboard(path: Path | str | None = None) -> dict[str, Any]:
    """Load the bake-off leaderboard json if present, else return the synthetic fallback."""
    p = Path(path) if path is not None else DEFAULT_LEADERBOARD
    if p.exists():
        data = json.loads(p.read_text(encoding="utf-8"))
        data.setdefault("_source_path", str(p))
        data.setdefault("synthetic", False)
        return data
    fb = _synthetic_leaderboard()
    fb["_source_path"] = None
    return fb


def _leaderboard_sha256(leaderboard: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(leaderboard, sort_keys=True, default=str).encode()).hexdigest()


# ──────────────────────────────────────────────────────────────────────────────
# Routing table derivation — leaderboard -> {task_class -> ranked_path_ids (+ rationale)}
# ──────────────────────────────────────────────────────────────────────────────
def _path_meta(leaderboard: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {p["path_id"]: p for p in leaderboard.get("paths", [])}


def _baseline_path_id(leaderboard: dict[str, Any]) -> str:
    for p in leaderboard.get("paths", []):
        if p.get("role") == "baseline":
            return p["path_id"]
    # honest fallback: lowest-sorted path id (P0 by convention).
    ids = sorted(p["path_id"] for p in leaderboard.get("paths", []))
    return ids[0] if ids else "P0"


def _rank_key(ps: dict[str, Any]) -> tuple:
    """Deterministic descending merit: in-budget, contract-pass, composability, proven-route, cheaper, faster."""
    return (
        1 if ps.get("within_budget", True) else 0,
        float(ps.get("contract_pass_rate", 0.0)),
        float(ps.get("mean_composability", 0.0)),
        float(ps.get("proven_route_pct", 0.0)),
        -float(ps.get("median_tokens", 0.0)),
        -float(ps.get("p50_latency_ms", 0.0)),
    )


def _rank_paths_for_class(class_entry: dict[str, Any]) -> list[str]:
    """Rank a class's eligible paths by merit, but FORCE the leaderboard's declared winner to the front (the policy
    prefers the leaderboard's own verdict; the merit sort only orders the fallbacks)."""
    stats = class_entry.get("path_stats", {})
    winner = class_entry.get("winner")
    eligible = list(class_entry.get("eligible_paths", stats.keys()))
    # sort by merit desc, tie-break by path_id asc (stable + deterministic).
    ranked = sorted(eligible, key=lambda pid: (_rank_key(stats.get(pid, {})), tuple(-ord(c) for c in pid)),
                    reverse=True)
    if winner and winner in ranked:
        ranked = [winner] + [pid for pid in ranked if pid != winner]
    return ranked


def _global_fallback_order(leaderboard: dict[str, Any], exclude: str) -> list[str]:
    """Order remaining paths by how often they win across classes (then by id) — used for the unknown/default route."""
    wc = leaderboard.get("overall", {}).get("winner_counts", {})
    ids = [p["path_id"] for p in leaderboard.get("paths", []) if p["path_id"] != exclude]
    return sorted(ids, key=lambda pid: (-int(wc.get(pid, 0)), pid))


def derive_routing_table(leaderboard: dict[str, Any] | None = None) -> dict[str, dict[str, Any]]:
    """Derive ``{task_class -> {winner, ranked_path_ids, fallbacks, rationale, path_names}}`` including an
    ``unknown`` entry that routes to the safe deterministic baseline path."""
    lb = leaderboard if leaderboard is not None else load_leaderboard()
    meta = _path_meta(lb)
    classes = lb.get("classes", {})
    table: dict[str, dict[str, Any]] = {}

    def _names(ids: list[str]) -> list[str]:
        return [meta.get(pid, {}).get("name", pid) for pid in ids]

    for cls in sorted(classes):
        entry = classes[cls]
        ranked = _rank_paths_for_class(entry)
        winner = entry.get("winner") or (ranked[0] if ranked else _baseline_path_id(lb))
        method = meta.get(winner, {}).get("portfolio_search_method")
        method_status = _search_method_status(method)
        table[cls] = {
            "task_class": cls, "winner": winner, "ranked_path_ids": ranked,
            "fallbacks": [pid for pid in ranked if pid != winner],
            "winner_name": meta.get(winner, {}).get("name", winner),
            "winner_search_method": method, "winner_search_method_status": method_status,
            "ranked_path_names": _names(ranked),
            "rationale": entry.get("winner_rationale",
                                   f"leaderboard elected {winner} for {cls}"),
            "source": "synthetic" if lb.get("synthetic") else "bakeoff",
            **BOUNDARY,
        }

    # the safe default for anything we cannot classify -> deterministic baseline path.
    base = _baseline_path_id(lb)
    fb = _global_fallback_order(lb, exclude=base)
    table[UNKNOWN_CLASS] = {
        "task_class": UNKNOWN_CLASS, "winner": base,
        "ranked_path_ids": [base] + fb, "fallbacks": fb,
        "winner_name": meta.get(base, {}).get("name", base),
        "winner_search_method": meta.get(base, {}).get("portfolio_search_method"),
        "winner_search_method_status": _search_method_status(meta.get(base, {}).get("portfolio_search_method")),
        "ranked_path_names": [meta.get(pid, {}).get("name", pid) for pid in [base] + fb],
        "rationale": (f"unclassified task -> SAFE deterministic baseline {base} "
                      f"({meta.get(base, {}).get('name', base)}); portfolio fallbacks ordered by global win-frequency "
                      "so it is never a lock-in."),
        "source": "synthetic" if lb.get("synthetic") else "bakeoff",
        **BOUNDARY,
    }
    return table


def _search_method_status(method: str | None) -> str | None:
    """Cross-check a path's search method against the retrieval-backend portfolio (real reuse, not a reinvented map)."""
    if method is None or not _RETRIEVAL_PORTFOLIO_AVAILABLE or _backends_of is None:
        return None
    try:
        for row in _backends_of("search_method"):
            if row.get("method_id") == method:
                return row.get("status")
    except Exception:  # noqa: BLE001
        return None
    return None


# ──────────────────────────────────────────────────────────────────────────────
# The DECISION api + the policy ledger
# ──────────────────────────────────────────────────────────────────────────────
def _features_hash(task_features: dict[str, Any]) -> str:
    return hashlib.sha256(json.dumps(task_features, sort_keys=True, default=str).encode()).hexdigest()[:16]


def _record_decision(decision: dict[str, Any], *, ledger_path: Path | str | None) -> None:
    if ledger_path is None:
        return
    p = Path(ledger_path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(decision, sort_keys=True, ensure_ascii=False) + "\n")


def select_path(task_features: dict[str, Any], *, leaderboard: dict[str, Any] | None = None,
                routing_table: dict[str, dict[str, Any]] | None = None,
                ledger_path: Path | str | None = DEFAULT_LEDGER, record: bool = True,
                now: str | None = None) -> dict[str, Any]:
    """Classify a task and return the leaderboard winner + ordered fallbacks (always a PORTFOLIO, never a lock-in).

    Returns ``{path_id, rationale, fallbacks, task_class, ...}`` and records the decision to the policy ledger for
    later refinement. Deterministic given ``task_features`` + ``now``; pass ``record=False`` / ``ledger_path=None``
    for a pure (no-side-effect) call."""
    lb = leaderboard if leaderboard is not None else load_leaderboard()
    table = routing_table if routing_table is not None else derive_routing_table(lb)
    cls = classify_task(task_features)
    entry = table.get(cls) or table[UNKNOWN_CLASS]
    decision = {
        "record_type": "path_selection_decision",
        "task_class": cls if cls in table else UNKNOWN_CLASS,
        "classified_as": cls,
        "path_id": entry["winner"],
        "winner_name": entry.get("winner_name"),
        "fallbacks": list(entry["fallbacks"]),
        "ranked_path_ids": list(entry["ranked_path_ids"]),
        "rationale": entry["rationale"],
        "winner_search_method": entry.get("winner_search_method"),
        "winner_search_method_status": entry.get("winner_search_method_status"),
        "task_features_hash": _features_hash(task_features),
        "leaderboard_sha256": _leaderboard_sha256(lb),
        "leaderboard_source": "synthetic" if lb.get("synthetic") else "bakeoff",
        "decided_utc": now or FIXED_NOW,
        **BOUNDARY,
    }
    if record:
        _record_decision(decision, ledger_path=ledger_path)
    return decision


def explain_policy(leaderboard: dict[str, Any] | None = None) -> str:
    """Render the full routing table as markdown — the human-readable statement of the current policy."""
    lb = leaderboard if leaderboard is not None else load_leaderboard()
    table = derive_routing_table(lb)
    src = "SYNTHETIC fallback (no bake-off on disk)" if lb.get("synthetic") else lb.get("_source_path", "bake-off leaderboard")
    lines = [
        "# Path Selection Policy — routing table",
        "",
        f"Derived from: `{src}`  ·  generated for `{lb.get('generated_utc', '?')}`",
        "",
        "Each task is classified by deterministic features into a task-class, then routed to the leaderboard "
        "winner **with ordered fallbacks** (a portfolio decision, never a lock-in).",
        "",
        "| Task class | Winner | Winner strategy | Search method (status) | Ordered fallbacks |",
        "| --- | --- | --- | --- | --- |",
    ]
    ordered = sorted(k for k in table if k != UNKNOWN_CLASS) + [UNKNOWN_CLASS]
    for cls in ordered:
        e = table[cls]
        status = e.get("winner_search_method_status") or "?"
        method = e.get("winner_search_method") or "—"
        fb = ", ".join(f"`{x}`" for x in e["fallbacks"]) or "—"
        lines.append(f"| `{cls}` | `{e['winner']}` | {e.get('winner_name', '')} | `{method}` ({status}) | {fb} |")
    lines += ["", "## Rationale per class", ""]
    for cls in ordered:
        lines.append(f"- **`{cls}` → `{table[cls]['winner']}`** — {table[cls]['rationale']}")
    lines += ["", "_Routing table is candidate analysis (candidate=true / serves_truth=false); it updates "
              "automatically whenever the bake-off re-runs._"]
    return "\n".join(lines) + "\n"


# ──────────────────────────────────────────────────────────────────────────────
# Pack writer (routing table + policy ledger + manifest) — --run
# ──────────────────────────────────────────────────────────────────────────────
def _routing_rows(table: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    return [table[cls] for cls in (sorted(k for k in table if k != UNKNOWN_CLASS) + [UNKNOWN_CLASS])]


def build_manifest(table: dict[str, dict[str, Any]], leaderboard: dict[str, Any], *, date: str) -> dict[str, Any]:
    rows = _routing_rows(table)
    canonical = "\n".join(json.dumps(r, sort_keys=True, ensure_ascii=False) for r in rows)
    row_counts = {
        "routing_table_rows": len(rows),
        "task_classes_routed": len([k for k in table if k != UNKNOWN_CLASS]),
        "paths_in_portfolio": len(leaderboard.get("paths", [])),
    }
    return {
        "record_type": "path_selection_policy_manifest",
        "pack_id": "path-selection-policy", "generator": "scripts/path_selection_policy.py",
        "generated_utc": date, "row_counts": row_counts, "total_rows": sum(row_counts.values()),
        "leaderboard_source": "synthetic" if leaderboard.get("synthetic") else leaderboard.get("_source_path"),
        "leaderboard_is_synthetic": bool(leaderboard.get("synthetic")),
        "leaderboard_sha256": _leaderboard_sha256(leaderboard),
        "winners_by_class": {cls: table[cls]["winner"] for cls in table},
        "safe_default_path": table[UNKNOWN_CLASS]["winner"],
        "reuse": reuse_availability(),
        "content_sha256": hashlib.sha256(canonical.encode("utf-8")).hexdigest(),
        **BOUNDARY,
    }


def write_pack(*, date: str, leaderboard_path: Path | str | None = None,
               ledger_path: Path | str | None = DEFAULT_LEDGER, now: str = FIXED_NOW) -> dict[str, Any]:
    lb = load_leaderboard(leaderboard_path)
    table = derive_routing_table(lb)
    POLICY_DIR.mkdir(parents=True, exist_ok=True)
    rows = _routing_rows(table)
    (POLICY_DIR / "routing_table.jsonl").write_text(
        "".join(json.dumps(r, ensure_ascii=False, sort_keys=True) + "\n" for r in rows), encoding="utf-8")
    (POLICY_DIR / "routing_table.md").write_text(explain_policy(lb), encoding="utf-8")
    manifest = build_manifest(table, lb, date=date)
    (POLICY_DIR / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    # append one demo decision so the ledger exists + is exercised end-to-end.
    select_path({"domain": "data_pipeline ingest", "is_multi_step": True, "has_input_type": True,
                 "has_output_type": True}, leaderboard=lb, routing_table=table,
                ledger_path=ledger_path, record=True, now=now)
    return manifest


# ──────────────────────────────────────────────────────────────────────────────
# Self-test (pure/offline, deterministic)
# ──────────────────────────────────────────────────────────────────────────────
def self_test() -> int:
    import tempfile

    checks: list[tuple[str, bool]] = []
    lb = load_leaderboard()  # real file present in-repo; falls back to synthetic elsewhere.
    table = derive_routing_table(lb)

    # 1) every real task-class routes to a winner with a NON-EMPTY fallback portfolio.
    routed = [c for c in table if c != UNKNOWN_CLASS]
    checks.append(("all 5 task-classes present in routing table", set(routed) == set(MAIN_CLASSES)))
    for cls in routed:
        e = table[cls]
        ok = bool(e["winner"]) and len(e["fallbacks"]) >= 1 and e["winner"] not in e["fallbacks"]
        checks.append((f"class {cls}: winner + non-empty fallbacks (portfolio)", ok))

    # 2) select_path PREFERS the leaderboard winner for each class (classify -> right class -> that winner).
    class_features = {
        "string_transform": {"domain": "string transform", "has_input_type": True, "has_output_type": True},
        "data_pipeline": {"domain": "data pipeline ingest", "is_multi_step": True, "has_input_type": True},
        "algorithm": {"domain": "algorithm solve plan", "is_multi_step": True},
        "extraction": {"domain": "document extraction parse", "is_multi_step": True},
        "agentic": {"domain": "agent tool orchestrate", "is_multi_step": True},
    }
    with tempfile.TemporaryDirectory() as td:
        ledger = Path(td) / "ledger.jsonl"
        for cls, feats in class_features.items():
            d = select_path(feats, leaderboard=lb, routing_table=table, ledger_path=ledger, now=FIXED_NOW)
            lb_winner = lb["classes"][cls]["winner"]
            checks.append((f"select_path prefers leaderboard winner for {cls} "
                           f"(got {d['path_id']}, leaderboard {lb_winner})",
                           d["task_class"] == cls and d["path_id"] == lb_winner and len(d["fallbacks"]) >= 1))
        # 3) an UNKNOWN class falls back to the safe deterministic baseline path.
        base = _baseline_path_id(lb)
        unk = select_path({"domain": "quantum_underwater_basketweaving_zzz"}, leaderboard=lb, routing_table=table,
                          ledger_path=ledger, now=FIXED_NOW)
        checks.append(("unknown task classifies as unknown", unk["classified_as"] == UNKNOWN_CLASS))
        checks.append((f"unknown falls back to safe baseline path {base} + non-empty fallbacks",
                       unk["path_id"] == base and len(unk["fallbacks"]) >= 1))
        # 4) the ledger actually recorded every decision (durable + refinable).
        recorded = ledger.read_text(encoding="utf-8").splitlines()
        checks.append(("policy ledger recorded every decision", len(recorded) == len(class_features) + 1))
        first = json.loads(recorded[0])
        checks.append(("ledger rows are candidate=true / serves_truth=false",
                       first["candidate"] is True and first["serves_truth"] is False))

    # 5) determinism — same features + same now -> identical decision (no wall-clock/RNG).
    a = select_path({"domain": "extraction"}, leaderboard=lb, routing_table=table, record=False, now=FIXED_NOW)
    b = select_path({"domain": "extraction"}, leaderboard=lb, routing_table=table, record=False, now=FIXED_NOW)
    checks.append(("select_path is deterministic", a == b))

    # 6) synthetic fallback works when no leaderboard exists (offline resilience).
    syn = load_leaderboard(Path(tempfile.gettempdir()) / "definitely_absent_bakeoff_zzz.json")
    syn_table = derive_routing_table(syn)
    syn_dec = select_path({"domain": "algorithm"}, leaderboard=syn, routing_table=syn_table, record=False)
    checks.append(("synthetic fallback leaderboard yields a valid decision",
                   syn.get("synthetic") is True and bool(syn_dec["path_id"]) and len(syn_dec["fallbacks"]) >= 1))

    # 7) explain_policy renders markdown with every class + the unknown default row.
    md = explain_policy(lb)
    checks.append(("explain_policy is markdown covering all classes + unknown default",
                   md.startswith("# Path Selection Policy") and all(f"`{c}`" in md for c in MAIN_CLASSES)
                   and f"`{UNKNOWN_CLASS}`" in md))

    # 8) manifest counts are computed from the table (never fabricated).
    manifest = build_manifest(table, lb, date="2026-07-03")
    checks.append(("manifest row_counts are computed + consistent",
                   manifest["row_counts"]["routing_table_rows"] == len(_routing_rows(table))
                   and manifest["total_rows"] == sum(manifest["row_counts"].values())
                   and len(manifest["content_sha256"]) == 64))

    # 9) reuse is real: retrieval portfolio helpers imported + used (dim_compatible sanity when available).
    if _RETRIEVAL_PORTFOLIO_AVAILABLE and _dim_compatible is not None:
        checks.append(("reused dim_compatible guard behaves", _dim_compatible(384, 384) and not _dim_compatible(64, 768)))

    failed = [n for n, ok in checks if not ok]
    if failed:
        print("FAIL - path_selection_policy:\n  " + "\n  ".join(failed))
        return 1
    print(f"PASS - path_selection_policy: routing table over {len(routed)} task-classes (+ safe unknown default); "
          "select_path returns the leaderboard winner + ordered fallbacks (portfolio, never lock-in), records every "
          "decision to the policy ledger, falls back to the deterministic baseline on unknown classes, works offline "
          "with a synthetic leaderboard, and re-derives automatically when the bake-off re-runs.")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--run", action="store_true", help="write the routing-table pack + append a demo ledger decision")
    parser.add_argument("--explain", action="store_true", help="print the routing table as markdown")
    parser.add_argument("--leaderboard", default=None, help="path to a bake-off leaderboard json (default: latest in-repo)")
    parser.add_argument("--date", default=None)
    args = parser.parse_args(argv)

    if args.explain and not args.run:
        print(explain_policy(load_leaderboard(args.leaderboard)))
        return 0
    if args.self_test and not args.run:
        return self_test()
    if args.run:
        date = args.date or dt.datetime.now(dt.timezone.utc).date().isoformat()
        now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        manifest = write_pack(date=date, leaderboard_path=args.leaderboard, now=now)
        print(json.dumps({k: v for k, v in manifest.items() if k != "content_sha256"}, indent=2, sort_keys=True))
        return self_test()
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
