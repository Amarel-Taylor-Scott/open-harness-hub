"""check_provider_arbitrage — proof for _repos/teleon/backend/src/teleon/economics/provider_arbitrage.py (backs registry #63).

Cross-provider price arbitrage for the SAME model: cheapest vs dearest provider, the spread = the savings.
Verifies the math on a fixture (deterministic) AND that it runs clean against the real model_index.json.

Deterministic, offline, stdlib only.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = next((_ar for _ar in Path(__file__).resolve().parents if (_ar / ".aidoneright-root").exists()), Path(__file__).resolve().parents[1])
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.teleon.economics.provider_arbitrage import all_arbitrage, arbitrage_for_model  # noqa: E402

# Fixture: model m1 served by two providers (blended 4 vs 10 -> 60% spread); m2 single-provider (no arbitrage).
_FIX = [
    {"model_id": "m1", "provider": "pA", "cost_per_mtok_in": 1.0, "cost_per_mtok_out": 3.0},
    {"model_id": "m1", "provider": "pB", "cost_per_mtok_in": 2.0, "cost_per_mtok_out": 8.0},
    {"model_id": "m2", "provider": "pC", "cost_per_mtok_in": 1.0, "cost_per_mtok_out": 1.0},
]
_EXPECTED_SPREAD_PCT = 60.0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--self-test", action="store_true")
    args = ap.parse_args()

    fails: list[str] = []
    checks = 0

    def ck(name: str, ok: bool, detail: str = "") -> None:
        nonlocal checks
        checks += 1
        if not ok:
            fails.append(f"{name}{(': ' + detail) if detail else ''}")
        if args.self_test and not ok:
            print(f"  [XX] {name}{(' — ' + detail) if detail else ''}")

    m1 = arbitrage_for_model("m1", _FIX)
    ck("m1 has arbitrage (2 providers)", m1.get("arbitrage") is True, str(m1.get("n_providers")))
    ck("m1 cheapest provider is pA", m1.get("cheapest", {}).get("provider") == "pA", str(m1.get("cheapest")))
    ck("m1 dearest provider is pB", m1.get("dearest", {}).get("provider") == "pB")
    ck("m1 spread == 60.0%", m1.get("spread_pct") == _EXPECTED_SPREAD_PCT, str(m1.get("spread_pct")))

    m2 = arbitrage_for_model("m2", _FIX)
    ck("m2 single provider -> no arbitrage", m2.get("arbitrage") is False)

    absent = arbitrage_for_model("does_not_exist", _FIX)
    ck("absent model -> available False (honest)", absent.get("available") is False)

    ranked = all_arbitrage(_FIX)
    ck("all_arbitrage returns only the arbitrage model", [a["model_id"] for a in ranked] == ["m1"], str(ranked))

    # runs clean against the REAL registry (may legitimately be empty if no model is multi-provider)
    real = all_arbitrage()
    ck("runs clean on real model_index (list)", isinstance(real, list))

    if fails:
        print(f"\nFAIL - check_provider_arbitrage: {len(fails)} of {checks} assertions failed")
        for f in fails:
            print(f"  - {f}")
        return 1
    print(f"PASS - check_provider_arbitrage: cheapest/dearest spread math verified on fixture (60.0%), honest on "
          f"single-provider + absent, runs clean on real model_index ({len(real)} multi-provider model(s)); "
          f"{checks} assertions; serves_truth=false.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
