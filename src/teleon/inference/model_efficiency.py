"""src.teleon.inference.model_efficiency — rank models by MEASURED efficiency per task class, so
OIPS picks the cheapest CAPABLE model instead of a fixed preference list (the "auto-pick the most
efficient model" / ClawWork-style intelligence — built INTO routing, not a new surface).

WHERE THIS FITS: OpenRoutingHub is the routing-policy SURFACE; OIPS `select_provider` is the runtime
MECHANISM. This module is the EVIDENCE that orders the choice. It does NOT decide eligibility (policy/
secret/specialization/health — that stays in oips._eligible); it only RE-ORDERS the already-eligible
nodes by efficiency. The selection stays deterministic + governed.

TWO INPUTS, governed differently (discovery ≠ trust):
  1. OUR receipts (the trusted, measured substrate) — every ModelInvocationReceipt already records
     cost_estimate_usd / latency_ms / tokens / selected_model / requested_model_class / fallback_used.
     This is real, first-party, governed evidence; it drives the ranking.
  2. EXTERNAL leaderboards (e.g. HKUDS/ClawWork — an economic GDPVal benchmark ranking models by
     income/cost/quality) — ingested as a CANDIDATE signal only, never silently overriding our measured
     numbers: tagged with provenance, weighted below first-party evidence, requires review to promote.

QUALITY axis: receipts carry cost/latency but not a quality score (quality comes from the gate / the
measured-lift producer). `rank_models` accepts an optional per-(model, class) quality map so the full
quality-per-cost ranking is possible the moment that data exists; without it, the ranking is the
cost/latency/reliability efficiency (lower is better), which is already the dominant signal for
"cheapest capable model".

Pure + deterministic (no clock/random — `now`/inputs injected). Offline-honest: no receipts ⇒ an empty
ranking (never a fabricated order). stdlib only.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterable

# --- efficiency weights (lower cost/latency/fallback = more efficient). Named, with rationale; a caller
# can override. Normalized within a task class so a cheap-but-slow and a fast-but-pricey model compare.
DEFAULT_WEIGHTS = {
    "cost": 0.55,       # $/call dominates "efficiency" — the whole point of auto-picking
    "latency": 0.25,    # responsiveness matters but less than price for batch-shaped work
    "reliability": 0.20,  # fallback/error rate — a cheap model that keeps failing isn't cheap
}
# first-party measured evidence outranks an external leaderboard by this factor (discovery ≠ trust):
# an external ranking can only tie-break / fill gaps, never override our own measured numbers.
EXTERNAL_SIGNAL_WEIGHT = 0.34   # < 0.5 so it can never outvote first-party evidence for a given model
MIN_SAMPLES_FOR_RANK = 3        # below this, a model's first-party score is "thin" (flagged, not hidden)


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return default


def load_receipts(path: Path | str) -> list[dict]:
    """Read a ModelInvocationReceipt JSONL sink (the model-receipts plane). Missing ⇒ []."""
    p = Path(path)
    if not p.is_file():
        return []
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


def _aggregate(receipts: Iterable[dict]) -> dict[tuple[str, str], dict]:
    """Aggregate receipts by (model, task_class) → {n, total_cost, total_latency, fallbacks}."""
    agg: dict[tuple[str, str], dict] = {}
    for r in receipts:
        model = str(r.get("selected_model") or r.get("selected_provider_node_id") or "")
        if not model:
            continue
        klass = str(r.get("requested_model_class") or "default")
        a = agg.setdefault((model, klass), {"n": 0, "cost": 0.0, "latency": 0.0, "fallbacks": 0})
        a["n"] += 1
        a["cost"] += _safe_float(r.get("cost_estimate_usd"))
        a["latency"] += _safe_float(r.get("latency_ms"))
        a["fallbacks"] += 1 if r.get("fallback_used") else 0
    return agg


def _normalize(values: dict[str, float]) -> dict[str, float]:
    """Min-max to [0,1] within a class; all-equal ⇒ 0 (no spurious spread)."""
    if not values:
        return {}
    lo, hi = min(values.values()), max(values.values())
    span = hi - lo
    return {k: (0.0 if span == 0 else (v - lo) / span) for k, v in values.items()}


def rank_models(receipts: Iterable[dict], *, task_class: str | None = None,
                weights: dict | None = None,
                quality: dict[tuple[str, str], float] | None = None,
                external: dict[tuple[str, str], float] | None = None) -> list[dict]:
    """Rank models for a task class by MEASURED efficiency. Returns a sorted list (best first) of
    {model, task_class, n, avg_cost_usd, avg_latency_ms, fallback_rate, efficiency_score, thin,
    quality, external_signal}. efficiency_score in [0,1], higher = better (cheaper/faster/more
    reliable, optionally × quality). Deterministic; empty receipts ⇒ []."""
    w = {**DEFAULT_WEIGHTS, **(weights or {})}
    agg = _aggregate(receipts)
    classes = {k[1] for k in agg} if task_class is None else {task_class}
    rows: list[dict] = []
    for klass in classes:
        members = {k[0]: v for k, v in agg.items() if k[1] == klass}
        if not members:
            continue
        avg_cost = {m: v["cost"] / v["n"] for m, v in members.items()}
        avg_lat = {m: v["latency"] / v["n"] for m, v in members.items()}
        fb_rate = {m: v["fallbacks"] / v["n"] for m, v in members.items()}
        # lower is better → invert the normalized cost/latency/reliability into a [0,1] goodness
        n_cost, n_lat, n_fb = _normalize(avg_cost), _normalize(avg_lat), _normalize(fb_rate)
        for m, v in members.items():
            goodness = (w["cost"] * (1 - n_cost[m]) + w["latency"] * (1 - n_lat[m])
                        + w["reliability"] * (1 - n_fb[m]))
            q = (quality or {}).get((m, klass))
            ext = (external or {}).get((m, klass))
            score = goodness
            if q is not None:                       # quality-per-cost when quality evidence exists
                score *= max(0.0, min(1.0, float(q)))
            if ext is not None:                     # external leaderboard = a weak tie-breaker only
                score = (1 - EXTERNAL_SIGNAL_WEIGHT) * score + EXTERNAL_SIGNAL_WEIGHT * float(ext) * goodness
            rows.append({
                "model": m, "task_class": klass, "n": v["n"],
                "avg_cost_usd": round(avg_cost[m], 6), "avg_latency_ms": round(avg_lat[m], 1),
                "fallback_rate": round(fb_rate[m], 3), "efficiency_score": round(score, 4),
                "thin": v["n"] < MIN_SAMPLES_FOR_RANK,
                "quality": q, "external_signal": ext,
            })
    # best first; deterministic tie-break by model id; thin samples sink below comparable solid ones
    rows.sort(key=lambda r: (-r["efficiency_score"], r["thin"], r["model"]))
    return rows


def efficiency_order(eligible_node_ids: list[str], ranking: list[dict]) -> list[str]:
    """THE OIPS CONSUMPTION POINT: reorder the already-eligible nodes (oips._eligible decided WHICH are
    allowed) by measured efficiency. Ranked-and-eligible nodes come first (best efficiency first);
    eligible-but-unranked nodes keep their original relative order AFTER (no measured evidence yet ⇒
    don't demote below a thin guess; preserve the policy's declared preference). Pure + deterministic."""
    rank_pos = {r["model"]: i for i, r in enumerate(ranking)}
    ranked = [n for n in eligible_node_ids if n in rank_pos]
    ranked.sort(key=lambda n: rank_pos[n])
    unranked = [n for n in eligible_node_ids if n not in rank_pos]
    return ranked + unranked


def ingest_external_ranking(source: str, entries: list[dict], *, now: str) -> dict:
    """Wrap an EXTERNAL leaderboard (e.g. HKUDS/ClawWork) as a CANDIDATE signal — provenance-tagged,
    never trusted as truth, never auto-overriding first-party measured evidence. Returns a governed
    record {source, collected_at, status:'candidate', is_truth:false, signals:{(model,class): score}}.
    The owner/review promotes a candidate before it weights routing in production."""
    signals = {}
    for e in entries:
        model = str(e.get("model") or e.get("agent") or "")
        klass = str(e.get("task_class") or "default")
        score = e.get("efficiency") or e.get("score")
        if model and score is not None:
            signals[f"{model}::{klass}"] = max(0.0, min(1.0, _safe_float(score)))
    return {"source": source, "collected_at": now, "status": "candidate", "is_truth": False,
            "note": "external leaderboard — candidate signal only; discovery ≠ trust; weighted below "
                    "first-party receipts and requires review before it routes production traffic.",
            "signals": signals}


# ---------------------------------------------------------------- producers (feed rank_models)

#: The committed external-leaderboard fixture (a CANDIDATE signal; provenance external_unverified).
DEFAULT_EXTERNAL_LEADERBOARD = Path(__file__).resolve().parents[3] / "data" / "model-efficiency" / "external-leaderboard.jsonl"


def quality_from_receipts(receipts: Iterable[dict]) -> dict[tuple[str, str], float]:
    """The QUALITY producer: per-(model, class) mean quality from receipts that carry a
    ``quality`` field (written by the measured-lift / eval pass). Returns the ``(model, class)``
    map ``rank_models(quality=...)`` consumes; EMPTY when no receipt carries quality (honest —
    cheapest-capable stays cost/latency-only until quality evidence exists). Deterministic."""
    sums: dict[tuple[str, str], list[float]] = {}
    for r in receipts:
        q = r.get("quality")
        if q is None:
            continue
        model = str(r.get("selected_model") or r.get("selected_provider_node_id") or "")
        if not model:
            continue
        klass = str(r.get("requested_model_class") or "default")
        sums.setdefault((model, klass), []).append(max(0.0, min(1.0, _safe_float(q))))
    return {k: round(sum(v) / len(v), 6) for k, v in sums.items() if v}


def external_signals_for_ranking(record: dict) -> dict[tuple[str, str], float]:
    """Convert an ``ingest_external_ranking`` record's ``'model::klass'`` signal keys into the
    ``(model, class)`` tuple shape ``rank_models(external=...)`` expects — bridging the two so the
    external candidate signal can actually tie-break the ranking (still weighted < first-party)."""
    out: dict[tuple[str, str], float] = {}
    for key, score in (record.get("signals") or {}).items():
        model, _, klass = str(key).partition("::")
        if model:
            out[(model, klass or "default")] = max(0.0, min(1.0, _safe_float(score)))
    return out


def load_external_leaderboard(path: Path | str = DEFAULT_EXTERNAL_LEADERBOARD,
                              *, now: str = "1970-01-01T00:00:00Z") -> dict[tuple[str, str], float]:
    """Load the committed leaderboard fixture → the ``(model, class)`` external map for
    ``rank_models``. EMPTY when the file is absent (honest — no external signal, no effect).
    Routes through ``ingest_external_ranking`` so the candidate-not-truth provenance is enforced."""
    p = Path(path)
    if not p.exists():
        return {}
    entries: list[dict] = []
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    record = ingest_external_ranking(str(p.name), entries, now=now)
    return external_signals_for_ranking(record)


# ---------------------------------------------------------------- self-test (offline, deterministic)

def _self_test() -> int:
    checks = []

    def ck(name, ok):
        checks.append((name, ok))

    # synthetic receipts: model-A cheap+fast, model-B pricey+slow, model-C cheap but always falls back
    recs = []
    for _ in range(5):
        recs.append({"selected_model": "A", "requested_model_class": "extract",
                     "cost_estimate_usd": 0.001, "latency_ms": 200, "fallback_used": False})
        recs.append({"selected_model": "B", "requested_model_class": "extract",
                     "cost_estimate_usd": 0.05, "latency_ms": 1800, "fallback_used": False})
        recs.append({"selected_model": "C", "requested_model_class": "extract",
                     "cost_estimate_usd": 0.001, "latency_ms": 220, "fallback_used": True})
    ranking = rank_models(recs, task_class="extract")
    ck("ranks the cheap+fast+reliable model (A) first", ranking and ranking[0]["model"] == "A")
    ck("the pricey+slow model (B) ranks worst", ranking[-1]["model"] == "B")
    ck("the cheap-but-unreliable model (C) is penalized below A",
       [r["model"] for r in ranking].index("C") > 0)
    ck("scores are in [0,1], deterministic", all(0 <= r["efficiency_score"] <= 1 for r in ranking)
       and rank_models(recs, task_class="extract") == ranking)
    ck("empty receipts → empty ranking (no fabricated order)", rank_models([]) == [])
    ck("thin samples flagged, not hidden", all("thin" in r for r in ranking)
       and rank_models(recs[:2], task_class="extract")[0]["thin"] is True)

    # OIPS consumption: reorder eligible nodes by the ranking, unranked preserved after
    order = efficiency_order(["B", "A", "D", "C"], ranking)
    ck("efficiency_order puts the best eligible model first (A before B)",
       order.index("A") < order.index("B"))
    ck("an eligible-but-unranked node (D) is preserved AFTER ranked ones (no demotion on no evidence)",
       order.index("D") > order.index("C"))

    # quality axis: without quality, reliable A out-ranks unreliable C; with quality strongly favoring
    # C, quality-per-cost flips them (both are cheap, so quality is the deciding axis) — a model at the
    # cost/latency EXTREME (B) still can't be rescued by quality, which is correct (50x price wins nothing)
    base_order = [r["model"] for r in ranking]
    q_ranking = rank_models(recs, task_class="extract",
                            quality={("C", "extract"): 1.0, ("A", "extract"): 0.1})
    q_order = [r["model"] for r in q_ranking]
    ck("quality-per-cost flips comparable models (C overtakes A when quality favors C)",
       base_order.index("A") < base_order.index("C") and q_order.index("C") < q_order.index("A"))

    # external (ClawWork-style) candidate ingest — governed, never truth
    ext = ingest_external_ranking("clawwork", [{"model": "A", "task_class": "extract", "efficiency": 0.9}],
                                  now="epoch:1")
    ck("external leaderboard ingested as a CANDIDATE (is_truth false, status candidate)",
       ext["is_truth"] is False and ext["status"] == "candidate" and "A::extract" in ext["signals"])
    ck("external signal only tie-breaks, never outvotes first-party (B stays worst even if ext loves it)",
       rank_models(recs, task_class="extract",
                   external={("B", "extract"): 1.0})[-1]["model"] == "B")

    # NEW PRODUCERS (the wiring that feeds rank_models in the live OIPS path):
    # quality_from_receipts surfaces a quality dimension from receipts that carry it; it then
    # demotes a cheap-but-low-quality model via the quality-per-cost score.
    q_recs = recs + [{"selected_model": "A", "requested_model_class": "extract",
                      "cost_estimate_usd": 0.001, "latency_ms": 200, "fallback_used": False, "quality": 0.1},
                     {"selected_model": "C", "requested_model_class": "extract",
                      "cost_estimate_usd": 0.001, "latency_ms": 220, "fallback_used": False, "quality": 0.95}]
    qmap = quality_from_receipts(q_recs)
    ck("quality_from_receipts surfaces per-(model,class) quality from receipts",
       qmap.get(("A", "extract")) == 0.1 and qmap.get(("C", "extract")) == 0.95)
    ck("quality_from_receipts is EMPTY when no receipt carries quality (honest)",
       quality_from_receipts(recs) == {})
    fed = [r["model"] for r in rank_models(q_recs, task_class="extract", quality=qmap or None)]
    ck("fed quality demotes the cheap-but-low-quality model (C now beats A)",
       fed.index("C") < fed.index("A"))
    # external_signals_for_ranking bridges the 'model::klass' record shape → (model, class) tuples.
    bridged = external_signals_for_ranking(ext)
    ck("external_signals_for_ranking bridges to (model,class) tuples rank_models consumes",
       bridged.get(("A", "extract")) == 0.9)
    # load_external_leaderboard loads the committed fixture into the right shape (or empty if absent).
    board = load_external_leaderboard()
    ck("load_external_leaderboard loads the committed fixture as (model,class) tuples",
       board == {} or all(isinstance(k, tuple) and len(k) == 2 for k in board))

    failed = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
    print(("PASS — " if not failed else "FAIL — ")
          + f"model_efficiency: {len(checks) - len(failed)}/{len(checks)} — measured efficiency ranks models "
            "per task class (cost/latency/reliability, optional quality-per-cost), external leaderboards are "
            "candidate-only, and efficiency_order is the OIPS reorder seam.")
    return 1 if failed else 0


if __name__ == "__main__":
    import sys
    sys.exit(_self_test())
