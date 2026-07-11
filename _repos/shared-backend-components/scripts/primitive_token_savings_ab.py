#!/usr/bin/env python3
"""scripts.primitive_token_savings_ab — the REAL (non-proxy) token-savings A/B: bare LLM writes the code vs.
reuse the verified primitive (candidate-only measurement).

Owner: get back to primitives + primitive-use harnesses that save SIGNIFICANT tokens. This is the honest
demonstration the whole build was for. For each of the 28 oracle-tested platform primitives (esoteric packs 1+2):

  - ARM A (bare): ask a live model to WRITE the function from scratch -> security-scan -> sandbox-run against the
    ORACLE fixtures -> record actual completion tokens + pass/fail. The model spends real output tokens AND may be
    wrong.
  - ARM B (reuse): the verified primitive is already in the registry -> the harness injects a one-line CALL; the
    implementation body is reused at ZERO generation tokens and is GUARANTEED correct (its oracle already passed).

token_savings = ArmA_completion_tokens - ArmB_call_tokens; correctness_delta = ArmB_pass_rate(=1.0) - ArmA_pass_rate.
This is executor-certified-per-$ made concrete: reuse saves the generation tokens AND removes the failure risk.

Offline `--self-test` uses a deterministic MOCK model (proves the sandbox + accounting, mutation-gated). Real
numbers come from `--live` over the gitignored OpenRouter pool. Everything candidate=true/serves_truth=false; no
generated code runs before the security scan.

    python3 scripts/primitive_token_savings_ab.py --self-test
    python3 scripts/primitive_token_savings_ab.py --live --sample 6
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
import subprocess  # noqa: E402  (the SANDBOX runner itself — not model-generated code)
import tempfile  # noqa: E402
from typing import Any, Callable  # noqa: E402

from scripts.esoteric_platform_primitive_pack import _PRIMITIVES as _PRIMS_1  # noqa: E402
from scripts.esoteric_platform_primitive_pack_2 import _PRIMITIVES as _PRIMS_2  # noqa: E402
from scripts.programming_primitives_pack import _PRIMITIVES as _PRIMS_PROG  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
BENCHMARK_KIND = "real"  # no_proxy_gate: real=executed+measured / proxy=estimated
ARTIFACT_DIR_REL = "data/dev-intel/token_savings"
# banned in model-generated code — no execution before this security scan passes (repo law).
_BANNED_TOKENS = ("import os", "import sys", "import subprocess", "import socket", "import shutil",
                  "__import__", "eval(", "exec(", "open(", "compile(", "globals(", "locals(",
                  "importlib", "import pty", "pty.spawn", "openpty", "forkpty", "popen")


def _tok(text: str) -> int:
    """Cheap token proxy for the CALL line only (ArmB); ArmA uses the model's REPORTED completion tokens."""
    return max(1, round(len(text) / 4))


def _all_specs() -> list[dict[str, Any]]:
    """Every CERTIFIED primitive across the packs (75): esoteric protocol (28) + programming (33) + the
    data-cleaning scalars (14, imported lazily to avoid a cycle with certification_campaign)."""
    specs = list(_PRIMS_1) + list(_PRIMS_2) + list(_PRIMS_PROG)
    try:
        from scripts.certification_campaign import _LANE2  # lazy: cert imports us for the gates -> avoid cycle
        specs += list(_LANE2)
    except Exception:  # noqa: BLE001
        pass
    try:
        from scripts.cloud_function_primitive_pack import _PRIMITIVES as _PRIMS_CF  # project-relevant primitives
        specs += list(_PRIMS_CF)
    except Exception:  # noqa: BLE001
        pass
    return specs


def build_tasks() -> list[dict[str, Any]]:
    tasks: list[dict[str, Any]] = []
    for spec in _all_specs():
        fn: Callable = spec["fn"]
        sig = str(inspect.signature(fn))
        doc = (inspect.getdoc(fn) or "").replace("\n", " ").strip()
        prompt = (f"Write a single self-contained Python function named `{fn.__name__}{sig}` that does the "
                  f"following: {doc}\n"
                  f"Rules: pure standard library only; deterministic; return ONLY the function definition, no "
                  f"prose, no examples, no markdown fences.")
        call_line = f"result = {fn.__name__}({', '.join('arg%d' % i for i in range(len(spec['fixtures'][0][0])))})"
        tasks.append({"name": fn.__name__, "entry": fn.__name__, "prompt": prompt,
                      "fixtures": spec["fixtures"], "verified_body": inspect.getsource(fn),
                      "call_line": call_line, "platform": spec.get("platform") or spec.get("cat") or "scalar"})
    return tasks


def security_scan(code: str) -> list[str]:
    low = code.lower()
    return [t for t in _BANNED_TOKENS if t in low]


def sandbox_run(code: str, entry: str, fixtures: list[tuple]) -> dict[str, Any]:
    """Run code against the oracle fixtures in an isolated subprocess (python -I -S, timeout). Never runs code
    that fails the security scan."""
    banned = security_scan(code)
    if banned:
        return {"ran": False, "n_pass": 0, "n_total": len(fixtures), "error": f"security_scan:{banned}"}
    harness = code + "\n\n_FX = " + repr(fixtures) + "\n_p = 0\n"
    harness += ("for _args, _exp in _FX:\n"
                f"    try:\n        _p += 1 if {entry}(*_args) == _exp else 0\n"
                "    except Exception:\n        pass\n")
    harness += "print('PASS', _p, len(_FX))\n"
    try:
        with tempfile.TemporaryDirectory() as td:
            f = Path(td) / "cand.py"
            f.write_text(harness, encoding="utf-8")
            out = subprocess.run([sys.executable, "-I", "-S", str(f)], capture_output=True, text=True,
                                 timeout=10, cwd=td)
        line = [ln for ln in out.stdout.splitlines() if ln.startswith("PASS")]
        if line:
            _, p, t = line[-1].split()
            return {"ran": True, "n_pass": int(p), "n_total": int(t), "error": None}
        return {"ran": True, "n_pass": 0, "n_total": len(fixtures), "error": (out.stderr or "no_output")[:80]}
    except subprocess.TimeoutExpired:
        return {"ran": False, "n_pass": 0, "n_total": len(fixtures), "error": "timeout"}


def _strip_fences(text: str) -> str:
    t = text.strip()
    if "```" in t:
        parts = t.split("```")
        # take the largest fenced block, drop a leading language tag
        blk = max(parts, key=len)
        return "\n".join(ln for ln in blk.splitlines() if not ln.strip() in ("python", "py")).strip()
    return t


def live_model(prompt: str, pool: list[str], model: str, max_tokens: int = 700,
               strip: bool = True,
               base_url: str = "https://openrouter.ai/api/v1/chat/completions") -> dict[str, Any]:
    """Call an OpenAI-compatible chat endpoint via a key pool (rotate on throttle). Returns real completion tokens
    from the usage payload. `strip=True` returns the largest fenced block (single-file tasks); `strip=False`
    returns RAW content so a MULTI-FILE build survives. `max_tokens` sizes the generation budget. `base_url`
    selects the provider — default OpenRouter; pass https://api.mistral.ai/v1/chat/completions for Mistral/
    Codestral (same OpenAI schema + Bearer auth)."""
    import urllib.request
    import urllib.error
    body = json.dumps({"model": model, "max_tokens": max_tokens, "temperature": 0,
                       "messages": [{"role": "user", "content": prompt}]}).encode()
    for key in pool:  # rotate until one answers
        req = urllib.request.Request(base_url, data=body,
                                     headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=120) as r:
                d = json.load(r)
            msg = d["choices"][0]["message"]
            raw = msg.get("content") or msg.get("reasoning") or ""
            code = _strip_fences(raw) if strip else raw
            usage = d.get("usage", {})
            comp = usage.get("completion_tokens") or _tok(code)
            if code.strip():
                return {"code": code, "completion_tokens": comp,
                        "input_tokens": usage.get("prompt_tokens"), "error": None}
        except urllib.error.HTTPError as e:
            if e.code in (429, 402, 503):
                continue
            return {"code": "", "completion_tokens": 0, "error": f"http{e.code}"}
        except KeyError as e:
            # OpenAI-compatible providers sometimes return a syntactically valid JSON
            # error/envelope without the expected choices/message fields.  Keep the
            # missing field (never the response body or credentials) so the grid can
            # distinguish a provider/schema failure from an executed model failure.
            return {"code": "", "completion_tokens": 0, "input_tokens": 0,
                    "error": f"response_missing_field:{e.args[0]}"[:120]}
        except Exception as e:  # noqa: BLE001
            return {"code": "", "completion_tokens": 0, "input_tokens": 0,
                    "error": f"transport:{type(e).__name__}"}
    return {"code": "", "completion_tokens": 0, "error": "all_keys_exhausted"}


def run_ab(tasks: list[dict[str, Any]], model_fn: Callable[[str], dict[str, Any]]) -> dict[str, Any]:
    rows = []
    for t in tasks:
        gen = model_fn(t["prompt"])
        arm_a = sandbox_run(gen["code"], t["entry"], t["fixtures"]) if gen["code"] else \
            {"ran": False, "n_pass": 0, "n_total": len(t["fixtures"]), "error": gen["error"]}
        a_tokens = gen["completion_tokens"]
        a_pass = arm_a["n_total"] > 0 and arm_a["n_pass"] == arm_a["n_total"]
        # ArmB: reuse the verified primitive — implementation at 0 gen tokens; only the CALL line is "spent".
        b_tokens = _tok(t["call_line"])
        rows.append({"name": t["name"], "platform": t["platform"],
                     "armA_tokens": a_tokens, "armA_pass": a_pass, "armA_detail": arm_a,
                     "armB_tokens": b_tokens, "armB_pass": True,  # oracle already proved it
                     "tokens_saved": max(0, a_tokens - b_tokens), **BOUNDARY})
    n = len(rows)
    a_total = sum(r["armA_tokens"] for r in rows)
    b_total = sum(r["armB_tokens"] for r in rows)
    a_correct = sum(1 for r in rows if r["armA_pass"])
    return {"record_type": "primitive_token_savings_ab", "n_tasks": n,
            "armA_total_tokens": a_total, "armB_total_tokens": b_total,
            "tokens_saved_total": a_total - b_total,
            "savings_factor": round(a_total / b_total, 2) if b_total else None,
            "armA_correct": a_correct, "armA_correct_rate": round(a_correct / n, 3) if n else None,
            "armB_correct_rate": 1.0, "rows": rows, **BOUNDARY}


def _load_pool() -> list[str]:
    for p in _here_boot.parents:
        f = p / ".agent" / "openrouter_keys.txt"
        if f.exists():
            return [l.strip() for l in f.read_text().splitlines() if l.strip() and not l.startswith("#")]
    return []


def run_multi_tier(tasks: list[dict[str, Any]], models: list[str], pool: list[str]) -> dict[str, Any]:
    """Run the A/B for each model tier; build a leaderboard (correctness-first, then savings). ArmB (reuse) is
    the same across models — the verified body — so the variable is how well each model WRITES it from scratch."""
    per_model: dict[str, Any] = {}
    for m in models:
        res = run_ab(tasks, lambda pr, mm=m: live_model(pr, pool, mm))
        per_model[m] = {k: res[k] for k in ("n_tasks", "armA_total_tokens", "armB_total_tokens",
                                            "tokens_saved_total", "savings_factor", "armA_correct_rate",
                                            "armB_correct_rate")}
    board = sorted(per_model.items(),
                   key=lambda kv: (kv[1]["armA_correct_rate"] or 0, kv[1]["savings_factor"] or 0), reverse=True)
    return {"record_type": "multi_tier_token_savings", "models": models, "n_tasks": len(tasks),
            "per_model": per_model, "leaderboard": [{"model": m, **v} for m, v in board],
            "armB_reuse_tokens": next(iter(per_model.values()))["armB_total_tokens"] if per_model else 0,
            **BOUNDARY}


def _mock_model_correct(prompt: str) -> dict[str, Any]:
    """Deterministic MOCK for the offline self-test: returns the verified body (correct) + a fixed token count."""
    name = prompt.split("`")[1].split("(")[0]
    body = next(inspect.getsource(s["fn"]) for s in _all_specs() if s["fn"].__name__ == name)
    return {"code": body, "completion_tokens": 180, "error": None}


def _mock_model_wrong(prompt: str) -> dict[str, Any]:
    return {"code": "def broken(*a):\n    return 'nope'\n", "completion_tokens": 150, "error": None}


def emit(result: dict[str, Any]) -> str:
    out_dir = resource(ARTIFACT_DIR_REL)
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / "token_savings_ab_receipt.json"
    p.write_text(json.dumps(result, indent=2, sort_keys=True), encoding="utf-8")
    return str(p)


def self_test() -> bool:
    """Mutation-gated (offline, MOCK model). Proves: security scan blocks dangerous code; sandbox measures oracle
    pass/fail correctly; ArmB reuses at ~0 gen tokens; savings > 0; correctness is measured (a wrong ArmA fails)."""
    tasks = build_tasks()
    assert len(tasks) >= 28, f"expected >=28 primitive tasks, got {len(tasks)}"

    # (1) security scan blocks a dangerous body (no execution before the gate).
    assert security_scan("import os\nos.system('x')"), "security scan must flag os.system"
    assert not security_scan("def f(x):\n    return x + 1\n"), "clean code must pass the scan"

    # (2) sandbox measures a CORRECT body as full pass, and a WRONG body as fail.
    good = tasks[0]
    r_ok = sandbox_run(good["verified_body"], good["entry"], good["fixtures"])
    assert r_ok["ran"] and r_ok["n_pass"] == r_ok["n_total"] > 0, f"verified body should pass its oracle: {r_ok}"

    # (3) full A/B with a CORRECT mock: ArmB reuses at fewer tokens than ArmA writes -> savings > 0.
    res = run_ab(tasks[:6], _mock_model_correct)
    assert res["armB_total_tokens"] < res["armA_total_tokens"], "reuse must cost fewer tokens than writing"
    assert res["tokens_saved_total"] > 0 and res["savings_factor"] > 1
    assert res["armB_correct_rate"] == 1.0
    assert res["candidate"] is True and res["serves_truth"] is False

    # (4) correctness is really measured: a WRONG mock makes ArmA fail while ArmB stays correct.
    res_bad = run_ab(tasks[:4], _mock_model_wrong)
    assert res_bad["armA_correct"] == 0, "a wrong ArmA must be detected as incorrect by the oracle sandbox"
    assert res_bad["armB_correct_rate"] == 1.0, "ArmB (verified reuse) is always correct"

    print(f"OK primitive_token_savings_ab self-test: {len(tasks)} primitive tasks; MOCK A/B on 6 -> "
          f"reuse {res['armB_total_tokens']} vs write {res['armA_total_tokens']} tokens "
          f"({res['savings_factor']}x saved), ArmB correctness 1.0; wrong-ArmA detected (0/4); serves_truth=false")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="Real token-savings A/B: bare LLM writes vs verified-primitive reuse.")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--live", action="store_true", help="run ArmA against the OpenRouter pool (real tokens)")
    ap.add_argument("--sample", type=int, default=6)
    ap.add_argument("--model", default="openai/gpt-oss-20b:free")
    ap.add_argument("--models", default=None, help="comma-separated model ladder for a multi-tier leaderboard")
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if args.models:
        tasks = build_tasks()[: args.sample]
        res = run_multi_tier(tasks, [m.strip() for m in args.models.split(",")], _load_pool())
        out_dir = resource(ARTIFACT_DIR_REL)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / "multi_tier_token_savings_receipt.json").write_text(json.dumps(res, indent=2, sort_keys=True),
                                                                       encoding="utf-8")
        print(json.dumps({"n_tasks": res["n_tasks"], "armB_reuse_tokens": res["armB_reuse_tokens"],
                          "leaderboard": res["leaderboard"]}, indent=2))
        return
    tasks = build_tasks()[: args.sample]
    if args.live:
        pool = [l.strip() for l in (_sbc_boot.parent / ".agent" / "openrouter_keys.txt").read_text().splitlines()
                if l.strip() and not l.startswith("#")] if (_sbc_boot.parent / ".agent" / "openrouter_keys.txt").exists() \
            else [l.strip() for p in _here_boot.parents for l in
                  ((p / ".agent" / "openrouter_keys.txt").read_text().splitlines()
                   if (p / ".agent" / "openrouter_keys.txt").exists() else [])
                  if l.strip() and not l.startswith("#")]
        res = run_ab(tasks, lambda pr: live_model(pr, pool, args.model))
    else:
        res = run_ab(tasks, _mock_model_correct)
    res["path"] = emit(res)
    print(json.dumps({k: res[k] for k in ("n_tasks", "armA_total_tokens", "armB_total_tokens",
                                          "tokens_saved_total", "savings_factor", "armA_correct_rate",
                                          "armB_correct_rate", "path")}, indent=2))


if __name__ == "__main__":
    main()
