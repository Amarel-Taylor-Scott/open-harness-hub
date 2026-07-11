"""deterministic_plane — unify the deterministic trio (descriptions · edges · remix), self-tune the edge
strategy per corpus, and roll up the token savings.

Owner (2026-07-11): "self tuning ... deterministic descriptions, deterministic remixing, deterministic edges."
This plane applies all three at 0 tokens, then SELF-TUNES: it measures which edge-derivation strategy makes
the most primitive pairs EXACTLY composable on THIS corpus and picks the champion non-destructively — because
"not all solutions work for every shape of data." The headline it proves: canonicalizing edges turns a corpus
with ~0 exact joins (independently-named edges) into one that composes, at 0 tokens.

    python3 scripts/deterministic_plane.py --self-test
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Callable

_HERE = Path(__file__).resolve()
_SBC = _HERE.parent.parent
for _p in (str(_SBC), str(_SBC / "scripts")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from scripts.deterministic_description import describe_registers
from scripts.deterministic_edge_derivation import normalize_edge
from scripts.deterministic_remix import remix_all

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
#: measured per-row LLM cost the deterministic plane REPLACES (description-backfill ≈ this many output tokens
#: per row for a 3-register description; edges + glue add more). Conservative; labeled an estimate.
_LLM_BASELINE_TOKENS_PER_CARD = 220


def apply_plane(card: dict[str, Any]) -> dict[str, Any]:
    """0-token enrichment: canonical edges + 3 deterministic description registers. Non-destructive."""
    out = dict(card)
    out["input_edge_raw"], out["output_edge_raw"] = card.get("input_edge", ""), card.get("output_edge", "")
    out["input_edge"] = normalize_edge(card.get("input_edge", ""))
    out["output_edge"] = normalize_edge(card.get("output_edge", ""))
    out["description_registers"] = describe_registers(out)
    out["deterministic_plane"] = {"edges": "canonical", "descriptions": 3, "token_cost": 0}
    return out


def count_exact_composable(cards: list[dict[str, Any]]) -> int:
    """Ordered pairs (a,b) where a.output_edge == b.input_edge exactly — the composition-health metric."""
    outs: dict[str, int] = {}
    for c in cards:
        outs[c["output_edge"]] = outs.get(c["output_edge"], 0) + 1
    total = 0
    for c in cards:
        total += outs.get(c["input_edge"], 0)
    return total


#: edge strategies to race (self-tuning). Each maps a card → (input_edge, output_edge).
EDGE_STRATEGIES: dict[str, Callable[[dict[str, Any]], tuple[str, str]]] = {
    "raw": lambda c: (c.get("input_edge", ""), c.get("output_edge", "")),
    "canonical": lambda c: (normalize_edge(c.get("input_edge", "")), normalize_edge(c.get("output_edge", ""))),
}


def selftune_edges(cards: list[dict[str, Any]]) -> dict[str, Any]:
    """Race edge strategies on THIS corpus; pick the one maximizing exact-composable pairs. Non-destructive:
    every strategy's score is kept; the champion is returned, losers retained as fallbacks."""
    scored = []
    for name, fn in EDGE_STRATEGIES.items():
        applied = [{"input_edge": (e := fn(c))[0], "output_edge": e[1]} for c in cards]
        scored.append({"strategy": name, "exact_composable_pairs": count_exact_composable(applied)})
    scored.sort(key=lambda s: (-s["exact_composable_pairs"], s["strategy"]))
    return {"champion": scored[0]["strategy"], "scoreboard": scored,
            "non_destructive": True, "token_cost": 0, **BOUNDARY}


def plane_savings(n_cards: int) -> dict[str, Any]:
    """Roll-up: the deterministic plane produces descriptions + edges (+ enables remix glue) at 0 tokens for
    the whole corpus, vs an LLM baseline. Labeled: baseline is an estimate, plane cost is exactly 0."""
    return {"cards": n_cards, "llm_baseline_tokens": n_cards * _LLM_BASELINE_TOKENS_PER_CARD,
            "deterministic_plane_tokens": 0,
            "note": f"~{_LLM_BASELINE_TOKENS_PER_CARD} output tok/card (est.) for LLM descriptions+edges → 0 "
                    f"deterministic; remix glue is 0-token too. Stacks with the recipe input/output savings.",
            **BOUNDARY}


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    # a corpus where two cards touch the same TYPE but under divergent raw names (the real-world case)
    corpus = [
        {"title": "reqwest", "input_edge": "HttpRequestSpec", "output_edge": "JSON",
         "capability_class": "http_client", "usage_recipes": [{"symbols": ["reqwest.get"], "snippet": "r=get()"}]},
        {"title": "serde_json", "input_edge": "json_bytes", "output_edge": "dict",
         "capability_class": "deserialize", "usage_recipes": [{"symbols": ["serde_json.from"], "snippet": "v=from()"}]},
    ]

    # SELF-TUNING: canonical strategy beats raw (raw: JSON≠json_bytes → 0 joins; canonical: both JsonBytes → joins)
    tune = selftune_edges(corpus)
    raw_score = next(s["exact_composable_pairs"] for s in tune["scoreboard"] if s["strategy"] == "raw")
    can_score = next(s["exact_composable_pairs"] for s in tune["scoreboard"] if s["strategy"] == "canonical")
    checks.append(("self-tune picks 'canonical' — it composes where 'raw' does not (0→>0 exact pairs)",
                   tune["champion"] == "canonical" and raw_score == 0 and can_score >= 1))

    checks.append(("self-tune is non-destructive (both strategies scored + kept)",
                   len(tune["scoreboard"]) == 2 and tune["non_destructive"] and tune["token_cost"] == 0))

    # apply_plane enriches at 0 tokens: canonical edges + 3 registers, raw edges preserved
    en = apply_plane(corpus[0])
    checks.append(("apply_plane: canonical edges + 3 registers at 0 tokens, raw edges preserved",
                   en["output_edge"] == "JsonBytes" and en["output_edge_raw"] == "JSON"
                   and len(en["description_registers"]) == 3 and en["deterministic_plane"]["token_cost"] == 0))

    # after the plane, the corpus actually remixes (reqwest→serde_json over JsonBytes)
    planed = [apply_plane(c) for c in corpus]
    planed[0]["id"], planed[1]["id"] = "reqwest", "serde_json"
    chains = remix_all(planed, "HttpRequestSpec", "Mapping")
    checks.append(("post-plane the corpus REMIXES exactly (reqwest→serde_json→Mapping, 0 tokens)",
                   len(chains) >= 1 and chains[0]["members"] == ["reqwest", "serde_json"]
                   and chains[0]["token_cost"] == 0))

    # savings roll-up: whole corpus of descriptions+edges at 0 tokens vs a positive LLM baseline
    sav = plane_savings(1000)
    checks.append(("savings roll-up: 0 deterministic tokens vs a positive LLM baseline",
                   sav["deterministic_plane_tokens"] == 0 and sav["llm_baseline_tokens"] > 0))

    # deterministic
    checks.append(("plane deterministic (byte-identical enrichment + tuning)",
                   json.dumps(apply_plane(corpus[0]), sort_keys=True) == json.dumps(en, sort_keys=True)
                   and json.dumps(selftune_edges(corpus), sort_keys=True) == json.dumps(tune, sort_keys=True)))

    ok = all(v for _, v in checks)
    print("deterministic_plane — self-test")
    for name, v in checks:
        print(f"  [{'ok' if v else 'FAIL'}] {name}")
    print(f"  self-tune: raw={raw_score} exact pairs → canonical={can_score} (champion). "
          f"Descriptions+edges+remix glue all 0-token. Baseline saved: "
          f"{plane_savings(1000)['llm_baseline_tokens']:,} tok/1K cards.")
    print("PASS" if ok else "FAIL")
    return 0 if ok else 1


def _main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    ap.parse_args()
    return _self_test()


if __name__ == "__main__":
    raise SystemExit(_main())
