#!/usr/bin/env python3
"""scripts.certification_campaign — Certification Campaign V1: turn candidate primitives into CERTIFIED
(oracle+security+determinism-gated) primitives, ranked by ADDRESSABILITY LIFT (candidate-only until certified).

Owner (2026-07-09): kick off certification NOW, in parallel with the multi-tier waiter. The 50k projection says
the bottleneck is addressable_rate (47%), not proof-of-mechanism — so certify primitives that raise addressability
fastest. Optimize certified-addressability-lift, not raw count. Five lanes; priority-ranked; multi-tier-aware
(reranks when the leaderboard lands).

Certification pipeline per candidate (reuses the real gates): security scan (no banned calls) -> isolated sandbox
vs its ORACLE fixtures (python -I -S) -> determinism (identical twice) -> CERTIFIED + receipt, else FAILED + reason.
Priority = expected_frequency x expected_token_weight x max(bare_failure_rate,0.01) x oracle_available x
route_composition_value / certification_cost. Lane 2 (high-frequency scalars) is prioritized because it lifts
addressability across every scenario. candidate=true/serves_truth=false until certified; no code runs before the
security gate.

    python3 scripts/certification_campaign.py --self-test
    python3 scripts/certification_campaign.py --run
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/ml_lifecycle_primitive_minter.py) ────────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import inspect  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
from typing import Any, Callable  # noqa: E402

from scripts.esoteric_platform_primitive_pack import _PRIMITIVES as _PRIMS_1  # noqa: E402
from scripts.esoteric_platform_primitive_pack_2 import _PRIMITIVES as _PRIMS_2  # noqa: E402
from scripts.programming_primitives_pack import _PRIMITIVES as _PRIMS_PROG  # noqa: E402
from scripts.primitive_token_savings_ab import security_scan, sandbox_run  # noqa: E402  REUSE the real gates

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
BENCHMARK_KIND = "real"  # no_proxy_gate: real=executed+measured / proxy=estimated
ARTIFACT_DIR_REL = "data/dev-intel/certification"

LANES: dict[str, dict[str, Any]] = {
    "deterministic_protocol": {"rank": 1, "desc": "encoding/checksum/identifier/legacy formats — high failure",
                               "bare_failure_rate": 0.5, "route_value": 1.1, "cost": 1.0},
    "data_cleaning_scalars": {"rank": 2, "desc": "money/date/units/email/phone — HIGH FREQUENCY, broad addressability",
                              "bare_failure_rate": 0.3, "route_value": 1.4, "cost": 0.8},
    "document_validators": {"rank": 3, "desc": "invoice totals / required fields / lookups", "bare_failure_rate": 0.4,
                            "route_value": 1.2, "cost": 1.2},
    "route_composition_bridges": {"rank": 4, "desc": "schema/enum/unit/port bridges — cut residual glue tokens",
                                  "bare_failure_rate": 0.25, "route_value": 2.0, "cost": 1.3},
    "high_density_scenario_families": {"rank": 5, "desc": "api_integration/micro_saas first (highest factor)",
                                       "bare_failure_rate": 0.35, "route_value": 1.3, "cost": 1.0},
    "programming_utilities": {"rank": 2, "desc": "everyday string/list/dict/math/algorithm dev utilities — the "
                              "HIGHEST-FREQUENCY, broadest-addressability lane", "bare_failure_rate": 0.2,
                              "route_value": 1.5, "cost": 0.7},
}


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
# Lane 2 — high-frequency data-cleaning SCALAR primitives (the biggest addressability lever). Each self-contained.
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════

def parse_money_to_float(text: str) -> float:
    """Data-cleaning: parse a money string to a float; accounting parentheses = negative. '$1,234.56'->1234.56."""
    import re
    neg = "(" in text and ")" in text
    cleaned = re.sub(r"[^0-9.]", "", text)
    val = float(cleaned) if cleaned else 0.0
    return -val if neg else val


def normalize_currency_symbol(symbol: str) -> str:
    """Data-cleaning: currency symbol -> ISO 4217 code."""
    return {"$": "USD", "US$": "USD", "€": "EUR", "£": "GBP", "¥": "JPY", "₹": "INR",
            "₩": "KRW", "R$": "BRL", "CHF": "CHF", "A$": "AUD", "C$": "CAD"}.get(symbol.strip(), "UNKNOWN")


def parse_percent_to_fraction(text: str) -> float:
    """Data-cleaning: '12.5%' -> 0.125."""
    return float(text.strip().rstrip("%")) / 100.0


def parse_basis_points(text: str) -> float:
    """Finance data-cleaning: '50bps' / '50 bps' -> 0.005 (bps/10000)."""
    import re
    return float(re.sub(r"(?i)\s*bps?", "", text).strip()) / 10000.0


def parse_iso8601_date(text: str) -> list:
    """Data-cleaning: 'YYYY-MM-DD' -> [year, month, day] ints."""
    y, m, d = text.strip().split("-")
    return [int(y), int(m), int(d)]


def normalize_us_zip(text: str) -> str:
    """Data-cleaning: ZIP+4 or padded -> 5-digit ZIP. '12345-6789'->'12345'."""
    return text.strip().split("-")[0].strip()[:5]


def validate_email_basic(text: str) -> bool:
    """Data-cleaning: basic RFC-ish email shape check."""
    import re
    return bool(re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", text.strip()))


def normalize_phone_e164_us(text: str) -> str:
    """Data-cleaning: US phone -> E.164. '(716) 555-1234' -> '+17165551234'."""
    import re
    d = re.sub(r"\D", "", text)
    if len(d) == 10:
        return "+1" + d
    if len(d) == 11 and d[0] == "1":
        return "+" + d
    return "+" + d


def company_legal_suffix(text: str) -> str:
    """Entity data-cleaning: extract + normalize the legal suffix. 'Acme, Inc.' -> 'INC'; none -> ''."""
    import re
    m = re.search(r"\b(inc|incorporated|llc|l\.l\.c|ltd|limited|corp|corporation|co|plc|gmbh|llp|lp)\b",
                  text, re.IGNORECASE)
    if not m:
        return ""
    canon = {"incorporated": "INC", "l.l.c": "LLC", "limited": "LTD", "corporation": "CORP"}
    return canon.get(m.group(1).lower(), m.group(1).upper())


def slugify(text: str) -> str:
    """Data-cleaning: 'Hello, World!' -> 'hello-world'."""
    import re
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


def collapse_whitespace(text: str) -> str:
    """Data-cleaning: collapse all runs of whitespace to single spaces + trim."""
    return " ".join(text.split())


def titlecase_person_name(text: str) -> str:
    """Data-cleaning: 'john  q. SMITH' -> 'John Q. Smith'."""
    return " ".join(w[:1].upper() + w[1:].lower() for w in text.split())


def hms_to_seconds(text: str) -> int:
    """Data-cleaning: 'H:M:S' or 'M:S' clock string -> total seconds."""
    parts = [int(p) for p in text.strip().split(":")]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    return parts[0]


def detect_trust_entity(text: str) -> bool:
    """Entity data-cleaning: is this party name a trust/estate?"""
    import re
    return bool(re.search(r"(?i)\b(trust|revocable|irrevocable|living trust|estate of|as trustee|u/?a/?d)\b", text))


_LANE2: list[dict[str, Any]] = [
    {"fn": parse_money_to_float, "freq": 9, "tok": 5, "fixtures": [(("$1,234.56",), 1234.56), (("1000",), 1000.0),
                                                                   (("($99.00)",), -99.0), (("$0.99",), 0.99)]},
    {"fn": normalize_currency_symbol, "freq": 6, "tok": 3, "fixtures": [(("$",), "USD"), (("€",), "EUR"),
                                                                        (("£",), "GBP"), (("¥",), "JPY")]},
    {"fn": parse_percent_to_fraction, "freq": 7, "tok": 3, "fixtures": [(("12.5%",), 0.125), (("100%",), 1.0),
                                                                        (("0.5%",), 0.005)]},
    {"fn": parse_basis_points, "freq": 4, "tok": 3, "fixtures": [(("50bps",), 0.005), (("50 bps",), 0.005),
                                                                 (("125 bp",), 0.0125)]},
    {"fn": parse_iso8601_date, "freq": 9, "tok": 4, "fixtures": [(("2026-07-09",), [2026, 7, 9]),
                                                                 (("2000-01-01",), [2000, 1, 1])]},
    {"fn": normalize_us_zip, "freq": 8, "tok": 3, "fixtures": [(("12345-6789",), "12345"), ((" 90210 ",), "90210"),
                                                              (("00501",), "00501")]},
    {"fn": validate_email_basic, "freq": 9, "tok": 4, "fixtures": [(("a@b.com",), True), (("bad",), False),
                                                                   (("x@y",), False), (("j.doe@sub.co.uk",), True)]},
    {"fn": normalize_phone_e164_us, "freq": 8, "tok": 5, "fixtures": [(("(716) 555-1234",), "+17165551234"),
                                                                      (("1-716-555-1234",), "+17165551234")]},
    {"fn": company_legal_suffix, "freq": 7, "tok": 4, "fixtures": [(("Acme, Inc.",), "INC"), (("Beta LLC",), "LLC"),
                                                                   (("Gamma Corporation",), "CORP"),
                                                                   (("Just A Name",), "")]},
    {"fn": slugify, "freq": 8, "tok": 4, "fixtures": [(("Hello, World!",), "hello-world"),
                                                      (("  Multi   Space  ",), "multi-space")]},
    {"fn": collapse_whitespace, "freq": 9, "tok": 3, "fixtures": [(("  a   b ",), "a b"), (("x\t\ny",), "x y")]},
    {"fn": titlecase_person_name, "freq": 7, "tok": 4, "fixtures": [(("john  SMITH",), "John Smith"),
                                                                    (("q. public",), "Q. Public")]},
    {"fn": hms_to_seconds, "freq": 5, "tok": 4, "fixtures": [(("1:30:00",), 5400), (("2:30",), 150), (("0:0:5",), 5)]},
    {"fn": detect_trust_entity, "freq": 6, "tok": 4, "fixtures": [(("The Smith Family Living Trust",), True),
                                                                  (("John Q. Public",), False),
                                                                  (("Estate of Jane Doe",), True)]},
]


def _candidates() -> list[dict[str, Any]]:
    """The certification queue: Lane 1 (28 esoteric protocol) + Lane 2 (14 high-frequency scalars)."""
    cands: list[dict[str, Any]] = []
    for spec in list(_PRIMS_1) + list(_PRIMS_2):
        cands.append({"name": spec["fn"].__name__, "fn": spec["fn"], "fixtures": spec["fixtures"],
                      "lane": "deterministic_protocol", "freq": 4, "tok": 6})
    for spec in _LANE2:
        cands.append({"name": spec["fn"].__name__, "fn": spec["fn"], "fixtures": spec["fixtures"],
                      "lane": "data_cleaning_scalars", "freq": spec["freq"], "tok": spec["tok"]})
    for spec in _PRIMS_PROG:  # everyday programming/development utilities (highest frequency)
        cands.append({"name": spec["fn"].__name__, "fn": spec["fn"], "fixtures": spec["fixtures"],
                      "lane": "programming_utilities", "freq": 9, "tok": 5})
    return cands


def priority_score(cand: dict[str, Any]) -> float:
    lane = LANES[cand["lane"]]
    bare_fail = cand.get("multi_tier_failure_rate", lane["bare_failure_rate"])  # tier-aware when the leaderboard lands
    return round(cand["freq"] * cand["tok"] * max(bare_fail, 0.01) * 1.0 * lane["route_value"] / lane["cost"], 3)


def certify(cand: dict[str, Any]) -> dict[str, Any]:
    """Real certification: security scan -> sandbox vs oracle -> determinism. Returns a receipt (certified or why)."""
    fn: Callable = cand["fn"]
    body = inspect.getsource(fn)
    banned = security_scan(body)
    if banned:
        return {"name": cand["name"], "lane": cand["lane"], "certified": False, "stage_failed": "security",
                "reason": f"banned:{banned}", **BOUNDARY}
    r1 = sandbox_run(body, fn.__name__, cand["fixtures"])
    oracle_ok = r1["ran"] and r1["n_total"] > 0 and r1["n_pass"] == r1["n_total"]
    if not oracle_ok:
        return {"name": cand["name"], "lane": cand["lane"], "certified": False, "stage_failed": "oracle",
                "reason": r1.get("error") or f"{r1['n_pass']}/{r1['n_total']}", **BOUNDARY}
    r2 = sandbox_run(body, fn.__name__, cand["fixtures"])
    if (r2["n_pass"], r2["n_total"]) != (r1["n_pass"], r1["n_total"]):
        return {"name": cand["name"], "lane": cand["lane"], "certified": False, "stage_failed": "determinism",
                "reason": "non_deterministic", **BOUNDARY}
    return {"name": cand["name"], "lane": cand["lane"], "certified": True,
            "receipts": ["security", "oracle", "determinism"], "n_fixtures": r1["n_total"],
            "priority_score": priority_score(cand), "lifecycle": "certified", **BOUNDARY}


def run_campaign() -> dict[str, Any]:
    cands = sorted(_candidates(), key=lambda c: -priority_score(c))
    receipts = [certify(c) for c in cands]
    certified = [r for r in receipts if r["certified"]]
    by_lane: dict[str, dict[str, int]] = {}
    for r in receipts:
        acc = by_lane.setdefault(r["lane"], {"attempted": 0, "certified": 0})
        acc["attempted"] += 1
        acc["certified"] += 1 if r["certified"] else 0
    queue = [{"name": c["name"], "lane": c["lane"], "priority_score": priority_score(c),
              "multi_tier_failure_rate": c.get("multi_tier_failure_rate")} for c in cands]
    return {"record_type": "certification_campaign_v1", "attempted": len(cands), "certified": len(certified),
            "certification_yield": round(len(certified) / len(cands), 3) if cands else 0.0,
            "by_lane": by_lane, "certified_names": sorted(r["name"] for r in certified),
            "failures": [r for r in receipts if not r["certified"]],
            "priority_queue": queue[:20],
            "multi_tier_aware": "reranks when the multi-tier A/B leaderboard lands (bare_failure_rate -> per-tier)",
            "executive_metric": "certified_addressability_lift_per_day", **BOUNDARY}


def emit(result: dict[str, Any]) -> str:
    out_dir = resource(ARTIFACT_DIR_REL)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "certification_campaign_v1_receipt.json").write_text(json.dumps(result, indent=2, sort_keys=True),
                                                                    encoding="utf-8")
    with (out_dir / "certification_queue.jsonl").open("w", encoding="utf-8") as f:
        for row in result["priority_queue"]:
            f.write(json.dumps(row) + "\n")
    return str(out_dir)


def self_test() -> bool:
    """Mutation-gated: real gates certify correct primitives + REJECT broken/dangerous ones; priority ranks
    scalars (high freq) up; receipts are candidate-until-certified."""
    # (1) a correct Lane-2 scalar certifies through all real gates.
    good = next(c for c in _candidates() if c["name"] == "parse_money_to_float")
    rc = certify(good)
    assert rc["certified"] and rc["receipts"] == ["security", "oracle", "determinism"], f"good must certify: {rc}"

    # (2) a WRONG oracle fixture fails certification (the gate really tests).
    bad = dict(good, fixtures=[(("$100",), 999.0)])
    assert certify(bad)["certified"] is False and certify(bad)["stage_failed"] == "oracle"

    # (3) a dangerous body is rejected at the security stage (no execution before the gate).
    def _evil(x):  # noqa: ANN001
        import os  # noqa: F401
        return os.getcwd()
    assert certify({"name": "evil", "fn": _evil, "fixtures": [((1,), 1)], "lane": "data_cleaning_scalars",
                    "freq": 1, "tok": 1})["stage_failed"] == "security"

    # (4) the full campaign certifies the real batch; Lane 2 present; yield reported.
    res = run_campaign()
    assert res["attempted"] >= 40, f"expected >=40 candidates (28 protocol + 14 scalar), got {res['attempted']}"
    assert res["certified"] == res["attempted"], (f"all real oracle-backed candidates must certify (self-contained "
                                                  f"executor bodies), got {res['certified']}/{res['attempted']}: "
                                                  f"{[f['name'] for f in res['failures']]}")
    assert res["by_lane"]["data_cleaning_scalars"]["certified"] >= 14, "Lane-2 scalars must certify"

    # (5) priority ranks high-frequency scalars above low-freq protocol (addressability-first).
    q = res["priority_queue"]
    top_lanes = [row["lane"] for row in q[:8]]
    assert top_lanes.count("data_cleaning_scalars") >= 4, "high-frequency scalars should dominate the top of the queue"

    # (6) candidate-only receipts.
    assert res["candidate"] is True and res["serves_truth"] is False

    print(f"OK certification_campaign self-test: {res['attempted']} candidates -> {res['certified']} CERTIFIED "
          f"(yield {res['certification_yield']}); Lane2 scalars {res['by_lane']['data_cleaning_scalars']['certified']} "
          f"certified; broken+dangerous rejected; priority = addressability-first; serves_truth=false")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="Certification Campaign V1 (oracle+security+determinism gated).")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if args.run:
        res = run_campaign()
        res["path"] = emit(res)
        print(json.dumps({k: res[k] for k in ("attempted", "certified", "certification_yield", "by_lane",
                                              "priority_queue", "executive_metric", "path")}, indent=2))
        return
    self_test()


if __name__ == "__main__":
    main()
