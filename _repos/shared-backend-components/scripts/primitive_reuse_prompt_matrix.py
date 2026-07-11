#!/usr/bin/env python3
"""scripts.primitive_reuse_prompt_matrix — RACE how to build-with-primitives across (prompt variant × model ×
project). The earlier compiled_route lane ("write only the wiring using these signatures") made codestral
re-implement the molecule; that is ONE prompt on ONE model. This module tests MANY ways to present a verified
primitive to a model and MANY models, per the multi-path law — never concluding from a single cell.

Owner (2026-07-09): "this conclusion is not solid ... try more models, more variations, more prompts, more ways to
build with primitives." So: 6 prompt variants (signatures-only · full-source-as-is · import-minimal · usage-example ·
docstring · negative-guarded) × a model zoo × the registered project genomes. Each cell EXECUTES the build against
the hidden oracle and records oracle_pass + input/output tokens + whether the model RE-IMPLEMENTED (the diagnostic).
Deterministic composition (0 tokens, always-pass) is included as the reference row. serves_truth=false.

    python3 scripts/primitive_reuse_prompt_matrix.py --self-test
    python3 scripts/primitive_reuse_prompt_matrix.py --live --models mistral:codestral-latest,openrouter: \
        --genomes semantic_search_engine__stdlib_http__v0 --variants all --repeats 3
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
from typing import Any, Callable  # noqa: E402

from scripts.reuse_experiment_policy import (  # noqa: E402
    CODEX_OPENROUTER_KEY_COUNT,
    DEFAULT_LIVE_REPEATS,
    REPORTING_MIN_N,
)

import scripts.run_large_project_ab as rlp  # noqa: E402
from scripts.run_large_project_ab import _compiled_route_files, _parse_files, _registry  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
BENCHMARK_KIND = "real_project_buildout"
ARTIFACT_DIR_REL = "data/dev-intel/primitive_reuse_prompt_matrix"

_MULTIFILE = ("Return each file in its own fenced block that STARTS with a `# filename: <name>` comment line. "
              "Python stdlib only; the app boots with `python app.py --port N`.")


def _top_level_sigs(mol_files: dict[str, str]) -> str:
    lines = []
    for fn, src in mol_files.items():
        mod = fn[:-3] if fn.endswith(".py") else fn
        for line in src.splitlines():
            if line.startswith(("def ", "class ")):
                lines.append(f"  # from {mod}: {line.strip().rstrip(':')}")
    return "\n".join(lines)


def _factory_docstring(mol_files: dict[str, str]) -> str:
    """Pull the first triple-quoted docstring following a top-level `def make_`.'"""
    for src in mol_files.values():
        lines = src.splitlines()
        for i, line in enumerate(lines):
            if line.startswith("def make_"):
                for j in range(i + 1, min(i + 12, len(lines))):
                    s = lines[j].strip()
                    if s.startswith("'''") or s.startswith('"""'):
                        doc = [s.strip("'\"")]
                        for k in range(j + 1, len(lines)):
                            if lines[k].strip().endswith(("'''", '"""')):
                                doc.append(lines[k].strip().strip("'\""))
                                return " ".join(d for d in doc if d)
                            doc.append(lines[k].strip())
                        return " ".join(doc)
    return ""


def _modnames(mol_files: dict[str, str]) -> str:
    return ", ".join(mol_files)


# ── PROMPT VARIANTS — genuinely different ways to present the SAME verified molecule to the model ──────────────
def _v_signatures_only(goal: str, mol: dict[str, str], entry: str) -> str:
    return (f"Build this project:\n{goal}\n\n{_MULTIFILE}\nThese modules are ALREADY in your workspace: "
            f"{_modnames(mol)}.\nTheir interface:\n{_top_level_sigs(mol)}\nWrite ONLY `{entry}` importing + wiring "
            f"them using EXACTLY these signatures. Emit JUST that one file.\n")


def _v_full_source_asis(goal: str, mol: dict[str, str], entry: str) -> str:
    src = "\n\n".join(f"# ===== {fn} — ALREADY IN YOUR WORKSPACE, TESTED, DO NOT REWRITE =====\n{s}"
                      for fn, s in mol.items())
    return (f"Build this project:\n{goal}\n\n{_MULTIFILE}\nThe following module(s) are ALREADY WRITTEN, TESTED, and "
            f"present in your workspace. DO NOT rewrite, re-implement, or wrap them — import and use them exactly "
            f"as-is:\n\n{src}\n\nNow write ONLY `{entry}`. It must be MINIMAL (a handful of lines): import the "
            f"factory + `run`, build the handler, call `run(Handler)`. Do NOT define your own request-handler "
            f"class.\n")


def _v_import_minimal(goal: str, mol: dict[str, str], entry: str) -> str:
    return (f"Tested module(s) already in your workspace: {_modnames(mol)}. They export a factory that returns a "
            f"ready handler class, plus `run(handler, port=None)`.\nGoal: {goal}\n\n{_MULTIFILE}\nWrite ONLY "
            f"`{entry}` — import the factory, call it to get Handler, then `run(Handler)`. About 5 lines. Do NOT "
            f"re-implement any logic; the module already does everything.\n")


def _v_usage_example(goal: str, mol: dict[str, str], entry: str) -> str:
    factory = next((line.split("(")[0].replace("def ", "") for s in mol.values()
                    for line in s.splitlines() if line.startswith("def make_")), "make_thing")
    mod = next((fn[:-3] for fn in mol if fn.endswith(".py") and fn != entry), "module")
    return (f"Build this project:\n{goal}\n\n{_MULTIFILE}\nModule `{mod}` (already in your workspace) exports "
            f"`{factory}(...)` which RETURNS a ready request-handler class, and `run(handler)`. The CORRECT pattern "
            f"is exactly:\n```python\nfrom {mod} import {factory}, run\nHandler = {factory}(...)\nif __name__ == "
            f"'__main__':\n    run(Handler)\n```\nWrite ONLY `{entry}` following EXACTLY this pattern (fill the "
            f"`...` with the config this project needs). Do NOT write your own handler class.\n")


def _v_docstring(goal: str, mol: dict[str, str], entry: str) -> str:
    doc = _factory_docstring(mol) or "returns a ready handler class; serve with run(handler)."
    return (f"Build this project:\n{goal}\n\n{_MULTIFILE}\nA tested module ({_modnames(mol)}) is in your workspace. "
            f"Its factory docstring: \"{doc}\"\nWrite ONLY `{entry}`: import the factory + `run`, and wire them per "
            f"that docstring. The factory RETURNS the handler — do not build your own.\n")


def _v_negative_guarded(goal: str, mol: dict[str, str], entry: str) -> str:
    return (f"Build this project:\n{goal}\n\n{_MULTIFILE}\nMandatory constraint: a TESTED module ({_modnames(mol)}) "
            f"is already in your workspace and provides a factory returning a ready handler + `run`. You MUST reuse "
            f"it. Your `{entry}` MUST NOT contain: `class `, `BaseHTTPRequestHandler`, `do_GET`, `do_POST`, or any "
            f"HTTP/parsing logic — all of that already exists in the module. Write ONLY the import + factory call + "
            f"`run(Handler)`.\n")


PROMPT_VARIANTS: dict[str, Callable[[str, dict, str], str]] = {
    "signatures_only": _v_signatures_only,
    "full_source_asis": _v_full_source_asis,
    "import_minimal": _v_import_minimal,
    "usage_example": _v_usage_example,
    "docstring": _v_docstring,
    "negative_guarded": _v_negative_guarded,
}

_REIMPL_MARKERS = ("BaseHTTPRequestHandler", "def do_GET", "def do_POST", "class ")


def _reimplemented(entry_src: str) -> bool:
    """Did the model re-implement handler/HTTP logic in the entry instead of just wiring the molecule?"""
    return any(m in entry_src for m in _REIMPL_MARKERS)


def run_cell(genome_id: str, variant: str, agent: Callable[[str], dict]) -> dict[str, Any]:
    """One (genome, variant) build: construct the variant prompt, call the agent, run the HIDDEN oracle.
    Never raises — a model/transport error becomes an error row so one bad cell can't sink the whole matrix."""
    genome, run_buildout = _registry()[genome_id]
    mol_files, names = _compiled_route_files(genome)
    entry = genome.get("solution_file", "app.py")
    prompt = PROMPT_VARIANTS[variant](genome["goal"], mol_files, entry)
    try:
        gen = agent(prompt)
        input_source = (gen.get("input_token_source") or
                        ("provider_unverified" if (gen.get("input_tokens", 0) or 0) > 0 else "missing"))
        output_source = (gen.get("output_token_source") or
                         ("provider_unverified" if (gen.get("completion_tokens", 0) or 0) > 0 else "missing"))
        if gen.get("error"):
            # Transport/provider failures did not execute the benchmark.  Keep a
            # diagnostic attempt, but use oracle_pass=None so the grid excludes
            # it from pass-rate denominators and retries the cell on resume.
            return {"genome": genome_id, "variant": variant, "oracle_pass": None,
                    "input_tokens": gen.get("input_tokens", 0) or 0,
                    "output_tokens": gen.get("completion_tokens", 0) or 0,
                    "input_token_source": input_source, "output_token_source": output_source,
                    "reimplemented": None, "entry_chars": 0, "oracle_checks": {},
                    "error": str(gen.get("error"))[:140]}
        files = {k: v for k, v in _parse_files(gen.get("code") or "").items() if k not in names}
        # keep only the entry the model was asked to write; mount the verified molecule verbatim
        written = ({entry: files.get(entry, files.get("app.py", ""))}
                   if (entry in files or "app.py" in files) else files)
        res = run_buildout(genome_id, written or {entry: ""}, lane=f"reuse:{variant}", extra_files=mol_files)
        entry_src = written.get(entry, "")
        return {"genome": genome_id, "variant": variant, "oracle_pass": bool(res["oracle_pass"]),
                "input_tokens": gen.get("input_tokens", 0) or 0, "output_tokens": gen.get("completion_tokens", 0) or 0,
                "input_token_source": input_source, "output_token_source": output_source,
                "reimplemented": _reimplemented(entry_src), "entry_chars": len(entry_src),
                "oracle_checks": res.get("oracle_checks") or {}, "error": gen.get("error")}
    except Exception as exc:  # noqa: BLE001  ANY error (transport/parse/oracle) -> error row; one bad cell can't sink the grid
        return {"genome": genome_id, "variant": variant, "oracle_pass": None, "input_tokens": 0,
                "output_tokens": 0, "input_token_source": "missing", "output_token_source": "missing",
                "reimplemented": None, "entry_chars": 0, "oracle_checks": {},
                "error": f"cell:{exc}"[:140]}


def race(genome_id: str, agent: Callable[[str], dict], variants: list[str], repeats: int = 1) -> list[dict[str, Any]]:
    rows = []
    for v in variants:
        for _ in range(repeats):
            rows.append(run_cell(genome_id, v, agent))
    return rows


def summarize(rows: list[dict[str, Any]]) -> dict[str, Any]:
    """Aggregate executed cells; transport errors remain retryable attempts outside denominators."""
    by: dict[str, list] = {}
    for r in rows:
        by.setdefault(r["variant"], []).append(r)
    out = {}
    for v, rs in by.items():
        completed = [r for r in rs if not r.get("error") and isinstance(r.get("oracle_pass"), bool)]
        reimpls = [r["reimplemented"] for r in completed if isinstance(r.get("reimplemented"), bool)]
        n = len(completed)
        reportable = n >= REPORTING_MIN_N
        out[v] = {"n": n, "n_attempts": len(rs), "n_retryable_errors": len(rs) - n,
                  "reportable": reportable, "headline_eligible": False,
                  "status": ("reportable per-variant sample; not a paired savings headline" if reportable else
                             f"insufficient n (<{REPORTING_MIN_N})"),
                  "pass_rate": round(sum(r["oracle_pass"] for r in completed) / n, 3) if n else None,
                  "reimpl_rate": round(sum(reimpls) / len(reimpls), 3) if reimpls else None,
                  "mean_out_tokens": round(sum(r["output_tokens"] for r in completed) / n, 1) if n else None,
                  "mean_entry_chars": round(sum(r["entry_chars"] for r in completed) / n, 1) if n else None}
    return out


# ── mock agents for the self-test (no network) ────────────────────────────────────────────────────────────────
def _mock_good_agent(genome_id: str) -> Callable[[str], dict]:
    genome, _ = _registry()[genome_id]
    entry = genome.get("solution_file", "app.py")
    good_entry = genome["good"][entry]

    def agent(prompt: str) -> dict:
        return {"code": f"# filename: {entry}\n```python\n{good_entry}\n```",
                "completion_tokens": max(1, len(good_entry) // 4), "input_tokens": max(1, len(prompt) // 4),
                "error": None}
    return agent


def _mock_reimpl_agent(genome_id: str) -> Callable[[str], dict]:
    """A model that ignores the molecule and writes a broken re-implementation (the observed failure mode)."""
    genome, _ = _registry()[genome_id]
    entry = genome.get("solution_file", "app.py")
    broken = ("import json\nfrom http.server import BaseHTTPRequestHandler, HTTPServer\n"
              "class H(BaseHTTPRequestHandler):\n    def do_GET(self):\n        self.send_response(200)\n"
              "        self.end_headers()\n")

    def agent(prompt: str) -> dict:
        return {"code": f"# filename: {entry}\n```python\n{broken}\n```",
                "completion_tokens": 200, "input_tokens": max(1, len(prompt) // 4), "error": None}
    return agent


def self_test() -> bool:
    """Mutation-gated + REAL: (1) all 6 variant prompts build for a real genome + are DISTINCT; (2) with a GOOD
    mock agent (writes the reference wiring) EVERY variant passes the real oracle; (3) with a RE-IMPLEMENTING mock
    agent every variant FAILS and is flagged reimplemented=True (the diagnostic works); (4) the summary aggregates."""
    gid = "semantic_search_engine__stdlib_http__v0"
    genome, _ = _registry()[gid]
    mol, _names = _compiled_route_files(genome)
    entry = genome.get("solution_file", "app.py")
    prompts = {v: PROMPT_VARIANTS[v](genome["goal"], mol, entry) for v in PROMPT_VARIANTS}
    assert len(set(prompts.values())) == len(PROMPT_VARIANTS), "variant prompts must be DISTINCT"
    assert all(len(p) > 50 for p in prompts.values())

    good_rows = race(gid, _mock_good_agent(gid), list(PROMPT_VARIANTS))
    assert all(r["oracle_pass"] for r in good_rows), f"good wiring must pass EVERY variant: {[r['variant'] for r in good_rows if not r['oracle_pass']]}"
    assert all(not r["reimplemented"] for r in good_rows), "good wiring must not be flagged reimplemented"

    reimpl_rows = race(gid, _mock_reimpl_agent(gid), list(PROMPT_VARIANTS))
    assert all(not r["oracle_pass"] for r in reimpl_rows), "a broken re-implementation must FAIL every variant"
    assert all(r["reimplemented"] for r in reimpl_rows), "re-implementation must be DETECTED for every variant"

    summ = summarize(good_rows)
    assert all(summ[v]["pass_rate"] == 1.0 for v in PROMPT_VARIANTS)

    transport_row = run_cell(
        gid, next(iter(PROMPT_VARIANTS)),
        lambda _prompt: {"code": "", "completion_tokens": 0, "input_tokens": 0, "error": "http503"},
    )
    transport_summary = summarize([transport_row])[transport_row["variant"]]
    assert transport_summary["n"] == 0 and transport_summary["n_retryable_errors"] == 1
    assert transport_summary["pass_rate"] is None

    print(f"OK primitive_reuse_prompt_matrix self-test: {len(PROMPT_VARIANTS)} DISTINCT prompt variants "
          f"({', '.join(PROMPT_VARIANTS)}) build for real genomes; GOOD-wiring mock passes EVERY variant's real "
          f"oracle (reimpl=0); RE-IMPLEMENTING mock FAILS every variant AND is detected (reimpl flagged); summary "
          f"aggregates executed pass/reimpl/token rates while preserving transport errors outside denominators. "
          f"Ready to race real models. serves_truth=false")
    return True


def _resolve_models(spec: str) -> list[tuple[str, str]]:
    """'mistral:codestral-latest,openrouter:' -> [(provider, model_or_default)]. Empty model = provider default."""
    out = []
    for part in spec.split(","):
        part = part.strip()
        if not part:
            continue
        provider, _, model = part.partition(":")
        base_url, keyfile, default_model = rlp._PROVIDERS[provider]
        out.append((provider, model or default_model))
    return out


def live_matrix(genome_ids: list[str], models: list[tuple[str, str]], variants: list[str],
                repeats: int, incremental_path: Path | None = None) -> dict[str, Any]:
    """Race the full (model × project × variant) grid. Robust: per-cell errors are captured, results written
    INCREMENTALLY after every cell so a late crash never loses the grid."""
    from scripts.primitive_token_savings_ab import live_model  # noqa: PLC0415
    matrix: dict[str, Any] = {}

    def _flush() -> dict[str, Any]:
        rep = {"record_type": "primitive_reuse_prompt_matrix", "benchmark_kind": BENCHMARK_KIND,
               "matrix": matrix, **BOUNDARY}
        if incremental_path is not None:
            incremental_path.write_text(json.dumps(rep, indent=2, sort_keys=True), encoding="utf-8")
        return rep

    for provider, model in models:
        base_url, keyfile, _ = rlp._PROVIDERS[provider]
        pool = rlp._load_key_file(keyfile) if keyfile else rlp._load_key_file(f"{provider}_keys.txt")
        if provider == "openrouter":
            pool = pool[:CODEX_OPENROUTER_KEY_COUNT]

        def agent(prompt: str, _b=base_url, _m=model, _p=pool) -> dict:
            return live_model(prompt, _p, _m, max_tokens=16000, strip=False, base_url=_b)
        for gid in genome_ids:
            rows: list[dict[str, Any]] = []
            for v in variants:
                for _ in range(repeats):
                    rows.append(run_cell(gid, v, agent))
                    matrix[f"{provider}:{model}|{gid}"] = {"summary": summarize(rows), "rows": rows}
                    _flush()
    return _flush()


def main() -> None:
    ap = argparse.ArgumentParser(description="Race prompt-variant × model × project for building-with-primitives.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--models", default="mistral:codestral-latest")
    ap.add_argument("--genomes", default="semantic_search_engine__stdlib_http__v0")
    ap.add_argument("--variants", default="all")
    ap.add_argument("--repeats", type=int, default=DEFAULT_LIVE_REPEATS)
    args = ap.parse_args()
    if args.self_test:
        raise SystemExit(0 if self_test() else 1)
    if args.live:
        variants = list(PROMPT_VARIANTS) if args.variants == "all" else args.variants.split(",")
        out = resource(ARTIFACT_DIR_REL); out.mkdir(parents=True, exist_ok=True)
        rep = live_matrix(args.genomes.split(","), _resolve_models(args.models), variants, args.repeats,
                          incremental_path=out / "matrix.json")
        for cell, data in rep["matrix"].items():
            print(f"\n== {cell} ==")
            for v, s in data["summary"].items():
                print(f"  {v:18} pass={s['pass_rate']} reimpl={s['reimpl_rate']} out_tok={s['mean_out_tokens']}")
        return
    ap.print_help()


if __name__ == "__main__":
    main()
