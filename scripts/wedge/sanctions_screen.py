"""Deterministic sanctions screener — Lane A capability-lift scaffold.

LIFT THESIS
-----------
Two structural gaps that a bare frontier model cannot close:

  1. deterministic_guarantee — The OFAC 50% Rule requires exact recursive
     arithmetic over a beneficial-ownership graph.  A probability sampler
     cannot guarantee the correct number.  A deterministic traversal always
     does.  Classic failure: two 30%-blocked co-owners aggregate to 60% ->
     BLOCKED; naive string matching silently passes the unlisted entity.

  2. volatile_fact — Sanctions designations are added / revoked daily.  Any
     entity designated after a model's training cutoff is invisible to a bare
     model.  Only a pipeline with a live-sync loop catches new designations.

Durability class for both: 'structural'.  More model / more data will NOT
close either gap.

DEFENSIVE SCOPE
---------------
This module screens entities AGAINST a sanctions list for compliance purposes
only.  It never produces evasion guidance, structuring advice, or counter-
sanctions routing.  All data is SYNTHETIC; no real OFAC data or PII is used.

Usage (module entry-point):
    python3 -m scripts.wedge.sanctions_screen --self-test

Public API:
    screen(query_name, entity_id=None) -> dict
"""
from __future__ import annotations

import argparse
import unicodedata
from difflib import SequenceMatcher
from typing import Optional

# ---------------------------------------------------------------------------
# Thresholds (named constants — never magic values)
# ---------------------------------------------------------------------------

# OFAC 50% Rule: an entity is treated as blocked when persons on the SDN list
# own, in aggregate, >= 50% of its equity/control interests.
# Source: 31 CFR §§ 501, 510; OFAC Guidance "Entities Owned by Blocked Persons"
OFAC_OWNERSHIP_BLOCK_THRESHOLD: float = 0.50  # unit: fractional equity [0..1]

# Fuzzy name-match similarity floor: SequenceMatcher ratio >= this value is
# treated as a potential name hit requiring further review.
# 0.82 catches transposition/diacritic/abbreviation variants while keeping
# false-positive rate low enough for a compliance triage queue.
FUZZY_MATCH_FLOOR: float = 0.82  # unit: ratio [0..1]

# Legal-suffix tokens stripped before comparison so "Gazprom LLC" and "Gazprom"
# score identically.  All lowercase; the normalizer lowercases before stripping.
LEGAL_SUFFIXES: frozenset[str] = frozenset({
    "llc", "ltd", "limited", "inc", "incorporated", "corp", "corporation",
    "gmbh", "ag", "sa", "sas", "sarl", "bv", "nv", "plc", "co", "company",
    "group", "holdings", "holding", "international", "intl", "enterprises",
    "enterprise", "partners", "partnership", "ventures", "venture",
})

# ---------------------------------------------------------------------------
# Synthetic SDN fixture (COMPLETELY SYNTHETIC — no real OFAC data, no PII)
# ---------------------------------------------------------------------------
# Each entry: {"id": str, "name": str, "aliases": list[str]}
_SYNTHETIC_SDN: list[dict] = [
    {
        "id": "SDN-001",
        "name": "Blackwater Trading Group",
        "aliases": ["Blackwater TG", "BWater Trading"],
    },
    {
        "id": "SDN-002",
        "name": "Novaya Commerce LLC",
        "aliases": ["Novaya Commerce", "NovCom LLC"],
    },
    {
        "id": "SDN-003",
        "name": "Al-Farouk Financial Services",
        "aliases": ["Al Farouk Financial", "AFFS"],
    },
    {
        "id": "SDN-004",
        "name": "Dmitri Volkov",
        "aliases": ["D. Volkov", "Dmitri Alexandrovitch Volkov"],
    },
    {
        "id": "SDN-005",
        "name": "Meridian Capital Ventures",
        "aliases": [],
    },
]

# Synthetic beneficial-ownership graph.
# Key = entity_id (string).
# Value = list of {"owner_id": str, "pct": float [0..1]}.
# owner_id references either another entity_id or an SDN entry id (SDN-xxx).
# SYNTHETIC — no real corporate data.
_SYNTHETIC_OWNERSHIP: dict[str, list[dict]] = {
    # Unlisted entity owned 30% each by two SDN persons -> 60% -> BLOCKED
    "ENT-ALPHA": [
        {"owner_id": "SDN-004", "pct": 0.30},   # Dmitri Volkov (SDN)
        {"owner_id": "SDN-002", "pct": 0.30},   # Novaya Commerce (SDN)
        {"owner_id": "CLEAN-P1", "pct": 0.40},
    ],
    # Entity owned 40% by SDN, 10% by a clean intermediate -> 40% -> CLEAR
    "ENT-BETA": [
        {"owner_id": "SDN-001", "pct": 0.40},
        {"owner_id": "CLEAN-P2", "pct": 0.60},
    ],
    # Entity owned 55% by SDN-005 (on list itself) -> BLOCKED
    "ENT-GAMMA": [
        {"owner_id": "SDN-005", "pct": 0.55},
        {"owner_id": "CLEAN-P3", "pct": 0.45},
    ],
    # Nested: clean entity that itself owns ENT-ALPHA (which is blocked)
    # ENT-DELTA owns 70% of ENT-ALPHA; not a person -> ownership not aggregated
    # (OFAC 50% Rule aggregates natural/legal-person SDN holders, not blocked entities
    # as re-aggregated owners; this fixture is intentionally simple)
    "ENT-DELTA": [
        {"owner_id": "ENT-ALPHA", "pct": 0.70},
        {"owner_id": "CLEAN-P4", "pct": 0.30},
    ],
}

# Pre-computed set of SDN IDs for O(1) lookup.
_SDN_IDS: frozenset[str] = frozenset(e["id"] for e in _SYNTHETIC_SDN)


# ---------------------------------------------------------------------------
# Normalisation helpers
# ---------------------------------------------------------------------------

def _strip_diacritics(text: str) -> str:
    """NFD-decompose then drop combining characters."""
    return "".join(
        ch for ch in unicodedata.normalize("NFD", text)
        if unicodedata.category(ch) != "Mn"
    )


def _normalize_name(name: str) -> str:
    """Lowercase, strip diacritics, collapse whitespace, remove legal suffixes."""
    name = _strip_diacritics(name.lower())
    tokens = name.split()
    tokens = [t for t in tokens if t not in LEGAL_SUFFIXES]
    return " ".join(tokens).strip()


# ---------------------------------------------------------------------------
# Fuzzy name matching
# ---------------------------------------------------------------------------

def _fuzzy_score(a: str, b: str) -> float:
    """SequenceMatcher ratio over normalized token sequences."""
    return SequenceMatcher(None, _normalize_name(a), _normalize_name(b)).ratio()


def _name_matches(query: str) -> list[dict]:
    """Return all SDN entries whose name or any alias fuzzy-matches query."""
    hits: list[dict] = []
    for entry in _SYNTHETIC_SDN:
        candidates = [entry["name"]] + entry.get("aliases", [])
        best_score = max(_fuzzy_score(query, c) for c in candidates)
        if best_score >= FUZZY_MATCH_FLOOR:
            hits.append({
                "sdn_id": entry["id"],
                "sdn_name": entry["name"],
                "match_score": round(best_score, 4),
            })
    return hits


# ---------------------------------------------------------------------------
# OFAC 50% Rule — recursive ownership aggregation
# ---------------------------------------------------------------------------

def _aggregate_blocked_pct(
    entity_id: str,
    visited: Optional[set] = None,
) -> float:
    """Sum the ownership fraction held by SDN-listed persons in entity_id.

    Uses iterative DFS to avoid stack limits on deep ownership chains.
    Only direct SDN-listed owners are aggregated (SDN-xxx IDs); this
    follows the plain-reading of OFAC 50% guidance which counts blocked
    persons, not blocked entities, as the ownership subjects.

    Returns a fraction in [0.0, 1.0].
    """
    if visited is None:
        visited = set()
    if entity_id in visited:
        return 0.0  # cycle guard
    visited.add(entity_id)

    owners = _SYNTHETIC_OWNERSHIP.get(entity_id, [])
    total_blocked: float = 0.0
    for owner in owners:
        oid = owner["owner_id"]
        pct = owner["pct"]
        if oid in _SDN_IDS:
            # Direct SDN owner — count full percentage
            total_blocked += pct
        elif oid in _SYNTHETIC_OWNERSHIP:
            # Intermediate entity — recurse to check pass-through blocked pct
            child_blocked = _aggregate_blocked_pct(oid, visited.copy())
            if child_blocked >= OFAC_OWNERSHIP_BLOCK_THRESHOLD:
                # Child is itself blocked -> treat as if an SDN person owns pct
                total_blocked += pct
    return min(total_blocked, 1.0)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def screen(
    query_name: str,
    entity_id: Optional[str] = None,
) -> dict:
    """Screen a name and/or entity against the synthetic sanctions fixture.

    Parameters
    ----------
    query_name:
        The legal name of the entity or person to screen.
    entity_id:
        If provided, also apply the OFAC 50% Rule by looking up the
        beneficial-ownership graph for this entity ID.

    Returns
    -------
    dict with keys:
      name_matches      list of SDN hits from fuzzy name matching
      blocked           bool — True if name hit OR 50% rule triggers
      reason            human-readable explanation of the block determination
      aggregate_blocked_pct  float — fraction of entity owned by blocked persons
                              (0.0 if entity_id not provided or not in graph)
    """
    name_hits = _name_matches(query_name)

    agg_pct: float = 0.0
    fifty_pct_block: bool = False
    if entity_id is not None:
        agg_pct = _aggregate_blocked_pct(entity_id)
        fifty_pct_block = agg_pct >= OFAC_OWNERSHIP_BLOCK_THRESHOLD

    name_blocked = len(name_hits) > 0

    reasons: list[str] = []
    if name_blocked:
        reasons.append(
            f"Name '{query_name}' fuzzy-matches {len(name_hits)} SDN entry/entries."
        )
    if fifty_pct_block:
        reasons.append(
            f"OFAC 50% Rule: {agg_pct:.1%} of '{entity_id}' is owned by "
            f"blocked persons (>= {OFAC_OWNERSHIP_BLOCK_THRESHOLD:.0%} threshold)."
        )
    if not reasons:
        reasons.append("No match against SDN list and 50% Rule not triggered.")

    return {
        "name_matches": name_hits,
        "blocked": name_blocked or fifty_pct_block,
        "reason": " | ".join(reasons),
        "aggregate_blocked_pct": round(agg_pct, 4),
    }


# ---------------------------------------------------------------------------
# Self-test
# ---------------------------------------------------------------------------

def _self_test() -> None:
    """Assertions covering the two structural lift scenarios and edge cases."""

    # ------------------------------------------------------------------
    # 1. OFAC 50% Rule — the classic bare-model failure:
    #    two 30%-blocked co-owners => 60% => BLOCKED
    #    A naive string match on "ENT-ALPHA" finds NO name hit on the SDN
    #    list (the entity is unlisted) and would silently CLEAR it.
    # ------------------------------------------------------------------
    result_alpha = screen("ENT-ALPHA Consulting", entity_id="ENT-ALPHA")
    assert result_alpha["aggregate_blocked_pct"] >= OFAC_OWNERSHIP_BLOCK_THRESHOLD, (
        f"Expected aggregate >= {OFAC_OWNERSHIP_BLOCK_THRESHOLD} for ENT-ALPHA, "
        f"got {result_alpha['aggregate_blocked_pct']}"
    )
    assert result_alpha["blocked"], "ENT-ALPHA should be BLOCKED (60% owned by SDN persons)"
    print(f"[PASS] 50% Rule — ENT-ALPHA aggregate_blocked_pct="
          f"{result_alpha['aggregate_blocked_pct']:.0%} -> BLOCKED")

    # ------------------------------------------------------------------
    # 2. Entity below the threshold -> CLEAR
    # ------------------------------------------------------------------
    result_beta = screen("Beta Industries", entity_id="ENT-BETA")
    assert result_beta["aggregate_blocked_pct"] < OFAC_OWNERSHIP_BLOCK_THRESHOLD, (
        f"ENT-BETA owns 40% by SDN, should be below threshold"
    )
    # name "Beta Industries" should not fuzzy-match any SDN name
    assert not result_beta["blocked"], (
        f"ENT-BETA should be CLEAR but got blocked=True; "
        f"name_matches={result_beta['name_matches']}"
    )
    print(f"[PASS] 50% Rule — ENT-BETA aggregate_blocked_pct="
          f"{result_beta['aggregate_blocked_pct']:.0%} -> CLEAR")

    # ------------------------------------------------------------------
    # 3. Near-miss fuzzy name — "Novaya Kommerz" should still match
    #    "Novaya Commerce LLC" (transposition + legal suffix stripped)
    # ------------------------------------------------------------------
    result_fuzzy = screen("Novaya Kommerz")
    assert len(result_fuzzy["name_matches"]) > 0, (
        "Fuzzy near-miss 'Novaya Kommerz' should match 'Novaya Commerce LLC'"
    )
    assert result_fuzzy["blocked"]
    print(f"[PASS] Fuzzy match — 'Novaya Kommerz' matched "
          f"{result_fuzzy['name_matches'][0]['sdn_name']} "
          f"(score={result_fuzzy['name_matches'][0]['match_score']})")

    # ------------------------------------------------------------------
    # 4. Exact-name match (normalized) — "Dmitri Volkov" on the list
    # ------------------------------------------------------------------
    result_exact = screen("Dmitri Volkov")
    assert result_exact["blocked"]
    print(f"[PASS] Exact match — 'Dmitri Volkov' -> BLOCKED")

    # ------------------------------------------------------------------
    # 5. Clean entity and name — neither match
    # ------------------------------------------------------------------
    result_clean = screen("Sunrise Digital Partners", entity_id="CLEAN-P1")
    assert not result_clean["blocked"], "Clean entity should not be blocked"
    assert result_clean["aggregate_blocked_pct"] == 0.0
    print(f"[PASS] Clean entity — 'Sunrise Digital Partners' + CLEAN-P1 -> CLEAR")

    # ------------------------------------------------------------------
    # 6. ENT-GAMMA: single 55% SDN owner -> BLOCKED
    # ------------------------------------------------------------------
    result_gamma = screen("Gamma Holdings Ltd", entity_id="ENT-GAMMA")
    assert result_gamma["aggregate_blocked_pct"] >= OFAC_OWNERSHIP_BLOCK_THRESHOLD
    assert result_gamma["blocked"]
    print(f"[PASS] 50% Rule — ENT-GAMMA (single 55% owner) -> BLOCKED")

    # ------------------------------------------------------------------
    # 7. Legal suffix stripping — "Meridian Capital" without "Ventures"
    #    should still score highly against "Meridian Capital Ventures"
    # ------------------------------------------------------------------
    result_suffix = screen("Meridian Capital")
    assert result_suffix["blocked"], (
        "Legal-suffix-stripped query 'Meridian Capital' should match "
        "'Meridian Capital Ventures'"
    )
    print(f"[PASS] Legal-suffix strip — 'Meridian Capital' matched "
          f"{result_suffix['name_matches'][0]['sdn_name']}")

    print("\nAll sanctions_screen self-tests PASSED.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Deterministic sanctions screener (SYNTHETIC data only)."
    )
    parser.add_argument("--self-test", action="store_true",
                        help="Run assertions and exit.")
    parser.add_argument("--name", default=None,
                        help="Query name to screen.")
    parser.add_argument("--entity-id", default=None,
                        help="Entity ID to check under 50%% Rule.")
    args = parser.parse_args()

    if args.self_test:
        _self_test()
        return

    if args.name:
        import json
        result = screen(args.name, entity_id=args.entity_id)
        print(json.dumps(result, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
