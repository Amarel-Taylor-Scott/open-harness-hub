#!/usr/bin/env python3
"""Extrapolate rollout savings: primitive-search harness across N developers.

Owner question 2026-07-01: if all the primitives + the tool were rolled out to
10,000 developers, what are the savings in tokens, spend, electricity, water
(and CO2)?

This is a TRANSPARENT, SOURCED estimate with explicit low/central/high bands —
NOT a precise claim. Every constant is named with its basis so you can challenge
any input. Output is candidate=true / serves_truth=false (evidence, not truth).

Model (honest, avoids the 486x best-case trap):
  A coding agent's tokens are mostly CONTEXT (file/doc reads). Primitives don't
  compress ALL work — only the reuse-eligible context slice, but they compress
  THAT slice massively (486x measured at M0, so ~100% of that slice's tokens).
  So:
     effective_total_reduction = context_share * reuse_eligible_share
  which lands ~30-55% of TOTAL tokens, NOT 486x of everything. The 486x is the
  compression on the compressible slice; the blended rollout number is smaller
  and that honesty is the point.

Chain: tokens_saved -> $ (pricing) -> kWh (energy/token) -> liters (water/kWh)
       -> kg CO2 (grid intensity).

If the developer A/B simulation has produced an aggregate effective reduction,
pass it via --effective-reduction to replace the default central estimate.

Usage:
  python3 _repos/shared-backend-components/scripts/extrapolate_rollout_savings.py --developers 10000
  python3 _repos/shared-backend-components/scripts/extrapolate_rollout_savings.py --self-test
"""
from __future__ import annotations
from scripts._repo_paths import resource as _resource

import argparse
import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

if __package__ is None or __package__ == "":
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from scripts._config import REPO_ROOT  # noqa: E402

OUT_DIR = _resource("data/dev-intel/rollout_savings")

# ── Named, sourced constants (low / central / high). Challenge any of these. ──
# Tokens a heavy AI-coding developer consumes per working day (agentic tools read
# whole files/repos/docs; input dominates). Basis: agent-trace token reports for
# Cursor/Claude Code/Devin-class tools; wide variance -> wide band.
TOKENS_PER_DEV_PER_DAY = {"low": 300_000, "central": 1_000_000, "high": 3_000_000}
WORKING_DAYS_PER_YEAR = 230  # basis: ~46 weeks x 5 days

# Effective TOTAL-token reduction from the primitive-search harness (blended over a
# real mixed workload). = context_share (~0.70; basis: REPOFORMER/file-read share
# 67.5-76.1% of coding-agent tokens) x reuse_eligible_share (~0.40-0.80 of that is
# recurring reuse-eligible work). NOT the 486x best-case slice compression.
EFFECTIVE_REDUCTION = {"low": 0.28, "central": 0.45, "high": 0.60}

# $ per 1M tokens, blended input+output for an agentic coding model.
# Basis: mid-tier coding model pricing (input ~$0.5-3, output ~$2-15/1M), agentic
# mix is input-heavy.
USD_PER_1M_TOKENS = {"low": 1.0, "central": 3.0, "high": 6.0}

# Energy per 1M tokens (kWh). Basis: large-model inference ~0.5-3 J/token; typical
# response energy cited ~0.3 Wh. 1 J/token = 0.278 kWh/1M tokens.
KWH_PER_1M_TOKENS = {"low": 0.20, "central": 0.45, "high": 1.10}

# Water per kWh (liters), datacenter combined on-site cooling + off-site power-gen.
# Basis: reported WUE ~0.5-1.8 L/kWh on-site; power generation adds more; combined
# often cited ~1.8-3.8 L/kWh.
LITERS_PER_KWH = {"low": 0.5, "central": 1.8, "high": 3.8}

# Grid carbon intensity (kg CO2 per kWh). Basis: global avg ~0.4; clean grids lower.
KG_CO2_PER_KWH = {"low": 0.20, "central": 0.40, "high": 0.60}

BANDS = ("low", "central", "high")


def _today() -> str:
    return dt.datetime.now(dt.timezone.utc).date().isoformat()


def _band_pick(const: dict[str, float], band: str) -> float:
    return float(const[band])


def compute(developers: int, effective_override: float | None = None) -> dict[str, Any]:
    """Compute annual savings for each band. For low/high we compose the
    conservative/aggressive ends so the band is a genuine envelope, not a point."""
    results: dict[str, Any] = {}
    for band in BANDS:
        tokens_day = _band_pick(TOKENS_PER_DEV_PER_DAY, band)
        reduction = effective_override if effective_override is not None else _band_pick(EFFECTIVE_REDUCTION, band)
        usd_1m = _band_pick(USD_PER_1M_TOKENS, band)
        kwh_1m = _band_pick(KWH_PER_1M_TOKENS, band)
        l_kwh = _band_pick(LITERS_PER_KWH, band)
        co2_kwh = _band_pick(KG_CO2_PER_KWH, band)

        total_tokens_year = tokens_day * WORKING_DAYS_PER_YEAR * developers
        tokens_saved_year = total_tokens_year * reduction
        m_tokens_saved = tokens_saved_year / 1_000_000

        usd_saved = m_tokens_saved * usd_1m
        kwh_saved = m_tokens_saved * kwh_1m
        liters_saved = kwh_saved * l_kwh
        co2_saved_kg = kwh_saved * co2_kwh

        results[band] = {
            "tokens_per_dev_per_day": int(tokens_day),
            "effective_reduction": round(reduction, 4),
            "total_tokens_year": int(total_tokens_year),
            "tokens_saved_year": int(tokens_saved_year),
            "usd_saved_year": round(usd_saved, 2),
            "kwh_saved_year": round(kwh_saved, 1),
            "liters_water_saved_year": round(liters_saved, 1),
            "co2_kg_saved_year": round(co2_saved_kg, 1),
        }
    return results


def _fmt(n: float) -> str:
    for unit, div in (("B", 1e9), ("M", 1e6), ("K", 1e3)):
        if abs(n) >= div:
            return f"{n / div:.2f}{unit}"
    return f"{n:.0f}"


def render(developers: int, res: dict[str, Any], effective_override: float | None) -> str:
    c = res["central"]
    L, H = res["low"], res["high"]
    lines: list[str] = []
    lines.append(f"# Rollout savings — {developers:,} developers on the primitive-search harness")
    lines.append("")
    lines.append("> Transparent SOURCED estimate with low/central/high bands. candidate=true / "
                 "serves_truth=false — evidence, not a precise claim. Challenge any input constant.")
    if effective_override is not None:
        lines.append(f"> effective token reduction pinned to {effective_override:.0%} "
                     "(from the developer A/B simulation aggregate).")
    lines.append("")
    lines.append("## Central estimate (per YEAR)")
    lines.append(f"- Tokens saved: **{_fmt(c['tokens_saved_year'])}** "
                 f"(of {_fmt(c['total_tokens_year'])} consumed; {c['effective_reduction']:.0%} blended reduction)")
    lines.append(f"- Spend saved: **${_fmt(c['usd_saved_year'])}**")
    lines.append(f"- Electricity saved: **{_fmt(c['kwh_saved_year'])} kWh** "
                 f"(~{c['kwh_saved_year'] / 8766 * 1000:.0f} avg continuous watts)")
    lines.append(f"- Water saved: **{_fmt(c['liters_water_saved_year'])} liters**")
    lines.append(f"- CO2 avoided: **{_fmt(c['co2_kg_saved_year'])} kg**")
    lines.append("")
    lines.append("## Band envelope (per year)")
    lines.append("| metric | low | central | high |")
    lines.append("|---|---:|---:|---:|")
    lines.append(f"| tokens saved | {_fmt(L['tokens_saved_year'])} | {_fmt(c['tokens_saved_year'])} | {_fmt(H['tokens_saved_year'])} |")
    lines.append(f"| $ saved | ${_fmt(L['usd_saved_year'])} | ${_fmt(c['usd_saved_year'])} | ${_fmt(H['usd_saved_year'])} |")
    lines.append(f"| kWh saved | {_fmt(L['kwh_saved_year'])} | {_fmt(c['kwh_saved_year'])} | {_fmt(H['kwh_saved_year'])} |")
    lines.append(f"| liters water | {_fmt(L['liters_water_saved_year'])} | {_fmt(c['liters_water_saved_year'])} | {_fmt(H['liters_water_saved_year'])} |")
    lines.append(f"| kg CO2 | {_fmt(L['co2_kg_saved_year'])} | {_fmt(c['co2_kg_saved_year'])} | {_fmt(H['co2_kg_saved_year'])} |")
    lines.append("")
    lines.append("## Per-developer-per-year (central)")
    lines.append(f"- ${c['usd_saved_year'] / developers:.0f} · {c['kwh_saved_year'] / developers:.0f} kWh · "
                 f"{c['liters_water_saved_year'] / developers:.0f} L water · {c['co2_kg_saved_year'] / developers:.0f} kg CO2")
    lines.append("")
    lines.append("## Basis (challenge these)")
    lines.append(f"- tokens/dev/day: {TOKENS_PER_DEV_PER_DAY} (agentic tools read whole repos)")
    lines.append(f"- effective reduction: {EFFECTIVE_REDUCTION} = context_share ~0.70 (REPOFORMER file-read share 67.5-76.1%) x reuse-eligible ~0.4-0.8; the 486x is slice compression, NOT this blended number")
    lines.append(f"- $/1M tokens: {USD_PER_1M_TOKENS} · kWh/1M tokens: {KWH_PER_1M_TOKENS} (~0.5-3 J/token) · L/kWh: {LITERS_PER_KWH} (datacenter WUE) · kgCO2/kWh: {KG_CO2_PER_KWH}")
    lines.append(f"- working days/year: {WORKING_DAYS_PER_YEAR}")
    lines.append("")
    lines.append("The single biggest uncertainty is `effective_reduction` — replace the estimate with the "
                 "developer A/B simulation aggregate (per industry/complexity) for a grounded number, and the "
                 "deterministic lift benchmark (486x) bounds the compressible slice.")
    return "\n".join(lines)


def run(developers: int, effective_override: float | None) -> dict[str, Any]:
    res = compute(developers, effective_override)
    md = render(developers, res, effective_override)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    payload = {
        "record_type": "rollout_savings_extrapolation",
        "generated_utc": _today(),
        "developers": developers,
        "effective_reduction_override": effective_override,
        "bands": res,
        "constants": {
            "tokens_per_dev_per_day": TOKENS_PER_DEV_PER_DAY,
            "working_days_per_year": WORKING_DAYS_PER_YEAR,
            "effective_reduction": EFFECTIVE_REDUCTION,
            "usd_per_1m_tokens": USD_PER_1M_TOKENS,
            "kwh_per_1m_tokens": KWH_PER_1M_TOKENS,
            "liters_per_kwh": LITERS_PER_KWH,
            "kg_co2_per_kwh": KG_CO2_PER_KWH,
        },
        "candidate": True,
        "serves_truth": False,
    }
    (OUT_DIR / f"rollout_{developers}_devs.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (OUT_DIR / f"rollout_{developers}_devs.md").write_text(md + "\n", encoding="utf-8")
    return payload


def self_test() -> int:
    res = compute(10_000)
    c = res["central"]
    # Sanity: monotonic bands (high >= central >= low on tokens saved).
    assert res["high"]["tokens_saved_year"] >= c["tokens_saved_year"] >= res["low"]["tokens_saved_year"]
    # Chain integrity: liters = kwh * L/kWh (central).
    expected_liters = c["kwh_saved_year"] * LITERS_PER_KWH["central"]
    assert abs(c["liters_water_saved_year"] - round(expected_liters, 1)) < 1.0, "water chain broke"
    # Cost chain: $ = (tokens/1e6) * $/1M.
    expected_usd = c["tokens_saved_year"] / 1_000_000 * USD_PER_1M_TOKENS["central"]
    assert abs(c["usd_saved_year"] - round(expected_usd, 2)) < 1.0, "cost chain broke"
    # Override replaces the reduction.
    ov = compute(10_000, effective_override=0.50)
    assert ov["central"]["effective_reduction"] == 0.5
    # Reduction never exceeds 1 (can't save more than 100%).
    for b in BANDS:
        assert 0 < res[b]["effective_reduction"] < 1
    # 10k-dev central annual tokens saved is positive and large.
    assert c["tokens_saved_year"] > 0
    # Render works and labels honesty.
    md = render(10_000, res, None)
    assert "serves_truth=false" in md and "486x" in md and "challenge these" in md.lower()
    # Constant bands are ordered low<=central<=high for every constant.
    for name, const in (("tokens", TOKENS_PER_DEV_PER_DAY), ("reduction", EFFECTIVE_REDUCTION),
                        ("usd", USD_PER_1M_TOKENS), ("kwh", KWH_PER_1M_TOKENS),
                        ("water", LITERS_PER_KWH), ("co2", KG_CO2_PER_KWH)):
        assert const["low"] <= const["central"] <= const["high"], f"{name} band unordered"
    print("OK: rollout savings extrapolation self-test passed (chain integrity, bands, override, honesty labels).")
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--developers", type=int, default=10_000)
    parser.add_argument("--effective-reduction", type=float, default=None,
                        help="override blended token reduction (e.g. from the A/B simulation aggregate)")
    parser.add_argument("--self-test", action="store_true")
    args = parser.parse_args(argv)
    if args.self_test:
        return self_test()
    payload = run(args.developers, args.effective_reduction)
    c = payload["bands"]["central"]
    print(f"wrote {OUT_DIR}/rollout_{args.developers}_devs.md — central/yr: "
          f"{_fmt(c['tokens_saved_year'])} tokens, ${_fmt(c['usd_saved_year'])}, "
          f"{_fmt(c['kwh_saved_year'])} kWh, {_fmt(c['liters_water_saved_year'])} L water, "
          f"{_fmt(c['co2_kg_saved_year'])} kg CO2.")
    return self_test()


if __name__ == "__main__":
    raise SystemExit(main())
