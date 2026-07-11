#!/usr/bin/env python3
"""scripts.buildout_agent_backends — the DATA-DRIVEN ZOO of agent/harness backend LANES that can DRIVE a
large-project buildout (the top-down BuildoutForge loop). The multi-path law (law §1) made literal for the
*driver* of a buildout: each backend is ONE ROW in `_BACKENDS`; adding a lane is a row, never a rewrite.

Backends enumerated: `direct_api` (the OpenRouter key pool, via `scripts.primitive_token_savings_ab.live_model`
+ `_load_pool`), the CLI harnesses `codex` / `aider` / `opencode` / `clawcodex` / `qwen_code`, and the Python
SDK lanes `openai_agents_sdk` / `langgraph`. `probe_backends()` REALLY probes what is installed HERE
(`shutil.which` for CLIs, `importlib.util.find_spec` for SDKs, a non-empty `_load_pool()` for the api pool) and
`run_cli_backend()` actually invokes an AVAILABLE CLI non-interactively over `subprocess.run` in a workspace.

COMPLEMENT, not duplicate, of `scripts/harness_bakeoff_spec.probe_availability()`: that module scores a
model x harness x runtime x task benchmark MATRIX (with local-runtime port checks + provider-key presence);
THIS module is the runnable BACKEND-LANE selector a buildout picks to actually generate code, and it adds the
Python-SDK lanes + a real non-interactive CLI runner that the bakeoff spec does not carry.

BENCHMARK_KIND=real — the availability probe is a real measured quantity (what is installed on this host), not a
proxy estimate. Everything here is candidate=true / serves_truth=false; no key value is ever returned or printed
(only a count), and an unavailable backend NEVER raises — it returns a skipped/errored receipt.

    python3 scripts/buildout_agent_backends.py --self-test
    python3 scripts/buildout_agent_backends.py --probe          # print the live availability matrix
"""
from __future__ import annotations

import sys
from pathlib import Path

# ── substrate-root bootstrap (sentinel; mirrors scripts/buildout_forge.py) ───────────────────────────────────
_here_boot = Path(__file__).resolve()
_sbc_boot = next((q for q in _here_boot.parents if (q / "scripts" / "_repo_paths.py").exists()),
                 _here_boot.parents[1])
if str(_sbc_boot) not in sys.path:
    sys.path.insert(0, str(_sbc_boot))
from scripts._repo_paths import install as _install_code_roots, resource  # noqa: E402

_install_code_roots()

import argparse  # noqa: E402
import importlib.util  # noqa: E402
import json  # noqa: E402
import shutil  # noqa: E402
import subprocess  # noqa: E402  (the NON-INTERACTIVE CLI runner — a real harness, not model-generated code)
import time  # noqa: E402
from typing import Any, Callable  # noqa: E402

from scripts.primitive_token_savings_ab import _load_pool, live_model  # noqa: E402,F401  (api-pool lane seam)

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
BENCHMARK_KIND = "real"  # no_proxy_gate: the availability probe is a REAL measured quantity (installed-here)
ARTIFACT_DIR_REL = "data/dev-intel/buildout_agent_backends"

# ── the backend ZOO: one row per lane; add a lane by adding a row (never a rewrite — the multi-path law). ─────
#    `kind` selects the probe: cli -> shutil.which(any binary) · sdk -> importlib.util.find_spec(module) ·
#    api_pool -> a non-empty _load_pool(). `probe` is the concrete arg the probe consumes (binary candidates /
#    module name / the "pool" sentinel). `live_model` is imported so the api-pool lane can actually drive a call.
_BACKENDS: dict[str, dict[str, Any]] = {
    "direct_api": {"name": "direct_api", "kind": "api_pool", "probe": "pool",
                   "note": "OpenRouter key pool -> scripts.primitive_token_savings_ab.live_model"},
    "codex": {"name": "codex", "kind": "cli", "probe": ["codex"]},
    "aider": {"name": "aider", "kind": "cli", "probe": ["aider"]},
    "opencode": {"name": "opencode", "kind": "cli", "probe": ["opencode"]},
    "clawcodex": {"name": "clawcodex", "kind": "cli", "probe": ["clawcodex", "claw"]},
    "qwen_code": {"name": "qwen_code", "kind": "cli", "probe": ["qwen", "qwen-code"]},
    "openai_agents_sdk": {"name": "openai_agents_sdk", "kind": "sdk", "probe": "agents"},
    "langgraph": {"name": "langgraph", "kind": "sdk", "probe": "langgraph"},
}

# ── non-interactive invocation recipes per CLI lane (best-effort flags; extend by adding a row). ─────────────
#    argv builder is (resolved_binary, prompt) -> list[str]. Flags are the documented one-shot/headless modes:
#    codex `exec`, aider `--message`/`--yes`, opencode `run`, gemini-style `-p` for the qwen fork. Best-effort:
#    the runner captures returncode/stdout regardless, so an off flag degrades to a captured non-zero exit.
_CLI_INVOCATIONS: dict[str, Callable[[str, str], list[str]]] = {
    "codex": lambda binary, prompt: [binary, "exec", prompt],
    "aider": lambda binary, prompt: [binary, "--message", prompt, "--yes", "--no-auto-commits", "--no-gitignore"],
    "opencode": lambda binary, prompt: [binary, "run", prompt],
    "clawcodex": lambda binary, prompt: [binary, "exec", prompt],
    "qwen_code": lambda binary, prompt: [binary, "-p", prompt],
}


def _which_first(candidates: list[str]) -> str | None:
    """First installed binary among `candidates`, or None. Never raises."""
    for binary in candidates:
        path = shutil.which(binary)
        if path:
            return path
    return None


def _probe_one(name: str, row: dict[str, Any]) -> dict[str, Any]:
    """Probe a single backend row. `detail` = path (cli) / origin (sdk) / key COUNT (api_pool — never a value)."""
    kind = row["kind"]
    if kind == "cli":
        path = _which_first(row["probe"])
        return {"name": name, "kind": kind, "available": path is not None, "how": "which",
                "checked": list(row["probe"]), "detail": path}
    if kind == "sdk":
        module = row["probe"]
        try:
            spec = importlib.util.find_spec(module)
        except Exception:  # noqa: BLE001 — a broken/partial install must not crash the probe
            spec = None
        return {"name": name, "kind": kind, "available": spec is not None, "how": "find_spec",
                "checked": [module], "detail": getattr(spec, "origin", None) if spec is not None else None}
    if kind == "api_pool":
        try:
            pool = _load_pool()
        except Exception:  # noqa: BLE001 — probing availability must never raise
            pool = []
        return {"name": name, "kind": kind, "available": len(pool) > 0, "how": "pool",
                "checked": [".agent/openrouter_keys.txt (walk up parents)"], "detail": len(pool)}  # count only
    return {"name": name, "kind": kind, "available": False, "how": "unknown_kind", "checked": [], "detail": None}


def probe_backends() -> dict[str, Any]:
    """REAL availability matrix keyed by backend name, plus a computed `n_available`. Never raises; never
    returns a key value (api_pool reports a COUNT). `how` in {which, find_spec, pool}."""
    matrix: dict[str, Any] = {name: _probe_one(name, row) for name, row in _BACKENDS.items()}
    matrix["n_available"] = sum(1 for name in _BACKENDS if matrix[name]["available"])
    matrix["available"] = sorted(name for name in _BACKENDS if matrix[name]["available"])
    return matrix


def _skip(name: str, reason: str) -> dict[str, Any]:
    return {"record_type": "buildout_cli_backend_run", "backend": name, "skipped": True, "reason": reason,
            "token_source": "not_run", "benchmark_kind": BENCHMARK_KIND, **BOUNDARY}


def run_cli_backend(name: str, prompt: str, workspace: str, timeout: int = 180) -> dict[str, Any]:
    """Invoke an AVAILABLE cli backend NON-INTERACTIVELY in `workspace` via subprocess.run, capturing
    returncode, stdout tail, wall time, and a `token_source` label. NEVER raises on an unavailable/unknown/
    non-cli backend or an invocation error — it returns a `skipped=True` receipt instead. Tokens are NOT
    invented: a generic CLI does not emit a parseable usage count, so `token_source="cli_stdout_approx"` and
    the char-derived `approx_output_tokens` is labelled a proxy, never a measured value."""
    row = _BACKENDS.get(name)
    if row is None:
        return _skip(name, f"unknown_backend:{name}")
    if row["kind"] != "cli":
        return _skip(name, f"non_cli_backend:{name} (kind={row['kind']}; use the api_pool/sdk lane, not the CLI runner)")
    binary = _which_first(row["probe"])
    if binary is None:
        return _skip(name, f"cli_not_installed:{name} (checked {row['probe']})")
    build_argv = _CLI_INVOCATIONS.get(name)
    if build_argv is None:
        return _skip(name, f"no_invocation_recipe:{name}")
    ws = Path(workspace)
    if not ws.is_dir():
        return _skip(name, f"workspace_missing:{workspace}")

    argv = build_argv(binary, prompt)
    t0 = time.time()
    try:
        proc = subprocess.run(argv, cwd=str(ws), capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"record_type": "buildout_cli_backend_run", "backend": name, "kind": "cli", "binary": binary,
                "argv": argv, "skipped": False, "timed_out": True, "returncode": None,
                "wall_time_s": round(time.time() - t0, 3), "token_source": "unmeasured_timeout",
                "benchmark_kind": BENCHMARK_KIND, **BOUNDARY}
    except Exception as exc:  # noqa: BLE001 — an unavailable/failed backend must NEVER raise out of here
        return _skip(name, f"invoke_error:{type(exc).__name__}:{str(exc)[:80]}")

    stdout = proc.stdout or ""
    stderr = proc.stderr or ""
    return {"record_type": "buildout_cli_backend_run", "backend": name, "kind": "cli", "binary": binary,
            "argv": argv, "skipped": False, "timed_out": False, "returncode": proc.returncode,
            "wall_time_s": round(time.time() - t0, 3),
            "stdout_tail": stdout[-2000:], "stderr_tail": stderr[-500:], "stdout_chars": len(stdout),
            # tokens NOT parseable from generic CLI stdout -> report a labelled proxy, never a measured count.
            "token_source": "cli_stdout_approx", "approx_output_tokens": max(0, round(len(stdout) / 4)),
            "benchmark_kind": BENCHMARK_KIND, **BOUNDARY}


def self_test() -> bool:
    """Mutation-gated + REAL: the matrix carries every enumerated backend with a real availability verdict; a
    FAKE backend name is absent; `n_available >= 1` (the OpenRouter pool and/or a CLI are present here); and an
    unavailable/unknown backend routes to a skip receipt WITHOUT raising."""
    matrix = probe_backends()

    # (1) every enumerated backend is present with the full status shape.
    for name, row in _BACKENDS.items():
        assert name in matrix, f"probe_backends dropped enumerated backend {name!r}"
        status = matrix[name]
        assert set(status) >= {"available", "kind", "how", "detail"}, f"{name} status missing fields: {status}"
        assert isinstance(status["available"], bool), f"{name}.available must be bool"
        assert status["kind"] == row["kind"] and status["how"] in {"which", "find_spec", "pool"}, \
            f"{name} kind/how mismatch: {status}"

    # (2) a FAKE backend is not present (and is unavailable if probed directly).
    assert "nonexistent_backend" not in _BACKENDS and "nonexistent_backend" not in matrix
    fake = _probe_one("nonexistent_backend", {"kind": "cli", "probe": ["nonexistent_backend_binary_xyz"]})
    assert fake["available"] is False, "a fake/uninstalled backend must probe UNAVAILABLE"

    # (3) n_available is correct AND >= 1 (pool file at .agent/openrouter_keys.txt up-parents, else a CLI).
    recomputed = sum(1 for name in _BACKENDS if matrix[name]["available"])
    assert matrix["n_available"] == recomputed, "n_available must equal the count of available backends"
    assert matrix["n_available"] >= 1, f"expected >=1 available backend (pool or a CLI); matrix={matrix}"
    assert matrix["available"] == sorted(n for n in _BACKENDS if matrix[n]["available"])

    # (4) run_cli_backend NEVER raises on an unavailable/unknown/non-cli backend — it returns a skip receipt.
    try:
        r_unknown = run_cli_backend("nonexistent_backend", "noop", "/tmp")
        r_noncli = run_cli_backend("direct_api", "noop", "/tmp")  # api_pool is not a CLI -> skip, no exec
    except Exception as exc:  # noqa: BLE001
        raise AssertionError(f"run_cli_backend MUST NEVER raise on an unavailable backend; raised {exc!r}")
    assert r_unknown.get("skipped") is True and r_noncli.get("skipped") is True, \
        f"unknown/non-cli backends must be skipped, got {r_unknown}, {r_noncli}"
    assert r_unknown["serves_truth"] is False and r_noncli["candidate"] is True

    assert BENCHMARK_KIND == "real"
    assert matrix[next(iter(_BACKENDS))]  # matrix is non-empty
    print(f"OK buildout_agent_backends self-test: probed {len(_BACKENDS)} backend lanes "
          f"(cli/sdk/api_pool zoo), REAL availability matrix; n_available={matrix['n_available']} "
          f"[{', '.join(matrix['available']) or 'none'}]; fake backend absent+unavailable; "
          f"run_cli_backend skips unavailable/unknown/non-cli WITHOUT raising; "
          f"benchmark_kind=real; candidate=true serves_truth=false")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="BuildoutForge agent/harness backend-lane zoo: probe + run.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--probe", action="store_true", help="print the live availability matrix")
    ap.add_argument("--emit", action="store_true", help="write the availability matrix receipt to disk")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if args.probe or args.emit:
        matrix = probe_backends()
        if args.emit:
            out_dir = resource(ARTIFACT_DIR_REL)
            out_dir.mkdir(parents=True, exist_ok=True)
            receipt = {"record_type": "buildout_agent_backend_matrix", "backends": matrix,
                       "benchmark_kind": BENCHMARK_KIND, **BOUNDARY}
            (out_dir / "availability_matrix.json").write_text(
                json.dumps(receipt, indent=2, sort_keys=True), encoding="utf-8")
        print(json.dumps(matrix, indent=2, sort_keys=True))
        return
    self_test()


if __name__ == "__main__":
    main()
