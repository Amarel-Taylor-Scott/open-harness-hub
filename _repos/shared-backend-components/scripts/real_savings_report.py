#!/usr/bin/env python3
"""scripts.real_savings_report — the ONE honest savings ledger: collect every real benchmark receipt, apply the
paired + no-proxy discipline, and refuse to HEADLINE anything that isn't executed paired evidence. This is the
report the owner demanded — "do not stop until you have a real_savings report generated, even if it says not
enough passing paired runs yet" — and the antidote to treating infrastructure as success (candidate-only).

The core is `classify_pair(baseline, treatment)`: the rules that make a savings number honest —
  * both lanes PASS         -> measured_savings = baseline_tokens - treatment_tokens (headline iff both REAL);
  * treatment passes, baseline fails -> capability_lift (token-savings N/A — no baseline cost);
  * baseline passes, treatment FAILS -> treatment_regressed (NO savings claimable — the escape hatch closed);
  * both fail               -> inconclusive_no_baseline (nothing to compare — NEVER a savings number).

It reads the receipts each benchmark actually wrote, tags each as REAL / IDEALIZED / CALIBRATED / PROXY with a
one-line honest reason, and writes docs/REAL_SAVINGS_NUMBERS.md + artifacts json. It EXECUTES nothing itself
(it is a reporter) — every number it surfaces is traced to a receipt path or marked missing.

    python3 scripts/real_savings_report.py --self-test
    python3 scripts/real_savings_report.py --run
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/buildout_forge.py) ────────────────────────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
from typing import Any  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
BENCHMARK_KIND = "real"  # a reporter over executed receipts; it fabricates nothing and headlines only paired passes
DEV_INTEL_REL = "data/dev-intel"
SAVINGS_JSON_REL = "data/dev-intel/savings/latest_savings_results.json"
REPORT_MD_REL = "docs/REAL_SAVINGS_NUMBERS.md"


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
# The honest core: how a paired savings number is (dis)allowed. Pure + mutation-gated.
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
def classify_pair(baseline: dict[str, Any], treatment: dict[str, Any], *, both_real: bool = True,
                  no_proxy_ok: bool = True) -> dict[str, Any]:
    """baseline/treatment = {"pass": bool, "tokens": int}. Returns the honest verdict + whether it may headline."""
    bp, tp = bool(baseline.get("pass")), bool(treatment.get("pass"))
    bt, tt = baseline.get("tokens"), treatment.get("tokens")
    if bp and tp:
        saved = (bt - tt) if (isinstance(bt, (int, float)) and isinstance(tt, (int, float))) else None
        eligible = both_real and no_proxy_ok
        return {"verdict": "measured_savings", "tokens_saved": saved,
                "tokens_reduction_ratio": round(saved / bt, 3) if saved is not None and bt else None,
                "headline_eligible": eligible,
                "reason": None if eligible else "both lanes pass but not both REAL / no_proxy failed"}
    if tp and not bp:
        return {"verdict": "capability_lift", "tokens_saved": None, "tokens_reduction_ratio": None,
                "headline_eligible": both_real and no_proxy_ok,
                "reason": "treatment passes where baseline FAILS; token-savings N/A (no baseline cost to beat)"}
    if bp and not tp:
        return {"verdict": "treatment_regressed", "tokens_saved": None, "tokens_reduction_ratio": None,
                "headline_eligible": False,
                "reason": "treatment FAILED while baseline passed — NO token savings claimable"}
    return {"verdict": "inconclusive_no_baseline", "tokens_saved": None, "tokens_reduction_ratio": None,
            "headline_eligible": False, "reason": "both lanes failed the oracle — nothing to compare"}


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
# Collectors — read what each benchmark actually wrote; classify honestly; never invent a missing number.
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
def _find(patterns: list[str]) -> list[Path]:
    root = resource(DEV_INTEL_REL)
    if not root.exists():
        return []
    out: list[Path] = []
    for pat in patterns:
        out.extend(sorted(root.rglob(pat)))
    return out


def _load(p: Path) -> dict[str, Any] | None:
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return None


def collect_function_ab() -> dict[str, Any]:
    """all-75 function A/B: REAL bare (executed tokens + correctness) but IDEALIZED treatment (call-line tokens +
    asserted pass). The bare cost is headline; the '19x' is an upper bound, NOT a realized paired number."""
    hits = _find(["token_savings_ab_receipt.json"])
    if not hits:
        return {"track": "function_level_ab", "status": "missing", "receipt_path": None, **BOUNDARY}
    d = _load(hits[-1]) or {}
    return {"track": "function_level_ab", "status": "present", "receipt_path": str(hits[-1]),
            "benchmark_kind": "real", "classification": "real_baseline__idealized_treatment",
            "headline_eligible": False,
            "reason": ("bare arm is executed (real tokens + correctness); reuse arm is NOT executed — it counts "
                       "only the call-line tokens and asserts pass. 19x is an upper bound. Also degenerate: "
                       "task == primitive."),
            "numbers": {"n_tasks": d.get("n_tasks"), "bare_total_tokens": d.get("armA_total_tokens"),
                        "bare_correct_rate": d.get("armA_correct_rate"),
                        "idealized_reuse_tokens": d.get("armB_total_tokens"),
                        "upper_bound_factor": d.get("savings_factor")},
            "real_headline": {"bare_generation_cost_tokens": d.get("armA_total_tokens"),
                              "bare_correct_rate": d.get("armA_correct_rate")}, **BOUNDARY}


def collect_project_ab() -> list[dict[str, Any]]:
    """project live-agent A/B (cloud_function): fully EXECUTED both lanes, but every lane failed the oracle ->
    inconclusive_no_baseline (no savings). The 20B package lane DID import the primitives (real behavioral fact)."""
    out = []
    for p in _find(["cloud_function_3lane_ab_*.json", "*_live_agent_ab.json"]):
        d = _load(p) or {}
        a = d.get("harness_alone", {})
        c = d.get("harness_plus_package", d.get("harness_plus_primitives", {}))
        pair = classify_pair({"pass": a.get("oracle_pass"), "tokens": a.get("tokens_to_pass")},
                             {"pass": c.get("oracle_pass"), "tokens": c.get("tokens_to_pass")})
        out.append({"track": "project_level_ab", "status": "present", "receipt_path": str(p),
                    "benchmark_kind": "real_project", "classification": "executed_paired",
                    "headline_eligible": pair["headline_eligible"], "verdict": pair["verdict"],
                    "reason": pair["reason"],
                    "numbers": {"pass_A": a.get("oracle_pass"), "pass_C": c.get("oracle_pass"),
                                "tokens_A": a.get("tokens_to_pass"), "tokens_C": c.get("tokens_to_pass"),
                                "package_imported": c.get("package_imported"),
                                "reuse": c.get("primitive_hits"), "error": c.get("error")}, **BOUNDARY})
    return out


def collect_buildout_ab() -> list[dict[str, Any]]:
    """buildout A/B (BuildoutForge): both lanes BUILD + BOOT + hidden HTTP oracle. This is the track that CAN
    yield a real project-level savings number when a capable model passes the bare lane."""
    out = []
    for p in _find(["*_buildout_ab.json"]):
        d = _load(p) or {}
        a = d.get("harness_alone", {})
        c = d.get("harness_plus_extracted_primitives", {})
        pair = classify_pair({"pass": a.get("oracle_pass"), "tokens": a.get("tokens_to_pass")},
                             {"pass": c.get("oracle_pass"), "tokens": c.get("tokens_to_pass")})
        out.append({"track": "buildout_level_ab", "status": "present", "receipt_path": str(p),
                    "benchmark_kind": "real_project_buildout", "classification": "executed_paired_buildout",
                    "headline_eligible": pair["headline_eligible"], "verdict": pair["verdict"],
                    "reason": pair["reason"], "genome_id": d.get("genome_id"),
                    "numbers": {"pass_A": a.get("oracle_pass"), "pass_C": c.get("oracle_pass"),
                                "tokens_A": a.get("tokens_to_pass"), "tokens_C": c.get("tokens_to_pass"),
                                "tokens_saved": pair.get("tokens_saved"),
                                "reduction_ratio": pair.get("tokens_reduction_ratio"),
                                "package_imported_C": c.get("package_imported"),
                                "injected": c.get("injected")}, **BOUNDARY})
    return out


def collect_buildout_replicates() -> list[dict[str, Any]]:
    """Replicate DISTRIBUTIONS supersede a single buildout run (a single run cherry-picks one draw of model
    noise). Reports mean/range/n_negative; headline-eligible only if all runs passed AND the mean is positive —
    with the noise stated so a small/noisy effect is never dressed as a big robust one."""
    out = []
    for p in _find(["*_replicates.json"]):
        d = _load(p) or {}
        if d.get("record_type") != "buildout_ab_replicate_distribution":
            continue
        all_pass = bool(d.get("all_lanes_passed"))
        mean = d.get("tokens_saved_mean")
        eligible = all_pass and isinstance(mean, (int, float)) and mean > 0
        noisy = (d.get("tokens_saved_stdev") or 0) >= abs(mean or 1) or (d.get("n_negative") or 0) > 0
        out.append({"track": "buildout_level_ab_distribution", "status": "present", "receipt_path": str(p),
                    "benchmark_kind": "real_project_buildout", "classification": "executed_paired_distribution",
                    "genome_id": d.get("genome_id"), "headline_eligible": eligible,
                    "verdict": "measured_savings_noisy" if (eligible and noisy) else
                               ("measured_savings" if eligible else "no_net_savings"),
                    "reason": d.get("honest_verdict"),
                    "numbers": {"n": d.get("n"), "all_pass": all_pass,
                                "tokens_saved_mean": mean, "tokens_saved_median": d.get("tokens_saved_median"),
                                "tokens_saved_range": [d.get("tokens_saved_min"), d.get("tokens_saved_max")],
                                "tokens_saved_stdev": d.get("tokens_saved_stdev"),
                                "reduction_mean": d.get("reduction_mean"),
                                "n_positive": d.get("n_positive"), "n_negative": d.get("n_negative")}, **BOUNDARY})
    return out


def collect_large_ab_distributions() -> list[dict[str, Any]]:
    """The run_large_project_ab distributions (coverage / compiled_route / macro treatments). Headline ONLY when
    there are both-pass runs AND mean TOTAL-token savings is positive — surfaces the honest negatives too
    (importable + compiled_route on micro helpers measured NET-NEGATIVE; macro-primitive is the test that can win)."""
    out = []
    for p in _find(["*_ab_distribution.json"]):
        d = _load(p) or {}
        if d.get("record_type") != "large_project_ab_distribution":
            continue
        ts = d.get("total_tokens_saved") or {}
        os = d.get("output_tokens_saved") or {}  # generation-only: the AMORTIZABLE view (primitive is a fixed asset)
        nbp = d.get("n_both_pass", 0)
        mean = ts.get("mean")
        omean = os.get("mean")
        eligible = nbp > 0 and isinstance(mean, (int, float)) and mean > 0
        out.append({"track": "large_project_ab", "status": "present", "receipt_path": str(p),
                    "benchmark_kind": "real_project_buildout", "genome_id": d.get("genome_id"),
                    "classification": f"executed_paired::{d.get('treatment_mode', '?')}",
                    "headline_eligible": eligible,
                    "verdict": "measured_savings_positive" if eligible else "net_negative_or_no_baseline",
                    "reason": ("both-pass runs with POSITIVE mean total-token savings"
                               if eligible else
                               f"treatment={d.get('treatment_mode')}, n_both_pass={nbp}, total_saved_mean={mean} — "
                               f"reuse did NOT net-save here (input overhead / model regenerates the bulk)"),
                    "output_savings_amortized_mean": omean,  # if >0: the model WRITES LESS (mechanism works)
                    "numbers": {"treatment": d.get("treatment_mode"), "n_runs": d.get("n_runs"), "n_both_pass": nbp,
                                "verdicts": d.get("verdict_counts"), "total_saved_mean": mean,
                                "output_saved_mean": omean, "total_saved_range": [ts.get("min"), ts.get("max")],
                                "output_saved_range": [os.get("min"), os.get("max")],
                                "n_negative": ts.get("n_negative")}, **BOUNDARY})
    return out


def collect_dispatch_scale() -> dict[str, Any]:
    """50k deterministic-dispatch: hit-rate + execution-correctness are REAL (executed over 50k); the token-savings
    total is CALIBRATED from the A/B per-task cost — real hit-rate is headline, the savings total is not."""
    hits = _find(["real_scale_prompt_receipt.json", "*real_scale*.json", "deterministic_dispatch*_receipt.json"])
    if not hits:
        return {"track": "dispatch_scale_50k", "status": "missing", "receipt_path": None, **BOUNDARY}
    d = _load(hits[-1]) or {}
    return {"track": "dispatch_scale_50k", "status": "present", "receipt_path": str(hits[-1]),
            "benchmark_kind": "real", "classification": "real_hitrate__calibrated_savings",
            "headline_eligible": False,
            "reason": ("dispatch hit-rate + execution-correctness are executed (headline); the tokens-saved TOTAL "
                       "is calibrated from the A/B per-task cost, not 50k live generations."),
            "numbers": {"n": d.get("n"), "dispatch_hit_rate": d.get("dispatch_hit_rate"),
                        "execution_correct_on_hits": d.get("execution_correct_on_hits"),
                        "calibrated_tokens_saved": d.get("real_tokens_saved_total"),
                        "llm_cost_source": d.get("llm_cost_source")},
            "real_headline": {"dispatch_hit_rate": d.get("dispatch_hit_rate"),
                              "execution_correct_on_hits": d.get("execution_correct_on_hits")}, **BOUNDARY}


def collect_all() -> dict[str, Any]:
    tracks = [collect_function_ab(), collect_dispatch_scale()]
    tracks += collect_project_ab()
    dist = collect_buildout_replicates()                         # a distribution supersedes a single cherry-picked run
    dist_genomes = {t.get("genome_id") for t in dist}
    tracks += [t for t in collect_buildout_ab() if t.get("genome_id") not in dist_genomes] + dist
    tracks += collect_large_ab_distributions()  # coverage / compiled_route / macro treatments (incl. honest negatives)
    headline = [t for t in tracks if t.get("headline_eligible")]
    present = [t for t in tracks if t.get("status") == "present"]
    return {"record_type": "real_savings_report", "benchmark_kind": BENCHMARK_KIND,
            "n_tracks": len(tracks), "n_present": len(present), "n_headline_eligible": len(headline),
            "headline_savings_proven": len(headline) > 0,
            "tracks": tracks, **BOUNDARY}


def render_markdown(report: dict[str, Any]) -> str:
    lines = ["# Real Savings Numbers — honest ledger", "",
             "> Generated by `scripts/real_savings_report.py`. A number is **headline-eligible** only when both",
             "> lanes ran the SAME task, both are REAL (executed), both PASSED, and no-proxy holds. `serves_truth=false`.",
             "",
             f"**Headline savings proven: {'YES' if report['headline_savings_proven'] else 'NOT YET'}** "
             f"({report['n_headline_eligible']} of {report['n_present']} present tracks headline-eligible).", "",
             "| Track | Status | Classification | Headline? | Key numbers | Receipt |",
             "|---|---|---|---|---|---|"]
    for t in report["tracks"]:
        if t.get("status") != "present":
            lines.append(f"| {t['track']} | missing | — | — | (no receipt found) | — |")
            continue
        nums = ", ".join(f"{k}={v}" for k, v in (t.get("numbers") or {}).items() if v is not None)
        rp = Path(t["receipt_path"]).name if t.get("receipt_path") else "—"
        lines.append(f"| {t['track']} | present | {t.get('classification','')} | "
                     f"{'✅' if t.get('headline_eligible') else '❌'} | {nums[:160]} | {rp} |")
    lines += ["", "## Honest reasons (why each is / isn't headline)"]
    for t in report["tracks"]:
        if t.get("status") == "present" and t.get("reason"):
            lines.append(f"- **{t['track']}** ({t.get('verdict', t.get('classification'))}): {t['reason']}")
    lines += ["", "## What would make project-level savings headline-eligible",
              "A buildout A/B where the **bare** lane BOOTS + passes the hidden HTTP oracle (a real baseline cost)",
              "AND the extracted-primitives lane also passes at fewer tokens — both executed. Blocker today: a model",
              "strong enough to pass the bare buildout (free-pool 120B exhausts; 20B can't). Wire a stronger model",
              "and re-run `buildout_forge_ab.py --live`.", ""]
    return "\n".join(lines)


def emit() -> dict[str, str]:
    report = collect_all()
    out_json = resource(SAVINGS_JSON_REL)
    out_json.parent.mkdir(parents=True, exist_ok=True)
    out_json.write_text(json.dumps(report, indent=2, sort_keys=True), encoding="utf-8")
    md = resource(REPORT_MD_REL)
    md.parent.mkdir(parents=True, exist_ok=True)
    md.write_text(render_markdown(report), encoding="utf-8")
    return {"json": str(out_json), "md": str(md), "headline_savings_proven": str(report["headline_savings_proven"]),
            "n_headline_eligible": str(report["n_headline_eligible"])}


def self_test() -> bool:
    """Mutation-gated on the honest core: the escape hatch (claim savings when treatment fails) MUST be closed."""
    win = classify_pair({"pass": True, "tokens": 1000}, {"pass": True, "tokens": 400})
    assert win["verdict"] == "measured_savings" and win["tokens_saved"] == 600 and win["headline_eligible"], win

    # THE critical rule: baseline passes, treatment fails -> NO savings, not headline.
    regress = classify_pair({"pass": True, "tokens": 1000}, {"pass": False, "tokens": 0})
    assert regress["verdict"] == "treatment_regressed" and regress["tokens_saved"] is None \
        and regress["headline_eligible"] is False, f"must NOT claim savings on regression: {regress}"

    lift = classify_pair({"pass": False, "tokens": 0}, {"pass": True, "tokens": 400})
    assert lift["verdict"] == "capability_lift" and lift["tokens_saved"] is None, lift

    both_fail = classify_pair({"pass": False, "tokens": 0}, {"pass": False, "tokens": 0})
    assert both_fail["verdict"] == "inconclusive_no_baseline" and both_fail["headline_eligible"] is False, both_fail

    # not-both-real demotes an otherwise-winning pair out of headline.
    proxyd = classify_pair({"pass": True, "tokens": 1000}, {"pass": True, "tokens": 400}, both_real=False)
    assert proxyd["verdict"] == "measured_savings" and proxyd["headline_eligible"] is False, proxyd

    report = collect_all()  # runs over whatever receipts exist; must never crash, never invent
    assert report["record_type"] == "real_savings_report" and report["serves_truth"] is False
    assert isinstance(report["headline_savings_proven"], bool)
    md = render_markdown(report)
    assert "Headline savings proven" in md
    print(f"OK real_savings_report self-test: honest-core gated (regression claims NO savings; both-fail is "
          f"inconclusive; non-real demoted); collected {report['n_present']} present tracks, "
          f"{report['n_headline_eligible']} headline-eligible; serves_truth=false")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="Honest savings ledger over all real benchmark receipts.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if args.run:
        paths = emit()
        print(json.dumps(paths, indent=2))
        report = collect_all()
        print("\n" + render_markdown(report))
        return
    self_test()


if __name__ == "__main__":
    main()
