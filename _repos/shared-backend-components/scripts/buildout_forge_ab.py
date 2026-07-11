#!/usr/bin/env python3
"""scripts.buildout_forge_ab — the both-arms-EXECUTED buildout A/B: a real model BUILDS a multi-file service
twice — bare vs with certified primitives extracted from a prior buildout PRE-INSTALLED — and BOTH builds must
BOOT and pass the hidden HTTP oracle. Savings = real tokens-to-pass, bare vs reuse. This is the honest
project-level number the function-level A/B (task == primitive, degenerate) cannot give (candidate-only).

Owner (2026-07-09): "if I provide more keys can you actually prove project level savings?" More keys remove the
free-pool quota wall (today's 120B run died on all_keys_exhausted for lanes B/C), but SAVINGS additionally needs
the BARE lane to PASS — a baseline token cost to beat — which needs a capable-enough model. This harness makes
the measurement honest and unambiguous:

  Lane A  harness_alone                 — model emits the whole multi-file build; must boot + pass the oracle.
  Lane C  harness_plus_extracted_prims  — certified primitives DECOMPOSED from a prior build are pre-installed as
                                          an importable verified_primitives.py; model imports + builds thin glue;
                                          must boot + pass the SAME oracle.

Verdict is honest by construction:
  * both pass          -> measured_savings = tokens_A - tokens_C (a real number, either sign);
  * A fails, C passes  -> capability_lift (primitives made an unbuildable project buildable);
  * A passes, C fails  -> primitives_hurt (reported, not hidden);
  * both fail          -> inconclusive (no baseline — NEVER reported as savings).

BENCHMARK_KIND=real_project_buildout. Offline `--self-test` uses mock builders (mutation-gated, no live calls);
`--live --model ...` drives the real model via the OpenRouter pool. serves_truth=false throughout.

    python3 scripts/buildout_forge_ab.py --self-test
    python3 scripts/buildout_forge_ab.py --live --model openai/gpt-oss-120b:free --repair 3
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
import re  # noqa: E402
from typing import Any, Callable  # noqa: E402

from scripts.buildout_forge import _GENOMES, run_buildout  # noqa: E402
from scripts.saas_buildout_decomposer import decompose_project, certify_candidate  # noqa: E402
from scripts.primitive_token_savings_ab import _load_pool, live_model  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
BENCHMARK_KIND = "real_project_buildout"  # no_proxy_gate: both lanes BOOT + pass the hidden oracle; real tokens
ARTIFACT_DIR_REL = "data/dev-intel/buildout_forge"
PACKAGE_MODULE = "verified_primitives"
_DEFAULT_GENOME = "vendor_onboarding_service__stdlib_http__v0"
# fenced multi-file contract: ```python filename=<path>\n<code>``` (same shape as real_buildout_ab_harness)
_FILE_BLOCK_RE = re.compile(r"```python(?:[ \t]+filename=([^\s`]+))?\s*\n(.*?)```", re.DOTALL)
_MULTIFILE_CONTRACT = (
    "OUTPUT CONTRACT: respond ONLY with complete runnable files in fenced blocks of the form\n"
    "```python filename=<relative/path.py>\\n<code>\\n``` . You MUST produce app.py (a stdlib http.server app "
    "whose main() reads --port and serves the endpoints), plus any helper modules you use. stdlib ONLY (no pip "
    "packages). The app must boot with `python app.py --port N`. No prose outside code blocks, no TODOs."
)


def _parse_files(text: str) -> dict[str, str]:
    """Extract fenced files. A block without filename= defaults to app.py (the entry the oracle boots)."""
    files: dict[str, str] = {}
    for fname, code in _FILE_BLOCK_RE.findall(text or ""):
        files[(fname or "app.py").strip()] = code
    return files


def extracted_primitive_package(genome_id: str) -> tuple[dict[str, str], list[str]]:
    """DECOMPOSE the genome's prior (reference) build and CERTIFY its pure primitives, then render the certified
    ones as an importable verified_primitives.py (the extracted-primitive reuse material). Honest: only
    decomposer-certified (deterministic/oracle_correct) primitives are injected — nothing asserted."""
    good = _GENOMES[genome_id]["good"]
    decomp = decompose_project(good)
    # sample inputs shaped like the genome's domain payloads (drive the determinism probe)
    samples = [({"vendor_id": "V1", "name": "Acme"},), ({"name": "NoId"},), ({"vendor_id": "V2", "name": "Beta"},)]
    certified: list[dict[str, Any]] = []
    for p in decomp["primitives"]:
        if not p.get("certification_target"):
            continue
        cert = certify_candidate(p, sample_inputs=samples)
        if cert["verdict"] in ("deterministic", "oracle_correct"):
            certified.append(p)
    if not certified:
        return {}, []
    header = ('"""verified_primitives — certified primitives EXTRACTED from a prior buildout (candidate=true / '
              'serves_truth=false). Import and compose; do not reimplement."""\n\n')
    body = "\n\n".join(p["executable_body"] for p in certified)
    return {f"{PACKAGE_MODULE}.py": header + body}, [p["name"] for p in certified]


def _prompt(genome: dict[str, Any], injected_names: list[str], prior_fail: dict | None, mode: str) -> str:
    p = f"Build this project: {genome['goal']}\n\n{_MULTIFILE_CONTRACT}\n"
    if mode == "package" and injected_names:
        names = ", ".join(injected_names)
        p += (f"\nA module `{PACKAGE_MODULE}` is ALREADY INSTALLED in your workspace with these certified, "
              f"verified-correct helpers extracted from a prior build: {names}. Import them "
              f"(`from {PACKAGE_MODULE} import {names}`) and COMPOSE them — do NOT reimplement their logic.\n")
    if prior_fail:
        failed = [k for k, v in prior_fail.items() if not v]
        p += f"\nYour previous build FAILED these hidden checks: {failed}. Fix it and resend ALL files.\n"
    return p


def run_lane(genome_id: str, lane: str, agent: Callable[[str], dict[str, Any]], repair: int,
             mode: str) -> dict[str, Any]:
    """Drive the agent to BUILD the multi-file project; BOOT it + run the hidden oracle; repair up to N turns.
    mode: 'none' (bare) | 'package' (certified extracted primitives pre-installed). Real tokens throughout."""
    genome = _GENOMES[genome_id]
    extra, injected = ({}, [])
    if mode == "package":
        extra, injected = extracted_primitive_package(genome_id)
    tokens = 0
    prior = None
    imported = False
    for turn in range(repair + 1):
        gen = agent(_prompt(genome, injected, prior, mode))
        tokens += gen.get("completion_tokens", 0)
        files = _parse_files(gen.get("code") or gen.get("text") or "")
        if "app.py" not in files:
            prior = {"emitted_app_py": False}
            continue
        imported = any(PACKAGE_MODULE in c for c in files.values())
        receipt = run_buildout(genome_id, files, lane=lane, extra_files=extra)
        if receipt.get("oracle_pass"):
            return {"lane": lane, "oracle_pass": True, "tokens_to_pass": tokens, "repair_turns": turn,
                    "n_files": len(files), "package_imported": imported, "injected": injected,
                    "checks": receipt["oracle_checks"], **BOUNDARY}
        prior = receipt.get("oracle_checks") or {}
    return {"lane": lane, "oracle_pass": False, "tokens_to_pass": tokens, "repair_turns": repair,
            "n_files": len(_parse_files(gen.get("code") or gen.get("text") or "")),
            "package_imported": imported, "injected": injected, "checks": prior, **BOUNDARY}


def run_ab(genome_id: str, agent: Callable[[str], dict[str, Any]], repair: int = 3) -> dict[str, Any]:
    a = run_lane(genome_id, "harness_alone", agent, repair, mode="none")
    c = run_lane(genome_id, "harness_plus_extracted_primitives", agent, repair, mode="package")
    ap, cp = a.get("oracle_pass"), c.get("oracle_pass")
    if ap and cp:
        verdict = "measured_savings"
        savings = a["tokens_to_pass"] - c["tokens_to_pass"]
    elif cp and not ap:
        verdict, savings = "capability_lift", None
    elif ap and not cp:
        verdict, savings = "primitives_hurt", None
    else:
        verdict, savings = "inconclusive_no_baseline", None
    return {"record_type": "buildout_forge_ab", "genome_id": genome_id, "benchmark_kind": BENCHMARK_KIND,
            "harness_alone": a, "harness_plus_extracted_primitives": c,
            "verdict": verdict, "tokens_saved": savings,
            "delta": {"pass_A": ap, "pass_C": cp, "tokens_A": a.get("tokens_to_pass"),
                      "tokens_C": c.get("tokens_to_pass"), "package_imported_C": c.get("package_imported"),
                      "injected": c.get("injected")}, **BOUNDARY}


# ── offline mock builders (mutation-gated self-test; no live calls) ───────────────────────────────────────────
def _fenced(files: dict[str, str]) -> str:
    return "\n".join(f"```python filename={n}\n{c}```" for n, c in files.items())


def _mock_build_good(prompt: str) -> dict[str, Any]:
    return {"code": _fenced(_GENOMES[_DEFAULT_GENOME]["good"]), "completion_tokens": 520, "error": None}


def _mock_build_bad(prompt: str) -> dict[str, Any]:
    return {"code": _fenced(_GENOMES[_DEFAULT_GENOME]["bad"]), "completion_tokens": 300, "error": None}


# a THIN build that COMPOSES the pre-installed verified_primitives (validate_vendor) + minimal store/glue — passes
# only in the package lane (where verified_primitives.py exists); fewer tokens than the full bare build.
_THIN_APP = (
    "import argparse, json\n"
    "from http.server import BaseHTTPRequestHandler, HTTPServer\n"
    "from verified_primitives import validate_vendor\n"
    "_D = {}\n"
    "class H(BaseHTTPRequestHandler):\n"
    "    def _s(self, c, b):\n"
    "        r = json.dumps(b).encode(); self.send_response(c)\n"
    "        self.send_header('Content-Length', str(len(r))); self.end_headers(); self.wfile.write(r)\n"
    "    def do_GET(self):\n"
    "        if self.path == '/health': return self._s(200, {'healthy': True})\n"
    "        if self.path.startswith('/vendors/'):\n"
    "            v = _D.get(self.path.rsplit('/', 1)[-1]); return self._s(200, v) if v else self._s(404, {})\n"
    "        return self._s(404, {})\n"
    "    def do_POST(self):\n"
    "        n = int(self.headers.get('Content-Length', 0) or 0); p = json.loads(self.rfile.read(n) or b'{}')\n"
    "        ok, errs = validate_vendor(p)\n"
    "        if not ok: return self._s(400, {'errors': errs})\n"
    "        new = p['vendor_id'] not in _D; _D.setdefault(p['vendor_id'], p)\n"
    "        return self._s(201 if new else 200, {'vendor_id': p['vendor_id']})\n"
    "    def log_message(self, *a): pass\n"
    "def main():\n"
    "    ap = argparse.ArgumentParser(); ap.add_argument('--port', type=int, default=8000)\n"
    "    a = ap.parse_args(); HTTPServer(('127.0.0.1', a.port), H).serve_forever()\n"
    "if __name__ == '__main__': main()\n"
)


def _mock_build_thin(prompt: str) -> dict[str, Any]:
    return {"code": _fenced({"app.py": _THIN_APP}), "completion_tokens": 210, "error": None}


def self_test() -> bool:
    """Mutation-gated + EXECUTED (offline): the good builder passes the bare lane; a thin builder that COMPOSES
    the extracted primitives passes the package lane at FEWER tokens (=> measured_savings > 0); a bad builder
    FAILS; and the thin build FAILS the bare lane (no module) => the extracted package is load-bearing."""
    # extracted package really certifies at least one primitive from the reference build.
    pkg, names = extracted_primitive_package(_DEFAULT_GENOME)
    assert pkg and "validate_vendor" in names, f"decompose+certify must yield validate_vendor: {names}"

    good = run_ab(_DEFAULT_GENOME, _mock_build_good, repair=1)
    assert good["harness_alone"]["oracle_pass"] is True, f"good builder must pass bare: {good['harness_alone']}"
    assert good["harness_plus_extracted_primitives"]["oracle_pass"] is True, "good build passes package lane too"

    # a builder that emits the FULL build in lane A but a THIN composed build in lane C: both pass, C cheaper.
    def _mixed(prompt: str) -> dict[str, Any]:
        return _mock_build_thin(prompt) if PACKAGE_MODULE in prompt else _mock_build_good(prompt)
    mixed = run_ab(_DEFAULT_GENOME, _mixed, repair=1)
    assert mixed["verdict"] == "measured_savings", f"both lanes must pass -> measured_savings: {mixed['verdict']}"
    assert mixed["tokens_saved"] is not None and mixed["tokens_saved"] > 0, f"reuse must cost fewer tokens: {mixed}"
    assert mixed["harness_plus_extracted_primitives"]["package_imported"] is True, "package lane must import module"

    # the thin build FAILS the bare lane (verified_primitives not installed) -> the extracted package is load-bearing.
    bare_thin = run_lane(_DEFAULT_GENOME, "harness_alone", _mock_build_thin, repair=0, mode="none")
    assert bare_thin["oracle_pass"] is False, "thin composed build must FAIL without the pre-installed module"

    bad = run_ab(_DEFAULT_GENOME, _mock_build_bad, repair=1)
    assert bad["verdict"] == "inconclusive_no_baseline", f"a bad builder proves nothing (both fail): {bad['verdict']}"

    assert BENCHMARK_KIND == "real_project_buildout" and good["candidate"] is True and good["serves_truth"] is False
    print(f"OK buildout_forge_ab self-test: decompose+certify extracts {names}; good builder passes BOTH lanes; a "
          f"thin COMPOSED build passes the package lane at fewer tokens (measured_savings={mixed['tokens_saved']}) "
          f"and FAILS bare without the module (load-bearing); a bad builder is inconclusive_no_baseline; "
          f"benchmark_kind=real_project_buildout; serves_truth=false")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="Both-arms-executed buildout A/B: bare vs extracted-primitives (BOOT+oracle).")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--genome", default=_DEFAULT_GENOME, choices=list(_GENOMES))
    ap.add_argument("--model", default="openai/gpt-oss-120b:free")
    ap.add_argument("--repair", type=int, default=3)
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if args.live:
        pool = _load_pool()
        if not pool:
            print(json.dumps({"skipped": True, "reason": "no OpenRouter pool (.agent/openrouter_keys.txt)"}, indent=2))
            return
        # raw (unstripped) multi-file output + a real buildout-sized token budget
        agent = lambda pr: live_model(pr, pool, args.model, max_tokens=4000, strip=False)  # noqa: E731
        res = run_ab(args.genome, agent, repair=args.repair)
        out_dir = resource(ARTIFACT_DIR_REL)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"{args.genome}_buildout_ab.json").write_text(json.dumps(res, indent=2, sort_keys=True),
                                                                 encoding="utf-8")
        print(json.dumps(res, indent=2))
        return
    self_test()


if __name__ == "__main__":
    main()
