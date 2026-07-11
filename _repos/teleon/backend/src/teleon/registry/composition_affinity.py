"""Composition affinity — LEARNED connection strengths between primitive edges (W1, 2026-07-01).

Answers the ranking question the static matchers cannot: *which components actually go together?*
`primitive_match` classifies what CAN chain; this module learns what DOES chain well, from three
deterministic evidence streams (no model calls, candidate-only):

  * SEED   — source-backed primitive GROUP cards: their ordered hidden member edges are known-good chains.
  * RUNS   — composition outcomes (a DAG run succeeded/failed with pair P feeding C) appended to a ledger.
  * TRIAGE — human accept/reuse (+) and dismiss/wrong-match (−) outcomes: negative memory suppresses pairs.

Scores are deterministic: log-scaled seed counts + outcome-weighted, recency-decayed ledger events
(half-life below). Consumers (`primitive_match` scoring, `registry_search` ranking) treat the score as a
BOOST signal only — affinity never overrides contract compatibility, and nothing here serves truth.
Pair ids are minted via ``canonical_id`` (naming law; never hand-rolled hashing).
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import json
import math
import sys
import time
from pathlib import Path

py_const_src_teleon_registry_composition_affinity__REPO = Path(__file__).resolve().parents[3]
if str(py_const_src_teleon_registry_composition_affinity__REPO) not in sys.path:
    sys.path.insert(0, str(py_const_src_teleon_registry_composition_affinity__REPO))

from src.teleon.experiments.ids import canonical_id

py_const_src_teleon_registry_composition_affinity__DEFAULT_LEDGER_PATH = (
    _resource("data") / "dev-intel" / "composition_affinity" / "affinity_ledger.jsonl"
)
py_const_src_teleon_registry_composition_affinity__DEFAULT_GROUP_CARDS_PATH = (
    _resource("data") / "dev-intel" / "aidevobserver_edge_foundry" / "source_backed_primitive_group_cards.jsonl"
)
#: recency half-life for ledger events, in seconds (30 days) — old evidence fades, never vanishes.
py_const_src_teleon_registry_composition_affinity__DECAY_HALF_LIFE_SECONDS = 30 * 24 * 3600.0
#: outcome weights: positive evidence strengthens a pair, negative memory suppresses it.
py_const_src_teleon_registry_composition_affinity__OUTCOME_WEIGHTS = {
    "success": 1.0, "accepted": 1.0, "reused": 1.25,
    "failure": -1.0, "dismissed": -1.0, "wrong_match": -1.5,
}


def py_function_src_teleon_registry_composition_affinity__pair_id(
    py_arg_src_teleon_registry_composition_affinity__pair_id__producer_edge: str,
    py_arg_src_teleon_registry_composition_affinity__pair_id__consumer_edge: str,
) -> str:
    """Deterministic id for an ordered (producer_edge, consumer_edge) pair."""

    return canonical_id(
        "affpair",
        str(py_arg_src_teleon_registry_composition_affinity__pair_id__producer_edge).strip(),
        str(py_arg_src_teleon_registry_composition_affinity__pair_id__consumer_edge).strip(),
    )


def py_function_src_teleon_registry_composition_affinity__seed_pairs_from_group_cards(
    py_arg_src_teleon_registry_composition_affinity__seed_pairs_from_group_cards__path: Path | str | None = None,
) -> dict[str, dict]:
    """Count consecutive member-edge pairs across source-backed group cards (known-good chains)."""

    path = Path(
        py_arg_src_teleon_registry_composition_affinity__seed_pairs_from_group_cards__path
        or py_const_src_teleon_registry_composition_affinity__DEFAULT_GROUP_CARDS_PATH
    )
    pairs: dict[str, dict] = {}
    if not path.is_file():
        return pairs
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if not line.strip():
            continue
        try:
            card = json.loads(line)
        except ValueError:
            continue
        contract = card.get("group_contract") or {}
        member_edges = [str(e).strip() for e in (contract.get("hidden_member_edges") or []) if str(e).strip()]
        for producer_edge, consumer_edge in zip(member_edges, member_edges[1:]):
            key = py_function_src_teleon_registry_composition_affinity__pair_id(producer_edge, consumer_edge)
            row = pairs.setdefault(key, {
                "pair_id": key, "producer_edge": producer_edge, "consumer_edge": consumer_edge,
                "seed_count": 0, "candidate": True, "serves_truth": False,
            })
            row["seed_count"] += 1
    return pairs


def py_function_src_teleon_registry_composition_affinity__record_composition(
    py_arg_src_teleon_registry_composition_affinity__record_composition__producer_edge: str,
    py_arg_src_teleon_registry_composition_affinity__record_composition__consumer_edge: str,
    py_arg_src_teleon_registry_composition_affinity__record_composition__outcome: str,
    *,
    py_arg_src_teleon_registry_composition_affinity__record_composition__at: float | None = None,
    py_arg_src_teleon_registry_composition_affinity__record_composition__ledger_path: Path | str | None = None,
) -> dict:
    """Append one composition outcome to the ledger (append-only; the ledger is the learning memory)."""

    outcome = str(py_arg_src_teleon_registry_composition_affinity__record_composition__outcome).strip().lower()
    if outcome not in py_const_src_teleon_registry_composition_affinity__OUTCOME_WEIGHTS:
        raise ValueError(f"unknown outcome {outcome!r}; expected one of "
                         f"{sorted(py_const_src_teleon_registry_composition_affinity__OUTCOME_WEIGHTS)}")
    path = Path(
        py_arg_src_teleon_registry_composition_affinity__record_composition__ledger_path
        or py_const_src_teleon_registry_composition_affinity__DEFAULT_LEDGER_PATH
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "record_type": "composition_affinity_event",
        "schema_version": "composition_affinity_event",
        "pair_id": py_function_src_teleon_registry_composition_affinity__pair_id(
            py_arg_src_teleon_registry_composition_affinity__record_composition__producer_edge,
            py_arg_src_teleon_registry_composition_affinity__record_composition__consumer_edge,
        ),
        "producer_edge": str(py_arg_src_teleon_registry_composition_affinity__record_composition__producer_edge).strip(),
        "consumer_edge": str(py_arg_src_teleon_registry_composition_affinity__record_composition__consumer_edge).strip(),
        "outcome": outcome,
        "at": float(py_arg_src_teleon_registry_composition_affinity__record_composition__at
                    if py_arg_src_teleon_registry_composition_affinity__record_composition__at is not None
                    else time.time()),
        "candidate": True,
        "serves_truth": False,
    }
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, sort_keys=True) + "\n")
    return row


def py_function_src_teleon_registry_composition_affinity__load_affinity_table(
    *,
    py_arg_src_teleon_registry_composition_affinity__load_affinity_table__ledger_path: Path | str | None = None,
    py_arg_src_teleon_registry_composition_affinity__load_affinity_table__group_cards_path: Path | str | None = None,
    py_arg_src_teleon_registry_composition_affinity__load_affinity_table__now: float | None = None,
) -> dict[str, dict]:
    """Fold seeds + decayed ledger outcomes into {pair_id -> row with 'affinity' score}."""

    now = float(py_arg_src_teleon_registry_composition_affinity__load_affinity_table__now
                if py_arg_src_teleon_registry_composition_affinity__load_affinity_table__now is not None
                else time.time())
    table = py_function_src_teleon_registry_composition_affinity__seed_pairs_from_group_cards(
        py_arg_src_teleon_registry_composition_affinity__load_affinity_table__group_cards_path)
    ledger = Path(
        py_arg_src_teleon_registry_composition_affinity__load_affinity_table__ledger_path
        or py_const_src_teleon_registry_composition_affinity__DEFAULT_LEDGER_PATH
    )
    if ledger.is_file():
        for line in ledger.read_text(encoding="utf-8", errors="replace").splitlines():
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except ValueError:
                continue
            weight = py_const_src_teleon_registry_composition_affinity__OUTCOME_WEIGHTS.get(event.get("outcome"))
            if weight is None:
                continue
            age = max(0.0, now - float(event.get("at") or now))
            decay = 0.5 ** (age / py_const_src_teleon_registry_composition_affinity__DECAY_HALF_LIFE_SECONDS)
            row = table.setdefault(event.get("pair_id"), {
                "pair_id": event.get("pair_id"),
                "producer_edge": event.get("producer_edge"), "consumer_edge": event.get("consumer_edge"),
                "seed_count": 0, "candidate": True, "serves_truth": False,
            })
            row["outcome_weight"] = row.get("outcome_weight", 0.0) + weight * decay
    for row in table.values():
        row["affinity"] = round(math.log1p(row.get("seed_count", 0)) + row.get("outcome_weight", 0.0), 6)
    return table


def py_function_src_teleon_registry_composition_affinity__affinity_boost(
    py_arg_src_teleon_registry_composition_affinity__affinity_boost__producer_edge: str,
    py_arg_src_teleon_registry_composition_affinity__affinity_boost__consumer_edge: str,
    py_arg_src_teleon_registry_composition_affinity__affinity_boost__table: dict[str, dict],
) -> float:
    """Ranking BOOST for a candidate pair (0.0 for unknown pairs; never a compatibility override)."""

    key = py_function_src_teleon_registry_composition_affinity__pair_id(
        py_arg_src_teleon_registry_composition_affinity__affinity_boost__producer_edge,
        py_arg_src_teleon_registry_composition_affinity__affinity_boost__consumer_edge,
    )
    row = py_arg_src_teleon_registry_composition_affinity__affinity_boost__table.get(key)
    return float(row.get("affinity", 0.0)) if row else 0.0


def py_function_src_teleon_registry_composition_affinity__self_test() -> int:
    import tempfile

    fails: list[str] = []

    def check(name: str, ok: bool, detail: str = "") -> None:
        print(f"  [{'ok' if ok else 'FAIL'}] {name}{(': ' + detail) if detail and not ok else ''}")
        if not ok:
            fails.append(name)

    with tempfile.TemporaryDirectory() as td:
        groups = Path(td) / "groups.jsonl"
        chain = ["RawCsv->ParsedRows", "ParsedRows->ValidRows", "ValidRows->ImportReceipt"]
        rare = ["Url->Html", "Html->TableRows"]
        groups.write_text("\n".join(json.dumps({"group_contract": {"hidden_member_edges": edges}})
                                    for edges in (chain, chain, rare)) + "\n", encoding="utf-8")
        ledger = Path(td) / "ledger.jsonl"
        now = 1_800_000_000.0  # fixed clock: the test is deterministic

        seeded = py_function_src_teleon_registry_composition_affinity__seed_pairs_from_group_cards(groups)
        check("seeding counts consecutive member-edge pairs across groups",
              len(seeded) == 3 and max(r["seed_count"] for r in seeded.values()) == 2)

        py_function_src_teleon_registry_composition_affinity__record_composition(
            "RawCsv->ParsedRows", "ParsedRows->ValidRows", "success",
            py_arg_src_teleon_registry_composition_affinity__record_composition__at=now - 3600,
            py_arg_src_teleon_registry_composition_affinity__record_composition__ledger_path=ledger)
        py_function_src_teleon_registry_composition_affinity__record_composition(
            "Url->Html", "Html->TableRows", "wrong_match",
            py_arg_src_teleon_registry_composition_affinity__record_composition__at=now - 3600,
            py_arg_src_teleon_registry_composition_affinity__record_composition__ledger_path=ledger)
        table = py_function_src_teleon_registry_composition_affinity__load_affinity_table(
            py_arg_src_teleon_registry_composition_affinity__load_affinity_table__ledger_path=ledger,
            py_arg_src_teleon_registry_composition_affinity__load_affinity_table__group_cards_path=groups,
            py_arg_src_teleon_registry_composition_affinity__load_affinity_table__now=now)
        strong = py_function_src_teleon_registry_composition_affinity__affinity_boost(
            "RawCsv->ParsedRows", "ParsedRows->ValidRows", table)
        suppressed = py_function_src_teleon_registry_composition_affinity__affinity_boost(
            "Url->Html", "Html->TableRows", table)
        unknown = py_function_src_teleon_registry_composition_affinity__affinity_boost("A", "B", table)
        check("repeated + succeeded pair outranks rare pair; dismissal SUPPRESSES (negative memory)",
              strong > math.log1p(2) > 0 > suppressed, f"strong={strong} suppressed={suppressed}")
        check("unknown pair boosts exactly 0.0 (affinity never invents compatibility)", unknown == 0.0)

        old_table = py_function_src_teleon_registry_composition_affinity__load_affinity_table(
            py_arg_src_teleon_registry_composition_affinity__load_affinity_table__ledger_path=ledger,
            py_arg_src_teleon_registry_composition_affinity__load_affinity_table__group_cards_path=groups,
            py_arg_src_teleon_registry_composition_affinity__load_affinity_table__now=now + 90 * 24 * 3600)
        check("evidence DECAYS with age (90-day-old outcome is weaker, half-life 30d)",
              py_function_src_teleon_registry_composition_affinity__affinity_boost(
                  "RawCsv->ParsedRows", "ParsedRows->ValidRows", old_table) < strong)

        rows = [json.loads(line) for line in ledger.read_text().splitlines()]
        check("ledger rows carry the truth boundary + canonical pair ids",
              all(r["candidate"] is True and r["serves_truth"] is False
                  and r["pair_id"].startswith("affpair-") and len(r["pair_id"].split("-")[-1]) == 16
                  for r in rows))
        try:
            py_function_src_teleon_registry_composition_affinity__record_composition(
                "A", "B", "vibes",
                py_arg_src_teleon_registry_composition_affinity__record_composition__ledger_path=ledger)
            check("negative: unknown outcome is rejected", False)
        except ValueError:
            check("negative: unknown outcome is rejected", True)

    real = py_function_src_teleon_registry_composition_affinity__seed_pairs_from_group_cards()
    print(f"  [info] production seed source: {len(real)} pairs from source-backed group cards")

    print(f"\n{'PASS - composition_affinity: connection strengths seed from known-good chains, learn from outcomes with decay + negative memory, and only ever BOOST ranking' if not fails else str(len(fails)) + ' FAILURES: ' + str(fails)}")
    return 0 if not fails else 1


if __name__ == "__main__":
    raise SystemExit(py_function_src_teleon_registry_composition_affinity__self_test())
