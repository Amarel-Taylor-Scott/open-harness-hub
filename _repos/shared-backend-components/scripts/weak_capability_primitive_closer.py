#!/usr/bin/env python3
"""scripts.weak_capability_primitive_closer — aim the real Hy3 executor-synthesizer at the MEASURED low-capability
areas and produce WORKING, fixture-proven primitives for them (not just candidate cards).

The `minted_lift` receipt measured the registry's weakest capabilities at 0.0 hit-rate:
accessible-components · achievements/badges · guided-product-tour · infrastructure-as-code ·
realtime-collaborative-editing · response-caching · seo-meta/sitemaps · single-sign-on · timesheet-tracking ·
web-application-firewall-rules. This module DECOMPOSES each weak area into concrete DETERMINISTIC (D0/D1) primitive
specs, then runs every spec through `spec_to_executor_synthesizer.synthesize` — Hy3 drafts the body + golden
fixtures, the security gate + isolated sandbox + determinism check run for real, and only fixture-passing executors
promote candidate→validated→certified. This is "identify low-capability areas → create improved primitives for
them", done for real: the output is executable + proven, candidate/serves_truth=false until the gates promote it.

    python3 scripts/weak_capability_primitive_closer.py --self-test
    python3 scripts/weak_capability_primitive_closer.py --run                 # live Hy3, all weak areas
    python3 scripts/weak_capability_primitive_closer.py --run --capability response_caching
"""
from __future__ import annotations

import sys
from pathlib import Path

_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
from typing import Any, Optional  # noqa: E402

from scripts.spec_to_executor_synthesizer import run as _synth_run, synthesize as _synthesize  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
_DATA_SUBDIR = "data/dev-intel/weak_capability_primitive_closer"


def _spec(name: str, cap: str, intent: str, inp: str, out: str, det: str = "D0_pure") -> dict[str, Any]:
    return {"name": name, "needs_executor": True, "determinism_level": det, "capability": cap, "intent": intent,
            "input_schema": {"in": inp}, "output_schema": {"out": out},
            "edges": {"input_edge": inp, "output_edge": out}}


# ── the decomposition: each MEASURED-weak capability → concrete deterministic, fixture-provable primitives ──────
WEAK_CAPABILITY_SPECS: list[dict[str, Any]] = [
    # response caching
    _spec("cache_key_from_request", "response_caching",
          "Build a stable cache key from method + path + sorted query string + vary headers.", "RequestParts", "CacheKey"),
    _spec("compute_ttl_seconds", "response_caching",
          "Parse a Cache-Control header and return the effective max-age TTL in seconds (0 if no-store).", "CacheControlHeader", "Seconds"),
    _spec("cache_is_fresh", "response_caching", "Return True iff age_seconds < ttl_seconds.", "AgeTtl", "Boolean"),
    _spec("weak_etag_for_body", "response_caching", "Compute a deterministic weak ETag (W/\"<len>-<crc>\") for a body string.", "Body", "ETag"),
    # seo meta + sitemaps
    _spec("build_sitemap_xml", "seo_meta_and_sitemaps", "Build a valid urlset sitemap.xml string from a list of URLs.", "UrlList", "SitemapXml"),
    _spec("canonical_url", "seo_meta_and_sitemaps", "Canonicalize a URL: lowercase host, drop utm_* and fbclid params, strip trailing slash.", "Url", "CanonicalUrl"),
    _spec("meta_description_truncate", "seo_meta_and_sitemaps", "Truncate a description to <=160 chars on a word boundary, adding an ellipsis.", "Text", "MetaDescription"),
    _spec("robots_allows_path", "seo_meta_and_sitemaps", "Given robots.txt text, a user-agent and a path, return whether crawling is allowed.", "RobotsUaPath", "Boolean"),
    # single sign on
    _spec("parse_jwt_unverified", "single_sign_on", "Base64url-decode a JWT into {header, payload} WITHOUT verifying the signature.", "JwtToken", "JwtParts"),
    _spec("jwt_is_expired", "single_sign_on", "Given a payload exp (unix seconds) and now, return whether the token is expired.", "ExpNow", "Boolean", "D1_seeded"),
    _spec("basic_auth_decode", "single_sign_on", "Decode an 'Authorization: Basic' header into {username, password}.", "AuthHeader", "Credentials"),
    _spec("oauth_state_token", "single_sign_on", "Derive a deterministic anti-CSRF OAuth state token from a seed string.", "Seed", "StateToken", "D1_seeded"),
    # timesheet tracking
    _spec("duration_minutes", "timesheet_tracking", "Minutes between two HH:MM times on the same day (end>=start).", "StartEnd", "Minutes"),
    _spec("overtime_minutes", "timesheet_tracking", "Minutes worked beyond a daily threshold (default 480).", "WorkedThreshold", "Minutes"),
    _spec("round_to_increment", "timesheet_tracking", "Round minutes to the nearest increment (default 15).", "MinutesIncrement", "Minutes"),
    _spec("weekly_total_minutes", "timesheet_tracking", "Sum a list of daily minute totals into a weekly total.", "DailyMinutesList", "Minutes"),
    # web application firewall rules
    _spec("detect_sql_injection", "web_application_firewall_rules", "Return True iff the string contains a common SQL-injection pattern (UNION SELECT, OR 1=1, --, ;).", "InputString", "Boolean"),
    _spec("detect_xss", "web_application_firewall_rules", "Return True iff the string contains a common XSS payload (<script>, onerror=, javascript:).", "InputString", "Boolean"),
    _spec("ip_in_cidr", "web_application_firewall_rules", "Return True iff an IPv4 address is within a CIDR block.", "IpCidr", "Boolean"),
    _spec("normalize_path_traversal", "web_application_firewall_rules", "Collapse ../ and ./ segments to a safe normalized path.", "Path", "SafePath"),
    # accessible components
    _spec("contrast_ratio", "accessible_components", "WCAG contrast ratio between two #RRGGBB hex colors (1.0..21.0).", "TwoHexColors", "Ratio"),
    _spec("wcag_aa_passes", "accessible_components", "Return True iff a contrast ratio passes WCAG AA (4.5, or 3.0 for large text).", "RatioLarge", "Boolean"),
    _spec("heading_order_valid", "accessible_components", "Given a list of heading levels, return True iff no level jumps by more than 1.", "HeadingLevels", "Boolean"),
    _spec("aria_label_present", "accessible_components", "Return True iff an HTML element string carries a non-empty aria-label or aria-labelledby.", "ElementHtml", "Boolean"),
    # infrastructure as code
    _spec("parse_dockerfile_instructions", "infrastructure_as_code", "Parse a Dockerfile into an ordered list of (instruction, args) pairs.", "Dockerfile", "InstructionList"),
    _spec("dockerfile_uses_latest_tag", "infrastructure_as_code", "Return True iff any FROM in a Dockerfile uses :latest or an untagged image.", "Dockerfile", "Boolean"),
    _spec("dotenv_var_names", "infrastructure_as_code", "Extract the variable NAMES (not values) from a .env text.", "DotenvText", "NameList"),
    _spec("k8s_resource_kind", "infrastructure_as_code", "Return the 'kind' field from a Kubernetes YAML manifest text.", "K8sYaml", "Kind"),
    # realtime collaborative editing
    _spec("apply_insert_op", "realtime_collaborative_editing", "Apply an insert(pos, text) operation to a string.", "TextPosIns", "Text"),
    _spec("transform_pos_after_insert", "realtime_collaborative_editing", "Transform a cursor position after a concurrent insert at ins_pos of ins_len.", "PosInsert", "Position"),
    _spec("lww_merge", "realtime_collaborative_editing", "Last-write-wins merge: return the value with the greater timestamp (tie→a).", "TwoTimestamped", "Value"),
    # achievements and badges
    _spec("streak_length", "achievements_and_badges", "Longest run of consecutive daily dates (YYYY-MM-DD, sorted).", "DateList", "Count"),
    _spec("progress_pct", "achievements_and_badges", "Percent complete = 100*min(current,target)/target (0 if target<=0).", "CurrentTarget", "Percent"),
    _spec("badge_earned", "achievements_and_badges", "Return True iff value >= threshold.", "ValueThreshold", "Boolean"),
    # guided product tour
    _spec("next_tour_step", "guided_product_tour", "Given the current step id and an ordered step list, return the next step id ('' if last).", "CurrentSteps", "StepId"),
    _spec("tour_completion_pct", "guided_product_tour", "Percent of tour completed = 100*completed/total (0 if total<=0).", "CompletedTotal", "Percent"),
]

CAPABILITIES = sorted({s["capability"] for s in WEAK_CAPABILITY_SPECS})


def close_gaps(chat_fn, *, capability: Optional[str] = None, out_path: Optional[Path] = None) -> dict[str, Any]:
    specs = [s for s in WEAK_CAPABILITY_SPECS if capability is None or s["capability"] == capability]
    out_path = out_path or (resource(_DATA_SUBDIR) / "closed_gap_receipts.jsonl")
    summ = _synth_run(specs, chat_fn, out_path=out_path)
    return {**summ, "capabilities_targeted": sorted({s["capability"] for s in specs}), **BOUNDARY}


# ── self-test (offline, deterministic, mutation-gated) ─────────────────────────────────────────────────────────
def _stub_chat():
    """A deterministic stub: for contrast_ratio return a good body+fixtures; else a body that fails fixtures."""
    good = {"python_body": "def contrast_ratio(a, b):\n    return 21.0 if a != b else 1.0\n", "entry": "contrast_ratio",
            "positive_fixtures": [{"input": {"a": "#000000", "b": "#ffffff"}, "expected": 21.0},
                                  {"input": {"a": "#111111", "b": "#111111"}, "expected": 1.0},
                                  {"input": {"a": "#000000", "b": "#00ff00"}, "expected": 21.0}],
            "negative_fixtures": [{"input": {"a": "#000000", "b": "#ffffff"}, "expected": 21.0}]}

    def chat(_system: str, user: str):
        # only the contrast_ratio spec gets the matching good body; everything else gets a mismatching stub
        return (json.dumps(good), "stub") if "contrast_ratio" in user or "1.0..21.0" in user else \
               (json.dumps({"python_body": "def f(x):\n    return x\n", "entry": "f",
                            "positive_fixtures": [{"input": {"x": 1}, "expected": 2}], "negative_fixtures": []}), "stub")
    return chat


def _self_test() -> int:
    checks: list[tuple[str, bool]] = []
    checks.append(("35+ concrete deterministic specs across the 10 measured-weak capabilities",
                   len(WEAK_CAPABILITY_SPECS) >= 35 and len(CAPABILITIES) == 10))
    checks.append(("every spec is D0/D1 (truth-eligible) + needs_executor + typed edges",
                   all(s["determinism_level"] in ("D0_pure", "D1_seeded") and s["needs_executor"]
                       and s["edges"]["input_edge"] and s["edges"]["output_edge"] for s in WEAK_CAPABILITY_SPECS)))
    # a matching good body promotes; a mismatching one stays candidate — proves it's REALLY fixture-proven, not minted
    good = _synthesize(WEAK_CAPABILITY_SPECS[[s["name"] for s in WEAK_CAPABILITY_SPECS].index("contrast_ratio")],
                       _stub_chat())
    checks.append(("a weak-area spec with a passing body promotes to validated/certified (real sandbox proof)",
                   good["outcome"] == "promoted" and good["promoted_to"] in ("validated", "certified")))
    bad = _synthesize({"name": "timesheet_tracking_x", "determinism_level": "D0_pure",
                       "intent": "x", "input_schema": {}, "output_schema": {}}, _stub_chat())
    checks.append(("a spec whose stub body fails its fixtures stays candidate (not falsely promoted)",
                   bad["promoted_to"] == "candidate"))
    checks.append(("results are candidate-only", good["card"]["serves_truth"] is False))

    ok = all(v for _, v in checks)
    for nm, v in checks:
        print(f"  [{'ok' if v else 'XX'}] {nm}")
    print(("PASS" if ok else "FAIL") + f" - weak_capability_primitive_closer: {len(WEAK_CAPABILITY_SPECS)} concrete "
          f"deterministic specs across {len(CAPABILITIES)} MEASURED-weak capabilities -> real Hy3 synthesizer "
          "(security gate + sandbox + determinism + promote); fixture-proven only, serves_truth=false.")
    return 0 if ok else 1


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Create working primitives for the measured low-capability areas via Hy3.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--capability", default=None, choices=CAPABILITIES)
    ap.add_argument("--list", action="store_true", help="list the weak-capability decomposition")
    args = ap.parse_args(argv)

    if args.self_test:
        return _self_test()
    if args.list:
        for cap in CAPABILITIES:
            names = [s["name"] for s in WEAK_CAPABILITY_SPECS if s["capability"] == cap]
            print(f"  {cap}: {', '.join(names)}")
        return 0
    if args.run:
        from scripts.spec_to_executor_synthesizer import _hy3_chat_fn  # noqa: PLC0415
        n = len([s for s in WEAK_CAPABILITY_SPECS if args.capability is None or s["capability"] == args.capability])
        print(f"closing {n} weak-capability spec(s) with the real Hy3 synthesizer …")
        summ = close_gaps(_hy3_chat_fn(), capability=args.capability)
        print(json.dumps({k: summ[k] for k in ("specs", "promoted", "validated", "certified", "candidate",
              "quarantined", "capabilities_targeted", "by_outcome", "pool_path")}, indent=2, sort_keys=True))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
