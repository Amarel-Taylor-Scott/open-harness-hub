#!/usr/bin/env python3
"""adaptive_vectorization — the WATERFALL: not every card gets vectors for everything; richer vectors are created
ONLY when the data shows they help.

Owner (2026-07-10): "a waterfall / hierarchy where not all cards/primitives get vectors for everything — we create
additional vectors only when helpful." This is the demand-driven vectorization policy that makes "build out every
model/facet" affordable: EVERY card gets a cheap L0 vector (so it's findable at all); a card is PROMOTED to richer
levels (more registers → more facets → a strong-model vector → multi-model + ColBERT) ONLY when the REAL-WORLD usage
ledger justifies the spend — it's frequently retrieved (needs discrimination), or frequently selected/implemented
(high value, find it faster), or ambiguous/contended (needs more signal to disambiguate). Unused cards stay L0; a
promoted card can be DEMOTED (lossless — its vectors recompute from the committed generators). Direction comes from
the design; PRIORITY comes from production traffic (`primitive_usage_ledger`), not lab guessing.

This dovetails with the serverless cold tier: L0 lives cold in object storage (cheap, always); promotions add vectors
lazily; the hot RAM set = the top-promoted cards. Cost tracks USAGE, not corpus size.

    PYTHONPATH=. python3 scripts/adaptive_vectorization.py --self-test
    PYTHONPATH=. python3 scripts/adaptive_vectorization.py --levels     # the richness ladder + vector budgets
    PYTHONPATH=. python3 scripts/adaptive_vectorization.py --plan       # promotion plan from the real usage ledger
    PYTHONPATH=. python3 scripts/adaptive_vectorization.py --apply --confirm   # persist earned level changes
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Optional

_HERE = Path(__file__).resolve()
_REPO = _HERE.parent.parent
for _p in (str(_REPO), str(_REPO / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

#: The RICHNESS LADDER (the waterfall). Each level ADDS surfaces/models; `vectors` is the approx per-card vector count
#: at that level (cumulative). L0 is universal + cheap; higher levels are earned. Tunable — add a level = one row.
LEVELS: dict[int, dict[str, Any]] = {
    0: {"name": "minimal", "adds": "1 cheap card vector (model2vec)", "surfaces": ["card"],
        "models": ["model2vec_potion_8m"], "vectors": 1},
    1: {"name": "registers", "adds": "+3 language registers", "surfaces": ["card", "plain", "technical", "semantic"],
        "models": ["model2vec_potion_8m"], "vectors": 4},
    2: {"name": "facets", "adds": "+~90 facet descriptions", "surfaces": ["all_facets"],
        "models": ["model2vec_potion_8m"], "vectors": 90},
    3: {"name": "strong", "adds": "+strong-model card vector (BGE/Gemma) + code surface (jina-code)",
        "surfaces": ["all_facets", "code"], "models": ["model2vec_potion_8m", "fastembed_bge_large", "fastembed_jina_code"],
        "vectors": 95},
    4: {"name": "rich", "adds": "+multi-model facets + ColBERT late-interaction + sparse (SPLADE)",
        "surfaces": ["all_facets", "code", "late_interaction", "sparse"],
        "models": ["model2vec_potion_8m", "fastembed_bge_large", "ollama_embeddinggemma", "fastembed_jina_code",
                   "colbert-ir/colbertv2.0", "Splade_PP"], "vectors": 300},
}
MAX_LEVEL = max(LEVELS)
#: default corpus size for plan cost framing — the current searchable-corpus figure; callers pass the live count.
DEFAULT_CORPUS_SIZE = 539_890

_STATE_DIR = _REPO / "data" / "dev-intel" / "adaptive_vectorization"
_LEVEL_STATE = _STATE_DIR / "level_state.json"           # current earned level per primitive (derived, recomputable)
_LEVEL_HISTORY = _STATE_DIR / "level_history.jsonl"      # append-only lossless record of every promotion/demotion
_BUILD_WORKLIST = _STATE_DIR / "vector_build_worklist.jsonl"  # per-apply derived queue for the embedding builders


#: PROMOTION POLICY — score thresholds per level (tunable). The score is computed from real usage signals; a card
#: rises to the highest level whose threshold it clears. NEVER a magic literal in logic elsewhere — one source here.
_PROMOTE_THRESHOLD: dict[int, float] = {0: 0.0, 1: 1.0, 2: 5.0, 3: 20.0, 4: 100.0}
#: signal weights — selection/implementation is worth much more than a bare retrieval appearance.
_W_RETRIEVED = 1.0
_W_SELECTED = 3.0   # downloaded
_W_SUCCESS = 8.0    # successfully implemented (the strongest signal)
_W_AMBIGUITY = 2.0  # appeared in many shortlists without winning -> needs more discrimination


def usefulness_score(signals: dict[str, float]) -> float:
    """Combine real-world usage signals into a promotion score (higher -> earns richer vectors)."""
    return (_W_RETRIEVED * signals.get("retrieved", 0)
            + _W_SELECTED * signals.get("selected", 0)
            + _W_SUCCESS * signals.get("success", 0)
            + _W_AMBIGUITY * signals.get("ambiguity", 0))


def target_level(score: float) -> int:
    """The highest level whose threshold the score clears (the waterfall step this card has earned)."""
    lvl = 0
    for level in sorted(LEVELS):
        if score >= _PROMOTE_THRESHOLD[level]:
            lvl = level
    return lvl


def signals_from_ledger(ledger_path: Optional[Path] = None) -> dict[str, dict[str, float]]:
    """Per-primitive usage signals from the usage ledger: retrieved / selected / success / ambiguity."""
    from collections import defaultdict
    try:
        from scripts import primitive_usage_ledger as _ul  # noqa: PLC0415
        events = _ul.load_events(ledger_path)
    except Exception:  # noqa: BLE001
        events = []
    sig: dict[str, dict[str, float]] = defaultdict(lambda: {"retrieved": 0, "selected": 0, "success": 0, "ambiguity": 0})
    for e in events:
        et = e.get("event_type")
        for pid in e.get("primitive_ids", []):
            if et == "searched":
                sig[pid]["retrieved"] += 1
            elif et == "downloaded":
                sig[pid]["selected"] += 1
            elif et == "implemented" and e.get("outcome") == "success":
                sig[pid]["success"] += 1
    # ambiguity: retrieved a lot but rarely selected -> hard to disambiguate -> earns more vectors
    for pid, s in sig.items():
        if s["retrieved"] >= 3 and s["selected"] == 0:
            s["ambiguity"] = s["retrieved"]
    return dict(sig)


def waterfall_plan(current_levels: dict[str, int], signals: dict[str, dict[str, float]], *,
                   n_corpus: int, include_full: bool = False) -> dict[str, Any]:
    """Which cards to PROMOTE (or demote) and the vector/cost delta vs materializing everything at max level.

    ``include_full=True`` additionally returns the complete promotion/demotion lists (apply needs them); the
    default receipt shape is unchanged (bounded samples only).
    """
    promotions, demotions = [], []
    added_vectors = 0
    for pid, sig in signals.items():
        want = target_level(usefulness_score(sig))
        have = current_levels.get(pid, 0)
        if want > have:
            promotions.append({"primitive_id": pid, "from": have, "to": want,
                               "add_vectors": LEVELS[want]["vectors"] - LEVELS[have]["vectors"]})
            added_vectors += LEVELS[want]["vectors"] - LEVELS[have]["vectors"]
        elif want < have:
            demotions.append({"primitive_id": pid, "from": have, "to": want})
    # cost framing: naive = everyone at MAX level; adaptive = L0 for all + promotions for the active few
    naive_vectors = n_corpus * LEVELS[MAX_LEVEL]["vectors"]
    adaptive_vectors = n_corpus * LEVELS[0]["vectors"] + added_vectors
    plan = {"n_corpus": n_corpus, "promotions": len(promotions), "demotions": len(demotions),
            "added_vectors": added_vectors, "sample_promotions": promotions[:10],
            "naive_vectors_all_max": naive_vectors, "adaptive_vectors": adaptive_vectors,
            "storage_reduction_vs_naive": round(1 - adaptive_vectors / naive_vectors, 4) if naive_vectors else 0.0,
            "note": "L0 for ALL (findable) + richer vectors only for usage-active cards. Unused stay L0; promoted "
                    "cards demote losslessly (recomputable). Cost tracks usage, not corpus size. serves_truth=false"}
    if include_full:
        plan["promotions_full"] = promotions
        plan["demotions_full"] = demotions
    return plan


def levels_view() -> dict[str, Any]:
    """The richness ladder + promotion policy (the one queryable view both the CLI and the tools serve)."""
    return {"levels": LEVELS, "thresholds": _PROMOTE_THRESHOLD,
            "weights": {"retrieved": _W_RETRIEVED, "selected": _W_SELECTED, "success": _W_SUCCESS,
                        "ambiguity": _W_AMBIGUITY},
            "candidate": True, "serves_truth": False}


def load_level_state(state_path: Optional[Path] = None) -> dict[str, int]:
    """Current earned level per primitive (absent card -> L0, the universal floor)."""
    path = Path(state_path or _LEVEL_STATE)
    if path.exists():
        try:
            return {str(pid): int(level) for pid, level in json.loads(path.read_text()).get("levels", {}).items()}
        except (json.JSONDecodeError, OSError, ValueError):
            pass
    return {}


def apply_plan(*, confirm: bool = False, n_corpus: int = DEFAULT_CORPUS_SIZE, ts: str = "",
               state_path: Optional[Path] = None, history_path: Optional[Path] = None,
               worklist_path: Optional[Path] = None, ledger_path: Optional[Path] = None) -> dict[str, Any]:
    """GUARDED apply: persist earned level changes losslessly and emit the vector-build worklist.

    Recomputes the plan from the CURRENT state + the real usage ledger, considering every card in either (so a
    card whose usage evaporated demotes back toward L0). Writes: `level_state.json` (current levels),
    `level_history.jsonl` (append-only — every change survives forever), and `vector_build_worklist.jsonl` (the
    derived queue the embedding builders consume: which surfaces/models each promoted card now earns). Vector
    materialization itself stays with the builders (build_primitive_embeddings / the multi-model store) — this
    records WHAT is earned; demoted vectors are recomputable, so demotion is lossless by construction.
    """
    current = load_level_state(state_path)
    signals = signals_from_ledger(ledger_path)
    considered = {pid: signals.get(pid, {}) for pid in set(signals) | set(current)}
    plan = waterfall_plan(current, considered, n_corpus=n_corpus, include_full=True)
    if not confirm:
        preview = {k: v for k, v in plan.items() if not k.endswith("_full")}
        return {"applied": False, "reason": "guard: pass confirm=true to persist level changes (preview below).",
                "plan": preview, "candidate": True, "serves_truth": False}

    state_file = Path(state_path or _LEVEL_STATE)
    history_file = Path(history_path or _LEVEL_HISTORY)
    worklist_file = Path(worklist_path or _BUILD_WORKLIST)
    state_file.parent.mkdir(parents=True, exist_ok=True)
    history_file.parent.mkdir(parents=True, exist_ok=True)
    worklist_file.parent.mkdir(parents=True, exist_ok=True)

    changes = ([{**row, "kind": "promotion"} for row in plan["promotions_full"]]
               + [{**row, "kind": "demotion"} for row in plan["demotions_full"]])
    with history_file.open("a") as history:
        for change in changes:
            history.write(json.dumps({"ts": ts, **change, "candidate": True, "serves_truth": False},
                                     sort_keys=True) + "\n")
    for change in changes:
        current[change["primitive_id"]] = change["to"]
    state_file.write_text(json.dumps(
        {"schema_version": "adaptive-vectorization-level-state/v1", "ts": ts,
         "levels": {pid: level for pid, level in sorted(current.items()) if level > 0},
         "candidate": True, "serves_truth": False}, indent=2, sort_keys=True))

    worklist = [{"primitive_id": row["primitive_id"], "to_level": row["to"],
                 "surfaces": LEVELS[row["to"]]["surfaces"], "models": LEVELS[row["to"]]["models"],
                 "add_vectors": row["add_vectors"], "candidate": True, "serves_truth": False}
                for row in plan["promotions_full"]]
    worklist_file.write_text("".join(json.dumps(item, sort_keys=True) + "\n" for item in worklist))

    return {"applied": True, "promotions": plan["promotions"], "demotions": plan["demotions"],
            "added_vectors": plan["added_vectors"], "worklist_items": len(worklist),
            "sample_worklist": worklist[:10], "state_path": str(state_file), "history_path": str(history_file),
            "worklist_path": str(worklist_file),
            "note": "levels persisted; vector materialization is the embedding builders' job (worklist emitted). "
                    "History is append-only — demotion never erases lineage. serves_truth=false",
            "candidate": True, "serves_truth": False}


def _self_test() -> int:
    checks: list[tuple[str, bool, str]] = []

    # (1) the ladder is cumulative + universal L0.
    checks.append((f"waterfall ladder {list(LEVELS)} with growing vector budgets ({[LEVELS[l]['vectors'] for l in LEVELS]})",
                   LEVELS[0]["vectors"] == 1 and all(LEVELS[i]["vectors"] <= LEVELS[i + 1]["vectors"] for i in range(MAX_LEVEL)),
                   ""))

    # (2) an UNUSED card stays L0; a lightly-queried card earns L1; a frequently-implemented card earns a high level.
    checks.append(("unused->L0, queried->L1, heavily-used->high level",
                   target_level(usefulness_score({})) == 0
                   and target_level(usefulness_score({"retrieved": 1})) == 1
                   and target_level(usefulness_score({"success": 20})) >= 3, ""))

    # (3) success is worth much more than a bare retrieval (a used card outranks a noisy one).
    checks.append(("selection/success weighted far above bare retrieval",
                   usefulness_score({"success": 1}) > usefulness_score({"retrieved": 5}), ""))

    # (4) signals_from_ledger reads events; a searched+implemented card gets retrieved+success signals.
    import tempfile
    from scripts import primitive_usage_ledger as _ul
    with tempfile.TemporaryDirectory() as td:
        led = Path(td) / "e.jsonl"
        _ul.log_search("q", [{"primitive_id": "p:hot"}], ts="t0", ledger_path=led)
        _ul.log_implement("p:hot", success=True, query_text="q", ts="t1", ledger_path=led)
        sig = signals_from_ledger(led)
        checks.append(("signals from ledger: p:hot has retrieved+success",
                       sig.get("p:hot", {}).get("retrieved") == 1 and sig["p:hot"]["success"] == 1, json.dumps(sig.get("p:hot"))))

    # (5) waterfall_plan shows a big storage reduction vs materializing everyone at max level.
    plan = waterfall_plan({}, {"p:hot": {"retrieved": 10, "selected": 5, "success": 3}}, n_corpus=100000)
    checks.append((f"plan: adaptive {plan['adaptive_vectors']} vs naive {plan['naive_vectors_all_max']} vectors "
                   f"({plan['storage_reduction_vs_naive']:.0%} less)",
                   plan["storage_reduction_vs_naive"] > 0.5 and plan["promotions"] == 1, ""))

    # (6) DETERMINISM.
    checks.append(("scoring deterministic", usefulness_score({"retrieved": 2, "success": 1})
                   == usefulness_score({"retrieved": 2, "success": 1}), ""))

    # (7) APPLY is guarded, persists levels, appends lossless history, emits the build worklist.
    with tempfile.TemporaryDirectory() as td:
        led = Path(td) / "e.jsonl"
        state = Path(td) / "state.json"
        history = Path(td) / "history.jsonl"
        worklist = Path(td) / "worklist.jsonl"
        _ul.log_search("q", [{"primitive_id": "p:hot"}], ts="t0", ledger_path=led)
        for i in range(6):
            _ul.log_implement("p:hot", success=True, query_text="q", ts=f"t{i + 1}", ledger_path=led)
        refused = apply_plan(confirm=False, n_corpus=100, ts="t9", state_path=state, history_path=history,
                             worklist_path=worklist, ledger_path=led)
        refused_wrote_nothing = refused["applied"] is False and "plan" in refused and not state.exists()
        applied = apply_plan(confirm=True, n_corpus=100, ts="t9", state_path=state, history_path=history,
                             worklist_path=worklist, ledger_path=led)
        levels_now = load_level_state(state)
        checks.append(("apply guarded (no confirm -> preview, nothing written), then persists an earned promotion",
                       refused_wrote_nothing and applied["applied"] is True and levels_now.get("p:hot", 0) >= 3
                       and applied["worklist_items"] == 1 and worklist.exists(), json.dumps(applied)))

        # (8) usage evaporates -> the card DEMOTES, and history keeps BOTH movements (lossless, append-only).
        empty_ledger = Path(td) / "empty.jsonl"
        demoted = apply_plan(confirm=True, n_corpus=100, ts="t10", state_path=state, history_path=history,
                             worklist_path=worklist, ledger_path=empty_ledger)
        history_rows = [json.loads(l) for l in history.read_text().splitlines()]
        kinds = [(r["kind"], r["primitive_id"]) for r in history_rows]
        checks.append(("stale usage demotes to L0; history preserves promotion AND demotion",
                       demoted["demotions"] == 1 and load_level_state(state).get("p:hot", 0) == 0
                       and ("promotion", "p:hot") in kinds and ("demotion", "p:hot") in kinds,
                       json.dumps(kinds)))

    ok = all(c[1] for c in checks)
    print(f"{'PASS' if ok else 'FAIL'} - adaptive_vectorization: {len(LEVELS)}-level vector waterfall (L0 universal + "
          f"usage-earned promotions), signals from the usage ledger, lossless demote. serves_truth=false")
    for name, passed, detail in checks:
        print(f"  [{'ok' if passed else 'XX'}] {name}" + (f"  ({detail})" if not passed else ""))
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Waterfall vectorization: richer vectors only when usage justifies them.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--levels", action="store_true", help="print the richness ladder + thresholds")
    ap.add_argument("--plan", action="store_true", help="compute the promotion plan from the real usage ledger")
    ap.add_argument("--apply", action="store_true", help="persist earned level changes + emit the build worklist")
    ap.add_argument("--confirm", action="store_true", help="required with --apply to actually write")
    ap.add_argument("--state", action="store_true", help="current persisted level distribution")
    ap.add_argument("--n-corpus", type=int, default=DEFAULT_CORPUS_SIZE)
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.levels:
        print(json.dumps(levels_view(), indent=2))
        return 0
    if args.plan:
        print(json.dumps(waterfall_plan(load_level_state(), signals_from_ledger(), n_corpus=args.n_corpus), indent=2))
        return 0
    if args.apply:
        from datetime import datetime, timezone  # noqa: PLC0415  wall-clock only at the CLI edge (tests inject ts)
        print(json.dumps(apply_plan(confirm=args.confirm, n_corpus=args.n_corpus,
                                    ts=datetime.now(timezone.utc).isoformat(timespec="seconds")), indent=2))
        return 0
    if args.state:
        levels = load_level_state()
        by_level: dict[int, int] = {}
        for level in levels.values():
            by_level[level] = by_level.get(level, 0) + 1
        print(json.dumps({"promoted_cards": len(levels), "by_level": {str(k): v for k, v in sorted(by_level.items())},
                          "state_path": str(_LEVEL_STATE), "candidate": True, "serves_truth": False}, indent=2))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
