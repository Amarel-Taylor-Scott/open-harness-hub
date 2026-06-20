#!/usr/bin/env python3
"""Corpus-acquisition grid — the cell schema and the value function.

Implements §1–§2 of the corpus-acquisition build spec
(docs/strategy/corpus-acquisition-grid-spec.md).

ONE PRINCIPLE: collect the negative space, not the head. If you ask an LLM what
to collect, it returns the well-covered head of the distribution — exactly what
you don't need. So cell selection here is driven by EXTERNAL importance signals
(regulator issuance velocity, enforcement/FATF events, buyer demand, query-miss
logs) MINUS a measured coverage map — never by a model's opinion. There is
deliberately no LLM call in this module.

A `cell` is the unit of acquisition:
    (jurisdiction, industry, source_type, time_window, publisher_type, use_case)
The full grid is combinatorially huge and cannot be crawled. The value function
is what searches it efficiently: expand the highest-value, emptiest cells first.
`expected_lift` is the capability-lift gate (scripts/eval/reason_codes.py) lifted
one level — from "what to keep" to "what to go get".
"""
from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field

from scripts.eval.reason_codes import MAX_TIER, TIER_BY_KEY, gap_durability_score

# Value-function weights (named, with rationale). Single source — tune here only.
W_LIFT = 1.4          # how badly base models fail here (primary driver)
W_PAYS = 1.2          # buyer budget / legal mandate in this cell
W_SOURCEABLE = 0.8    # how reachable authoritative sources are (tier score)
W_VOLATILITY = 1.0    # regulatory-change velocity → durable, recency-based lift
W_COVERAGE = 1.3      # PENALTY: how much we already hold — forces us to empty cells
W_COST = 0.7          # PENALTY: crawl + parse + maintain effort


def _slug(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", str(text).lower()).strip("-") or "x"


@dataclass(frozen=True)
class Cell:
    """One acquisition cell. `cell_id` is deterministic (stable hash suffix, no
    version) so daily queues don't collapse during dedupe/merge."""
    jurisdiction: str          # ISO 3166 (PH, ID, NG, …) + sub-national if needed
    industry: str              # NACE/ISIC-aligned (labor, financial-crime, customs, …)
    source_type: str = "primary_regulator"
    time_window: str = "all"   # issuance date bucket (enables CDC + recency targeting)
    publisher_type: str = "government_primary"
    use_case: str = "screening"

    @property
    def cell_id(self) -> str:
        parts = (self.jurisdiction, self.industry, self.source_type,
                 self.time_window, self.publisher_type, self.use_case)
        digest = hashlib.sha1("|".join(p.lower() for p in parts).encode()).hexdigest()[:10]
        return f"cell/{_slug(self.jurisdiction)}-{_slug(self.industry)}-{digest}"


@dataclass
class CellSignals:
    """External, model-independent signals (all 0..1). The whole point is that
    none of these come from an LLM proposing topics."""
    expected_lift: float = 0.0      # base-model failure here (see expected_lift_from)
    pays: float = 0.0               # mandate/budget (enforcement, FATF status, buyers)
    sourceable: float = 0.0         # reachability (see sourceable_from_tier)
    volatility: float = 0.0         # issuance velocity / change events
    current_coverage: float = 0.0   # measured by the coverage instrument (§7)
    acquisition_cost: float = 0.0   # crawl/parse/maintain effort
    query_misses: int = 0           # registry questions we couldn't answer (purest gap signal)
    notes: list[str] = field(default_factory=list)


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, float(value)))


def sourceable_from_tier(retrievability_tier: int | str) -> float:
    """Tier 1 (clean API) = most sourceable → 1.0; tier 5 (human-only) → low."""
    tier = retrievability_tier
    if isinstance(tier, str):
        tier = int(TIER_BY_KEY.get(tier, {}).get("tier", MAX_TIER))
    tier = max(1, min(MAX_TIER, int(tier)))
    return round((MAX_TIER - tier) / (MAX_TIER - 1), 3)  # 1→1.0 … MAX_TIER→0.0


def expected_lift_from(*, lift_reason=None, retrievability_tier=None,
                       adversarial=False, mechanisms=None) -> float:
    """The lift gate, lifted one level: durability score normalized to 0..1.
    Reuses the single-source scorer so the grid and the gate never drift."""
    score = gap_durability_score(
        reason_codes=[lift_reason] if lift_reason else [],
        retrievability_tier=retrievability_tier,
        adversarial=adversarial,
        mechanisms=mechanisms or [],
    )
    return round(score / 5.0, 3)


def cell_priority(signals: CellSignals) -> float:
    """Guided-acquisition score. Higher = acquire sooner. Coverage and cost
    SUBTRACT — that is what forces the system toward the negative space."""
    misses = _clamp01(signals.query_misses / 10.0)  # 10+ misses saturates the demand signal
    return round(
        W_LIFT * _clamp01(signals.expected_lift)
        + W_PAYS * _clamp01(max(signals.pays, misses))
        + W_SOURCEABLE * _clamp01(signals.sourceable)
        + W_VOLATILITY * _clamp01(signals.volatility)
        - W_COVERAGE * _clamp01(signals.current_coverage)
        - W_COST * _clamp01(signals.acquisition_cost),
        4,
    )


def rank_cells(cells: list[tuple[Cell, CellSignals]]) -> list[dict]:
    """Rank (cell, signals) pairs by descending priority — the acquisition queue."""
    scored = [{"cell_id": c.cell_id, "jurisdiction": c.jurisdiction, "industry": c.industry,
               "use_case": c.use_case, "priority": cell_priority(s)} for c, s in cells]
    return sorted(scored, key=lambda r: r["priority"], reverse=True)


def _self_test() -> int:
    # The spec's two worked cells: the value function must rank PH financial-crime
    # (high lift × high pays × high volatility, mixed sourceable, low coverage)
    # ABOVE PH labor (medium across the board).
    bsp = (Cell("PH", "financial-crime", "primary_regulator", "2026", "government_primary", "screening"),
           CellSignals(expected_lift=expected_lift_from(lift_reason="volatile_fact",
                                                        retrievability_tier="unstructured_addressable"),
                       pays=0.95, sourceable=0.5, volatility=0.9, current_coverage=0.1,
                       acquisition_cost=0.5, query_misses=6))
    dole = (Cell("PH", "labor", "primary_regulator", "all", "government_primary", "eligibility"),
            CellSignals(expected_lift=expected_lift_from(lift_reason="esoteric_rule",
                                                         retrievability_tier="structured_no_api"),
                        pays=0.5, sourceable=0.6, volatility=0.5, current_coverage=0.2,
                        acquisition_cost=0.5, query_misses=1))
    ranked = rank_cells([dole, bsp])
    assert ranked[0]["industry"] == "financial-crime", ranked
    assert ranked[0]["priority"] > ranked[1]["priority"], ranked
    # determinism + no version in id
    assert bsp[0].cell_id == bsp[0].cell_id and "v1" not in bsp[0].cell_id
    # coverage penalty actually bites: same cell, fuller coverage → lower priority
    full = CellSignals(**{**bsp[1].__dict__, "current_coverage": 0.95})
    assert cell_priority(full) < cell_priority(bsp[1])
    print("cell_priority OK · ranked:", [(r["industry"], r["priority"]) for r in ranked],
          "· bsp_id", bsp[0].cell_id)
    return 0


if __name__ == "__main__":
    raise SystemExit(_self_test())
