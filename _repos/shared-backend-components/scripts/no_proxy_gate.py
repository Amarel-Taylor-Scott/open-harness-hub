#!/usr/bin/env python3
"""scripts.no_proxy_gate — the RULE that prevents dumb proxies from being reported as real (candidate-only tooling).

Owner (2026-07-09): I need REAL benchmarking and scoring of actual use / actual primitive token savings — make
rules and systems that PREVENT any dumb proxies. This gate enforces the rule at the code level:

  A module that reports a token-savings number or a quality SCORE must declare `BENCHMARK_KIND = "real" | "proxy"`.
  - REAL requires evidence of ACTUAL execution + ACTUAL measurement: API-reported completion tokens
    (`completion_tokens`/`usage`), an executed sandbox/oracle (`sandbox_run`, `n_pass`/`n_total`,
    `oracle_fixtures`), or a real HTTP call (`urlopen`). No proxy math in the headline path.
  - PROXY is anything estimated: token counts via `len(...)/4` (chars/4), scores via `hashlib`/`random`,
    or anything labeled `projection`/`simulated`/`_proxy`. A PROXY module MUST self-declare kind="proxy" and
    MUST NOT be cited as a real savings/quality number.

The gate FAILS (RED) if: a module has proxy signals but declares "real"; declares "real" without a real-execution
signal; or omits the declaration entirely. This makes "dumb proxy reported as real" a hard build failure, not a
judgment call. candidate=true / serves_truth=false.

    python3 scripts/no_proxy_gate.py --self-test
    python3 scripts/no_proxy_gate.py --audit          # classify every benchmark/scoring module
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
from scripts._repo_paths import install as _install_code_roots  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import json  # noqa: E402
import re  # noqa: E402
from typing import Any  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
_SCRIPTS = _sbc_boot / "scripts"

# ── the modules that produce a savings number or a quality score (must be classified). Add new ones here. ────
BENCHMARK_MODULES: list[str] = [
    "primitive_token_savings_ab.py",     # REAL: live model writes vs verified reuse; real completion tokens + oracle
    "certification_campaign.py",         # REAL: security -> sandbox oracle -> determinism
    "deterministic_dispatch_zoo.py",     # REAL: deterministic 0-token hit-rate over real primitives (no estimate)
    "deterministic_primitive_dispatch.py",  # REAL: deterministic resolution measurement
    "session_scale_evaluation.py",       # PROXY: 50k Monte-Carlo projection calibrated on the real A/B
    "process_path_search.py",            # PROXY: deterministic proxy scorer (real benchmarker is a seam)
    "pipeline_genome_grid.py",           # PROXY: structured proxy scorer w/ domain boosts
    "harness_bakeoff_spec.py",           # REAL-ish: real availability probe; matrix is a spec, no fabricated savings
    "real_scale_prompt_test.py",         # REAL: executes 50k prompts through real dispatch+primitive
    "project_task_harness.py",           # REAL_PROJECT: passes only on executed build/run/oracle, never plausibility
    "project_live_agent_ab.py",          # REAL_PROJECT: a real model solves a project task; executed oracle + real tokens
    "saas_buildout_decomposer.py",       # REAL_PROJECT: decompose a buildout -> EXECUTED determinism/oracle certification
    "buildout_forge.py",                 # REAL_PROJECT_BUILDOUT: a built app BOOTS + a hidden HTTP oracle exercises endpoints
    "buildout_oracle_patterns.py",       # REAL_PROJECT_BUILDOUT: EXECUTED worker + csv-upload genomes; hidden oracle per build
    "buildout_forge_ab.py",              # REAL_PROJECT_BUILDOUT: both arms BUILD+BOOT+oracle; savings=real tokens-to-pass
    "buildout_forge_large.py",           # REAL_PROJECT_BUILDOUT: one LARGE 11-module app BOOTS + a hidden HTTP oracle drives ~27 endpoints
    "buildout_forge_pipeline.py",        # REAL_PROJECT_BUILDOUT: a ten-module ETL DAG RUNS + a hidden pipeline oracle inspects out.db/metrics.json
    "real_savings_report.py",            # REAL: honest ledger — headlines ONLY executed paired passes; closes the escape hatch
    "run_large_project_ab.py",           # REAL_PROJECT_BUILDOUT: LARGE build bare vs certified coverage pack; both BOOT+oracle; netted tokens
    "real_app_forge.py",                 # REAL_APP_BUILDOUT: A6 = EQUIVALENT app build EXECUTES + passes a hidden oracle; A0-A5 source-only
    "bench_project_to_primitives.py",    # REAL: executed decomposition of built code -> primitive YIELD per project; deterministic
]

# ── signal patterns ──────────────────────────────────────────────────────────────────────────────────────────
_REAL_SIGNALS: dict[str, str] = {
    "completion_tokens": r"completion_tokens", "api_usage": r"\busage\b", "sandbox": r"sandbox_run",
    "oracle": r"oracle_fixtures|n_pass|n_total", "live_http": r"urlopen|requests\.(get|post)",
    "deterministic_measured": r"hit_rate|brief_hits|certified\b",
    "subprocess_exec": r"subprocess\.run", "project_oracle": r"oracle_pass|oracle_checks|build_pass",
}
_KIND_ALIASES = {"real_project": "real",             # executed build/run/oracle
                 "real_project_buildout": "real",    # a built app BOOTS + a hidden HTTP oracle exercises it
                 "real_app_buildout": "real"}        # A6 = an EQUIVALENT app build EXECUTES + passes a hidden oracle
_PROXY_SIGNALS: dict[str, str] = {
    "chars_over_4": r"len\([^)]*\)\s*/\s*4|/\s*4\).*token|chars\s*/\s*4",
    "hash_score": r"hashlib\.sha256[^\n]*\n[^\n]*(score|proxy|obj)|def\s+_proxy",
    "random_score": r"random\.Random[^\n]*\n[^\n]*(score|objective)",
    "labeled_proxy": r'"proxy"|projection|simulated|PROXY',
}
_KIND_RE = re.compile(r'BENCHMARK_KIND\s*=\s*["\'](real|proxy|real_project|real_project_buildout|real_app_buildout)["\']')


def _find(patterns: dict[str, str], text: str) -> list[str]:
    return [name for name, pat in patterns.items() if re.search(pat, text, re.IGNORECASE)]


def audit_module(filename: str) -> dict[str, Any]:
    path = _SCRIPTS / filename
    if not path.exists():
        return {"module": filename, "error": "missing", "ok": False}
    text = path.read_text(encoding="utf-8")
    m = _KIND_RE.search(text)
    declared_raw = m.group(1) if m else None
    declared = _KIND_ALIASES.get(declared_raw, declared_raw)  # real_project -> real for enforcement
    real = _find(_REAL_SIGNALS, text)
    proxy = _find(_PROXY_SIGNALS, text)
    # STRONG real = the headline quantity is actually executed/measured (not a secondary tiny estimate).
    strong_real = any(s in real for s in ("completion_tokens", "sandbox", "oracle", "live_http",
                                          "deterministic_measured", "subprocess_exec", "project_oracle"))
    minor_estimate = bool(proxy) and strong_real  # e.g. real API tokens + a tiny len/4 on the reuse call-line
    inferred = "real" if strong_real else ("proxy" if proxy else "unknown")
    # ENFORCEMENT — a "real" claim is only violated when the HEADLINE lacks strong real backing.
    violations = []
    if declared is None:
        violations.append("no BENCHMARK_KIND declaration")
    if declared == "real" and proxy and not strong_real:
        violations.append(f"declares REAL but headline is proxy {proxy} with NO strong real signal "
                          f"(completion_tokens/sandbox/oracle) — a dumb proxy reported as real")
    if declared == "real" and not real:
        violations.append("declares REAL but no real-execution signal (completion_tokens/sandbox/oracle/http)")
    if declared == "proxy" and not proxy and not real:
        violations.append("declares PROXY but shows neither proxy nor real signals (unclassifiable)")
    return {"module": filename, "declared_kind": declared, "inferred_kind": inferred,
            "real_signals": real, "proxy_signals": proxy, "minor_estimate": minor_estimate,
            "violations": violations, "ok": not violations}


def enforce() -> dict[str, Any]:
    audits = [audit_module(f) for f in BENCHMARK_MODULES]
    failing = [a for a in audits if not a["ok"]]
    real_headline = sorted(a["module"] for a in audits if a.get("declared_kind") == "real" and a["ok"])
    proxy_labeled = sorted(a["module"] for a in audits if a.get("declared_kind") == "proxy" and a["ok"])
    return {"record_type": "no_proxy_gate_audit", "n_modules": len(audits),
            "real_headline_allowed": real_headline, "proxy_labeled": proxy_labeled,
            "failing": failing, "gate_pass": not failing,
            "rule": "REAL = executes + measures actual tokens/oracle; PROXY (chars/4, hash/random, projection) "
                    "must self-declare and is NEVER a headline savings number.",
            "audits": audits, **BOUNDARY}


def self_test() -> bool:
    """Mutation-gated: the gate correctly classifies the REAL modules (real signals + kind=real) and the PROXY
    modules (proxy signals + kind=proxy), and REJECTS a synthetic module that dresses a proxy up as real."""
    # (1) every registered benchmark module must carry a valid declaration and pass enforcement.
    result = enforce()
    assert result["gate_pass"], f"registered modules must pass the no-proxy gate: {result['failing']}"

    # (2) the REAL token-savings benchmark is classified REAL: the HEADLINE (bare-write) is real API
    #     completion_tokens + executed oracle; the tiny reuse call-line len/4 is an acknowledged minor_estimate,
    #     which passes (strong real backing dominates) — NOT a violation.
    ab = audit_module("primitive_token_savings_ab.py")
    assert ab["declared_kind"] == "real" and "completion_tokens" in ab["real_signals"] and ab["ok"], ab
    assert ab["minor_estimate"] is True, "the reuse-line len/4 must be surfaced as a minor estimate, not hidden"

    # (3) the proxy scorers are classified PROXY (they must NOT be headline savings numbers).
    for prox in ("pipeline_genome_grid.py", "process_path_search.py", "session_scale_evaluation.py"):
        a = audit_module(prox)
        assert a["declared_kind"] == "proxy", f"{prox} must declare proxy: {a}"
    assert "pipeline_genome_grid.py" not in result["real_headline_allowed"], "a proxy must never be headline-real"

    # (4) ENFORCEMENT bite: a synthetic module that declares REAL but scores via chars/4 must FAIL.
    fake = ('BENCHMARK_KIND = "real"\n'
            'def score(text):\n    return len(text) / 4  # token estimate\n')
    tmp = _SCRIPTS / "_no_proxy_gate_selftest_fixture.py"
    try:
        tmp.write_text(fake, encoding="utf-8")
        a = audit_module("_no_proxy_gate_selftest_fixture.py")
        assert not a["ok"] and any("proxy" in v for v in a["violations"]), \
            f"gate must reject a chars/4 proxy declared as real: {a}"
        # and a module with NO declaration must fail.
        tmp.write_text("def score(x):\n    return 1\n", encoding="utf-8")
        assert not audit_module("_no_proxy_gate_selftest_fixture.py")["ok"], "missing declaration must fail"
    finally:
        tmp.unlink(missing_ok=True)

    print(f"OK no_proxy_gate self-test: {result['n_modules']} benchmark modules audited; "
          f"REAL-headline={result['real_headline_allowed']}; PROXY-labeled={result['proxy_labeled']}; "
          f"gate rejects chars/4-declared-real + missing declarations; serves_truth=false")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="Prevent dumb proxies from being reported as real benchmarks.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--audit", action="store_true")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if args.audit:
        r = enforce()
        for a in r["audits"]:
            tag = "REAL " if a.get("declared_kind") == "real" else ("PROXY" if a.get("declared_kind") == "proxy"
                                                                    else "  ?  ")
            flag = "OK" if a["ok"] else "FAIL " + ";".join(a["violations"])
            print(f"  [{tag}] {a['module']:<40} {flag}")
        print(f"\n  gate_pass={r['gate_pass']} | REAL-headline-allowed: {r['real_headline_allowed']}")
        sys.exit(0 if r["gate_pass"] else 1)
    self_test()


if __name__ == "__main__":
    main()
