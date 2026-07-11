#!/usr/bin/env python3
"""scripts.run_large_project_ab — the LARGE-project both-arms-EXECUTED A/B with a CERTIFIED COVERAGE PACK and
input+output token netting. A real model BUILDS a large multi-module project (the 11-file ops-API, the 10-module
ETL DAG, ...) twice — bare vs the certified coverage pack pre-installed — and BOTH must BOOT/RUN and pass the
genome's HIDDEN oracle. Savings = real tokens-to-pass (output AND total = input+output), reported as a
DISTRIBUTION over n runs, never a cherry-picked run (candidate-only).

Owner (2026-07-09): tiny 40-line services + one 10-line primitive gave noisy ~9% savings; the next proof must be
on LARGE tasks (20+ files / hundreds of lines) with a real COVERAGE pack and netted input+output tokens. This
runner is that — it resolves the LARGE genomes (buildout_forge_large / _pipeline) + injects the certified
`project_coverage_primitive_pack` as an importable module. BENCHMARK_KIND=real_project_buildout; serves_truth=false.

    python3 scripts/run_large_project_ab.py --self-test
    python3 scripts/run_large_project_ab.py --live --genome backoffice_ops_api__stdlib_http__v0 --repeats 8
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
import statistics as _stats  # noqa: E402
from typing import Any, Callable  # noqa: E402

from scripts.primitive_token_savings_ab import _load_pool, live_model  # noqa: E402
from scripts.project_coverage_primitive_pack import coverage_package_source, _PRIMITIVES as _COV  # noqa: E402
from scripts.reuse_experiment_policy import (  # noqa: E402
    CODEX_OPENROUTER_KEY_COUNT,
    DEFAULT_LIVE_REPEATS,
)

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
BENCHMARK_KIND = "real_project_buildout"  # both lanes BUILD/BOOT + pass the genome's hidden oracle; real tokens
ARTIFACT_DIR_REL = "data/dev-intel/buildout_forge"
PACKAGE_MODULE = "verified_primitives"
# provider -> (OpenAI-compatible base_url, .agent keyfile or None=OpenRouter pool, default model). Probed working
# frontier code lanes: ollama qwen3-coder:480b, mistral codestral, sambanova llama-70b.
_PROVIDERS: dict[str, tuple] = {
    "openrouter": ("https://openrouter.ai/api/v1/chat/completions", None, "openai/gpt-oss-120b:free"),
    "mistral": ("https://api.mistral.ai/v1/chat/completions", "mistral_keys.txt", "codestral-latest"),
    "ollama": ("https://ollama.com/v1/chat/completions", "ollama_keys.txt", "qwen3-coder:480b"),
    "sambanova": ("https://api.sambanova.ai/v1/chat/completions", "sambanova_keys.txt", "Meta-Llama-3.3-70B-Instruct"),
    "together": ("https://api.together.xyz/v1/chat/completions", "together_keys.txt", "Qwen/Qwen2.5-Coder-32B-Instruct"),
    "groq": ("https://api.groq.com/openai/v1/chat/completions", "groq_keys.txt", "moonshotai/kimi-k2-instruct"),
    "cerebras": ("https://api.cerebras.ai/v1/chat/completions", "cerebras_keys.txt", "qwen-3-coder-480b"),
    "nvidia_nim": ("https://integrate.api.nvidia.com/v1/chat/completions", "nvidia_nim_keys.txt",
                   "qwen/qwen2.5-coder-32b-instruct"),
    # FREE lanes: GitHub Models (free via the owner's GITHUB_TOKEN) + Gemini (free tier, 1M-token context).
    "github_models": ("https://models.github.ai/inference/chat/completions", "github_token.txt", "openai/gpt-4o"),
    "gemini": ("https://generativelanguage.googleapis.com/v1beta/openai/chat/completions", "gemini_keys.txt",
               "gemini-2.0-flash"),
}
_FILE_BLOCK_RE = re.compile(r"```(?:python|py)?(?:[ \t]+filename=([^\s`]+))?\s*\n(.*?)```", re.DOTALL)
_MULTIFILE_CONTRACT = (
    "OUTPUT CONTRACT: respond ONLY with complete runnable files in fenced blocks of the form\n"
    "```python filename=<relative/path.py>\\n<code>\\n``` . Emit EVERY file the project needs. The ENTRY module "
    "MUST be at the repository ROOT (app.py for services, run.py for pipelines) and boot/run exactly as the goal "
    "states; helper modules MAY live in subpackages that the entry imports. Python stdlib + sqlite3 only (no pip). "
    "No prose outside code blocks, no TODOs."
)


def _load_key_file(fname: str) -> list[str]:
    """Load a gitignored .agent/<fname> key pool (one key per line; ignores comments). Never logs values."""
    for p in [_here_boot, *_here_boot.parents]:
        f = p / ".agent" / fname
        if f.exists():
            return [l.strip() for l in f.read_text().splitlines() if l.strip() and not l.strip().startswith("#")]
    return []


def _registry() -> dict[str, tuple[dict, Callable]]:
    import scripts.buildout_forge as _bf  # noqa: PLC0415
    import scripts.buildout_forge_large as _bl  # noqa: PLC0415
    import scripts.buildout_forge_pipeline as _bp  # noqa: PLC0415
    import scripts.http_scaffold_macro as _hs  # noqa: PLC0415  macro-primitive scaffolded genome
    import scripts.macro_crud_service as _mc  # noqa: PLC0415  CRUD-factory macro-primitive genome (lane D)
    import scripts.buildout_forge_automation as _ba  # noqa: PLC0415  signed-webhook integration-worker (molecule reuse)
    import scripts.buildout_forge_search_rag as _sr  # noqa: PLC0415  semantic search / labeling / RAG large projects
    reg: dict[str, tuple[dict, Callable]] = {}
    for mod in (_bf, _bl, _bp, _hs, _mc, _ba, _sr):
        for gid, genome in mod._GENOMES.items():
            reg[gid] = (genome, mod.run_buildout)
    return reg


def _parse_files(text: str) -> dict[str, str]:
    files: dict[str, str] = {}
    for fname, code in _FILE_BLOCK_RE.findall(text or ""):
        files[(fname or "app.py").strip()] = code
    return files


def _coverage_files(genome: dict) -> tuple[dict[str, str], list[str]]:
    """Relevance-ROUTED injection: inject only the coverage primitives whose name-tokens overlap the genome goal
    (+ declared targets) — measured: dumping the whole pack into a simple task REGRESSES it. This scales
    naturally (few relevant for a small task, many for a complex one) instead of a fixed dump."""
    import re
    goal = (str(genome.get("goal", "")) + " " + " ".join(genome.get("primitive_targets", []))).lower()
    gpref = {g[:4] for g in re.findall(r"[a-z]{3,}", goal)}
    names = []
    for s in _COV:
        ptoks = re.findall(r"[a-z]{3,}", s["fn"].__name__)
        if any(p[:4] in gpref for p in ptoks):
            names.append(s["fn"].__name__)
    if not names:  # fallback: the generic http/validation helpers every service needs
        names = [s["fn"].__name__ for s in _COV if s["family"] in ("http", "validation")]
    return {f"{PACKAGE_MODULE}.py": coverage_package_source(names)}, names


def _compiled_route_files(genome: dict) -> tuple[dict[str, str], list[str]]:
    """Compiled-route: provide the build's VERIFIED helper modules VERBATIM (0 generated tokens); the model writes
    ONLY the thin entry file that wires them, instead of regenerating the whole app. This is where token savings
    must come from — the model outputs materially LESS AND has less to get right (both failure modes at once)."""
    good = genome["good"]
    entry = genome.get("solution_file", "app.py")
    provided = {fn: src for fn, src in good.items() if fn != entry}
    return provided, sorted(provided.keys())


def _prompt(genome: dict, injected: list[str], prior_fail: dict | None, mode: str) -> str:
    p = f"Build this project:\n{genome['goal']}\n\n{_MULTIFILE_CONTRACT}\n"
    if mode == "coverage" and injected:
        p += (f"\nThe module `{PACKAGE_MODULE}` is ALREADY INSTALLED in your workspace with these CERTIFIED, "
              f"verified-correct helpers: {', '.join(injected)}.\nImport the ones you need "
              f"(`from {PACKAGE_MODULE} import <name>`) and COMPOSE them — do NOT reimplement their logic.\n")
    if mode == "compiled_route" and injected:
        entry = genome.get("solution_file", "app.py")
        good = genome.get("good", {})
        sigs = []  # show only the PUBLIC interface (TOP-LEVEL def/class) — not internal impl methods
        for m in injected:
            mod = m[:-3] if m.endswith(".py") else m
            for line in good.get(m, "").splitlines():
                if line.startswith(("def ", "class ")):  # top-level only (no leading indent = not an internal method)
                    sigs.append(f"  # from {mod}: {line.strip().rstrip(':')}")
        interface = "\n".join(sigs)
        p += (f"\nThese modules are ALREADY PROVIDED + VERIFIED in your workspace (import them, do NOT rewrite). "
              f"Their exact interface:\n{interface}\nWrite ONLY `{entry}` — `from <module> import <name>` and wire "
              f"the entry/routing using EXACTLY these signatures. Emit JUST that one file (nothing else).\n")
    if prior_fail:
        failed = [k for k, v in prior_fail.items() if not v]
        p += f"\nYour previous build FAILED these hidden checks: {failed}. Fix and resend ALL files.\n"
    return p


def run_lane(genome_id: str, lane: str, agent: Callable[[str], dict], repair: int, mode: str) -> dict[str, Any]:
    genome, run_buildout = _registry()[genome_id]
    if mode == "coverage":
        extra, injected = _coverage_files(genome)
    elif mode == "compiled_route":
        extra, injected = _compiled_route_files(genome)
    else:
        extra, injected = {}, []
    entry = genome.get("solution_file", "app.py")
    out_tok = in_tok = 0
    prior = None
    imported = False
    nfiles = 0
    last_agent_error: str | None = None
    executed_turns = 0
    transport_errors = 0
    max_transport_errors = repair + 1
    input_token_sources: list[str] = []
    output_token_sources: list[str] = []

    def token_source(gen: dict[str, Any], field: str, declared_field: str) -> str:
        declared = gen.get(declared_field)
        if declared:
            return str(declared)
        return "provider_unverified" if (gen.get(field, 0) or 0) > 0 else "missing"

    def accounting_fields() -> dict[str, str]:
        return {
            "input_token_source": ("provider" if input_token_sources
                                   and all(source == "provider" for source in input_token_sources)
                                   else "mixed_or_unverified"),
            "output_token_source": ("provider" if output_token_sources
                                    and all(source == "provider" for source in output_token_sources)
                                    else "mixed_or_unverified"),
        }

    while executed_turns <= repair:
        gen = agent(_prompt(genome, injected, prior, mode))
        out_tok += gen.get("completion_tokens", 0) or 0
        in_tok += gen.get("input_tokens", 0) or 0
        input_token_sources.append(token_source(gen, "input_tokens", "input_token_source"))
        output_token_sources.append(token_source(gen, "completion_tokens", "output_token_source"))
        last_agent_error = str(gen.get("error") or "") or None
        if not last_agent_error and not str(gen.get("code") or gen.get("text") or "").strip():
            last_agent_error = "response_missing_content"
        if last_agent_error:
            # A provider/rate-limit/response-schema failure is not an executed
            # project failure and does not consume the executed repair budget.
            # A bounded transport budget prevents a dead endpoint looping
            # forever; exhaustion leaves the whole logical cell retryable.
            transport_errors += 1
            if transport_errors >= max_transport_errors:
                return {"lane": lane, "oracle_pass": None, "output_tokens": out_tok, "input_tokens": in_tok,
                        "total_tokens": in_tok + out_tok, "repair_turns": executed_turns,
                        "n_files": nfiles, "package_imported": imported, "injected_count": len(injected),
                        "checks": prior, "error": last_agent_error, **accounting_fields(), **BOUNDARY}
            continue
        turn = executed_turns
        executed_turns += 1
        last_agent_error = None
        files = _parse_files(gen.get("code") or gen.get("text") or "")
        if mode == "compiled_route":  # verbatim provided modules WIN — drop any the model re-emitted
            files = {k: v for k, v in files.items() if k not in injected}
        nfiles = len(files)
        if not any(k in files for k in (entry, "app.py", "run.py")):
            prior = {"emitted_entry": False}
            continue
        imported = any(PACKAGE_MODULE in c for c in files.values())
        receipt = run_buildout(genome_id, files, lane=lane, extra_files=extra)
        if receipt.get("oracle_pass"):
            return {"lane": lane, "oracle_pass": True, "output_tokens": out_tok, "input_tokens": in_tok,
                    "total_tokens": in_tok + out_tok, "repair_turns": turn, "n_files": nfiles,
                    "package_imported": imported, "injected_count": len(injected),
                    "checks": receipt.get("oracle_checks"), "error": None, **accounting_fields(), **BOUNDARY}
        prior = receipt.get("oracle_checks") or {}
    return {"lane": lane, "oracle_pass": False, "output_tokens": out_tok, "input_tokens": in_tok,
            "total_tokens": in_tok + out_tok, "repair_turns": repair, "n_files": nfiles,
            "package_imported": imported, "injected_count": len(injected), "checks": prior,
            "error": None, **accounting_fields(), **BOUNDARY}


def run_ab(genome_id: str, agent: Callable[[str], dict], repair: int = 3,
           treatment: str = "coverage") -> dict[str, Any]:
    a = run_lane(genome_id, "harness_alone", agent, repair, "none")
    lane_name = "harness_plus_" + ("coverage_pack" if treatment == "coverage" else "compiled_route")
    c = run_lane(genome_id, lane_name, agent, repair, treatment)
    ap, cp = a.get("oracle_pass"), c.get("oracle_pass")
    if ap and cp:
        verdict = "measured_savings"
        out_saved, total_saved = a["output_tokens"] - c["output_tokens"], a["total_tokens"] - c["total_tokens"]
    elif cp and not ap:
        verdict, out_saved, total_saved = "capability_lift", None, None
    elif ap and not cp:
        verdict, out_saved, total_saved = "treatment_regressed", None, None
    else:
        verdict, out_saved, total_saved = "inconclusive_no_baseline", None, None
    return {"record_type": "large_project_ab", "genome_id": genome_id, "benchmark_kind": BENCHMARK_KIND,
            "treatment_mode": treatment, "treatment_lane": lane_name,
            "harness_alone": a, "harness_plus_treatment": c, "verdict": verdict,
            "output_tokens_saved": out_saved, "total_tokens_saved": total_saved, **BOUNDARY}


def run_distribution(genome_id: str, agent: Callable[[str], dict], repeats: int, repair: int = 3,
                     treatment: str = "coverage") -> dict[str, Any]:
    """n runs -> a DISTRIBUTION (never a cherry-picked run). Reports mean/median/range on BOTH output and total
    tokens, and how often each verdict occurred. Honest: total-token savings nets the treatment's input cost."""
    runs = [run_ab(genome_id, agent, repair, treatment) for _ in range(repeats)]
    both_pass = [r for r in runs if r["verdict"] == "measured_savings"]
    out_saved = [r["output_tokens_saved"] for r in both_pass]
    total_saved = [r["total_tokens_saved"] for r in both_pass]
    verdicts: dict[str, int] = {}
    for r in runs:
        verdicts[r["verdict"]] = verdicts.get(r["verdict"], 0) + 1

    def _dist(xs: list) -> dict[str, Any]:
        if not xs:
            return {"n": 0}
        return {"n": len(xs), "mean": round(_stats.mean(xs), 1), "median": _stats.median(xs),
                "min": min(xs), "max": max(xs), "stdev": round(_stats.pstdev(xs), 1) if len(xs) > 1 else 0,
                "n_positive": sum(1 for x in xs if x > 0), "n_negative": sum(1 for x in xs if x < 0)}
    return {"record_type": "large_project_ab_distribution", "genome_id": genome_id, "benchmark_kind": BENCHMARK_KIND,
            "treatment_mode": treatment, "n_runs": repeats, "n_both_pass": len(both_pass), "verdict_counts": verdicts,
            "output_tokens_saved": _dist(out_saved), "total_tokens_saved": _dist(total_saved),
            "runs": runs, **BOUNDARY}


# ── offline mocks: the genome's OWN good/bad builds prove the runner measures a LARGE oracle correctly ─────────
def _fenced(files: dict[str, str]) -> str:
    return "\n".join(f"```python filename={n}\n{c}```" for n, c in files.items())


def _mock_good(genome_id: str) -> Callable[[str], dict]:
    genome = _registry()[genome_id][0]
    return lambda prompt: {"code": _fenced(genome["good"]), "completion_tokens": 4200, "input_tokens": 900,
                           "error": None}


def _mock_bad(genome_id: str) -> Callable[[str], dict]:
    genome = _registry()[genome_id][0]
    return lambda prompt: {"code": _fenced(genome["bad"]), "completion_tokens": 800, "input_tokens": 700,
                           "error": None}


def self_test() -> bool:
    """Mutation-gated + EXECUTED (offline): the genome's own GOOD build passes BOTH lanes of the LARGE hidden
    oracle; the BAD build fails -> inconclusive; input+output tokens are netted; the coverage package is real."""
    gid = "backoffice_ops_api__stdlib_http__v0"
    cov_files, cov_names = _coverage_files(_registry()[gid][0])  # relevance-routed for this genome
    assert cov_files and len(cov_names) >= 12, f"the complex ops-API must route in many primitives: {len(cov_names)}"

    good = run_ab(gid, _mock_good(gid), repair=1)
    assert good["harness_alone"]["oracle_pass"] is True, f"good build must pass the LARGE bare oracle: {good['harness_alone']['checks']}"
    assert good["harness_plus_treatment"]["oracle_pass"] is True, "good build passes the treatment lane too"
    assert good["harness_alone"]["total_tokens"] == good["harness_alone"]["input_tokens"] + good["harness_alone"]["output_tokens"]
    assert good["verdict"] == "measured_savings", good["verdict"]

    bad = run_ab(gid, _mock_bad(gid), repair=1)
    assert bad["verdict"] == "inconclusive_no_baseline", f"a bad builder proves nothing: {bad['verdict']}"

    dist = run_distribution(gid, _mock_good(gid), repeats=2, repair=0)
    assert dist["n_both_pass"] == 2 and dist["output_tokens_saved"]["n"] == 2

    bad_then_transport_calls = {"n": 0}
    bad_agent = _mock_bad(gid)

    def bad_then_transport(prompt: str) -> dict:
        bad_then_transport_calls["n"] += 1
        if bad_then_transport_calls["n"] == 1:
            return bad_agent(prompt)
        return {"code": "", "completion_tokens": 0, "input_tokens": 0, "error": "http503"}

    interrupted = run_lane(gid, "without", bad_then_transport, repair=1, mode="none")
    assert interrupted["oracle_pass"] is None and interrupted["error"] == "http503", interrupted
    assert bad_then_transport_calls["n"] == 3, "transport failures must not consume the executed repair budget"

    empty = run_lane(
        gid, "without",
        lambda _prompt: {"code": "", "completion_tokens": 0, "input_tokens": 10, "error": None},
        repair=0, mode="none",
    )
    assert empty["oracle_pass"] is None and empty["error"] == "response_missing_content", empty

    assert BENCHMARK_KIND == "real_project_buildout" and good["serves_truth"] is False
    n_checks = len(good["harness_alone"]["checks"])
    print(f"OK run_large_project_ab self-test: coverage pack injects {len(cov_names)} certified primitives; the "
          f"11-file ops-API GOOD build passes BOTH lanes of the LARGE hidden oracle ({n_checks} checks), input+"
          f"output tokens netted; a BAD build -> inconclusive_no_baseline; distribution over n runs; "
          f"interrupted repair + empty responses stay retryable; benchmark_kind=real_project_buildout; "
          f"serves_truth=false")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="Large-project A/B: bare vs certified coverage pack (executed, netted).")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--genome", default="backoffice_ops_api__stdlib_http__v0")
    ap.add_argument("--provider", default="openrouter", choices=list(_PROVIDERS))
    ap.add_argument("--model", default=None, help="defaults per provider (see _PROVIDERS)")
    ap.add_argument("--repeats", type=int, default=DEFAULT_LIVE_REPEATS)
    ap.add_argument("--repair", type=int, default=3)
    ap.add_argument("--treatment", default="coverage", choices=["coverage", "compiled_route"])
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if args.live:
        if args.genome not in _registry():
            print(json.dumps({"error": "unknown genome", "have": list(_registry())}, indent=2)); return
        base_url, keyfile, default_model = _PROVIDERS[args.provider]
        pool = _load_pool() if keyfile is None else _load_key_file(keyfile)
        if args.provider == "openrouter":
            pool = pool[:CODEX_OPENROUTER_KEY_COUNT]
        model = args.model or default_model
        if not pool:
            print(json.dumps({"skipped": True, "reason": f"no {args.provider} key pool"}, indent=2)); return
        # LARGE multi-module builds need a big single-turn budget — 6000 truncated the 11-module ops-API mid-file
        # (non-booting builds); 16000 lets the full build fit in one response.
        agent = lambda pr: live_model(pr, pool, model, max_tokens=16000, strip=False, base_url=base_url)  # noqa: E731
        res = run_distribution(args.genome, agent, repeats=args.repeats, repair=args.repair, treatment=args.treatment)
        out_dir = resource(ARTIFACT_DIR_REL)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"{args.genome}_{args.treatment}_ab_distribution.json").write_text(
            json.dumps(res, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps({k: res[k] for k in ("genome_id", "treatment_mode", "n_runs", "n_both_pass",
                                              "verdict_counts", "output_tokens_saved", "total_tokens_saved")}, indent=2))
        return
    self_test()


if __name__ == "__main__":
    main()
