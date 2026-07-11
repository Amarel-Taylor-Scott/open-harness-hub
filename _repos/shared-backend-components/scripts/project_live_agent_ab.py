#!/usr/bin/env python3
"""scripts.project_live_agent_ab — the LIVE-AGENT project A/B: a real model actually SOLVES a project task,
harness-alone vs harness+primitives, scored by the EXECUTED hidden oracle (candidate-only).

Owner (2026-07-09): wire the live-agent lane on the cloud-function task; use real open-source harnesses; go
toward 1M real programming projects — but only EXECUTED runs count (no proxies). This drives a real model (via
the gitignored OpenRouter pool; agent backend is pluggable — the installed codex/aider CLIs are alternatives)
to write the project solution, runs it through `project_task_harness` (real subprocess oracle), and repairs on
failure up to N turns. Two lanes per task:

  A. harness_alone            — the model gets only the goal + starter stub.
  B. harness_plus_primitives  — the model ALSO gets relevant certified primitives (dispatched by the goal),
                                and we record whether it actually reused them.

Headline metrics are executed: oracle_pass, tokens_to_pass (real completion tokens summed across repair turns),
repair_turns, primitive_hits. BENCHMARK_KIND=real_project. Offline `--self-test` uses a mock agent (good ->
oracle passes; bad -> fails), mutation-gated. `--live` drives the real model. candidate=true/serves_truth=false.

    python3 scripts/project_live_agent_ab.py --self-test
    python3 scripts/project_live_agent_ab.py --live --task cloud_function_http_json --repair 3
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
from typing import Any, Callable  # noqa: E402

from scripts.project_task_harness import _TASKS, run_task, environments  # noqa: E402
from scripts.primitive_token_savings_ab import _load_pool, live_model, _strip_fences, _all_specs  # noqa: E402
from scripts.deterministic_primitive_dispatch import resolve  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
BENCHMARK_KIND = "real_project"  # no_proxy_gate: passes only on executed oracle; tokens are real completion tokens
ARTIFACT_DIR_REL = "data/dev-intel/project_runs"


def _relevant_primitives(goal: str, k: int = 3) -> list[dict[str, str]]:
    """Dispatch the project goal to the verified set; return the top-k as injectable helper packages."""
    ranked = resolve(goal, top_k=k)
    by_name = {s["fn"].__name__: s["fn"] for s in _all_specs()}
    out = []
    for r in ranked:
        fn = by_name.get(r["primitive"])
        if fn:
            out.append({"name": r["primitive"], "source": inspect.getsource(fn)})
    return out


PACKAGE_MODULE = "verified_primitives"  # the pre-installed importable module name for the executable-package lane


def _package_files(injected: list[dict[str, str]]) -> dict[str, str]:
    """Executable-package lane: render the injected primitives as an importable workspace module the solution
    IMPORTS (vs the prompt lane, which merely offers the source text for the model to copy — measured: 0 reuse)."""
    if not injected:
        return {}
    header = ('"""verified_primitives — pre-installed, oracle-certified helper primitives for THIS task.\n'
              'Each passed a hidden-fixture oracle + determinism + security gate (candidate=true / '
              'serves_truth=false). Import and COMPOSE these; do NOT reimplement their logic."""\n'
              'from __future__ import annotations\n\n')
    body = "\n\n".join(h["source"] for h in injected)
    return {f"{PACKAGE_MODULE}.py": header + body}


def _prompt(task: dict[str, Any], injected: list[dict[str, str]] | None, prior_fail: dict | None,
            mode: str = "prompt") -> str:
    p = (f"Implement `{task['solution_file']}` for this project task: {task['goal']}.\n"
         f"Starter stub:\n```python\n{task['starter_files'][task['solution_file']]}```\n")
    if injected and mode == "package":
        names = ", ".join(h["name"] for h in injected)
        p += (f"\nThe module `{PACKAGE_MODULE}` is ALREADY INSTALLED in your workspace and contains these "
              f"oracle-certified, verified-correct helpers: {names}.\n"
              f"Import them (`from {PACKAGE_MODULE} import {names}`) and COMPOSE them in your solution. "
              f"Do NOT reimplement their logic — they are proven correct against hidden fixtures.\n")
    elif injected:  # prompt lane: offer the source text; the model may copy what is useful
        helpers = "\n\n".join(f"# verified helper: {h['name']}\n{h['source']}" for h in injected)
        p += (f"\nYou MAY reuse these verified helper primitives (copy what is useful):\n```python\n{helpers}```\n")
    if prior_fail:
        p += (f"\nYour previous solution FAILED these checks: "
              f"{[k for k, v in prior_fail.items() if not v]}. Fix it.\n")
    p += "Return ONLY the complete Python file contents (no prose, no markdown fences)."
    return p


def run_lane(task_name: str, lane: str, agent: Callable[[str], dict[str, Any]], repair: int = 3,
             inject_mode: str = "none") -> dict[str, Any]:
    """Drive the agent to solve the task; run the EXECUTED oracle; repair up to `repair` turns. Real tokens.
    inject_mode: 'none' (harness alone) | 'prompt' (primitives offered as prompt text) |
    'package' (primitives PRE-INSTALLED as an importable module the solution is told to import + compose)."""
    task = _TASKS[task_name]
    injected = _relevant_primitives(task["goal"]) if inject_mode in ("prompt", "package") else []
    extra = _package_files(injected) if inject_mode == "package" else {}
    tokens = 0
    prior = None
    prim_hits = 0
    imported = False
    for turn in range(repair + 1):
        gen = agent(_prompt(task, injected, prior, mode=inject_mode))
        tokens += gen.get("completion_tokens", 0)
        code = _strip_fences(gen.get("code") or "")
        if not code:
            return {"lane": lane, "oracle_pass": False, "tokens_to_pass": tokens, "repair_turns": turn,
                    "error": gen.get("error"), "primitive_names": [h["name"] for h in injected], **BOUNDARY}
        receipt = run_task(task_name, code, lane=lane, primitives_injected=[h["name"] for h in injected],
                           extra_files=extra)
        if receipt.get("skipped"):
            return {"lane": lane, "skipped": True, "skip_reason": receipt["skip_reason"], **BOUNDARY}
        imported = PACKAGE_MODULE in code                            # did the model import the pre-installed package?
        prim_hits = sum(1 for h in injected if h["name"] in code)    # did the model reference a primitive by name?
        if receipt["oracle_pass"]:
            return {"lane": lane, "oracle_pass": True, "tokens_to_pass": tokens, "repair_turns": turn,
                    "primitive_hits": prim_hits, "package_imported": imported,
                    "primitive_names": [h["name"] for h in injected],
                    "checks": receipt["oracle_checks"], **BOUNDARY}
        prior = receipt["oracle_checks"]
    return {"lane": lane, "oracle_pass": False, "tokens_to_pass": tokens, "repair_turns": repair,
            "primitive_hits": prim_hits, "package_imported": imported, "checks": prior,
            "primitive_names": [h["name"] for h in injected], **BOUNDARY}


def run_ab(task_name: str, agent: Callable[[str], dict[str, Any]], repair: int = 3) -> dict[str, Any]:
    """Three lanes on the SAME executed oracle: alone vs primitives-offered-in-prompt vs primitives-pre-installed."""
    a = run_lane(task_name, "harness_alone", agent, repair, inject_mode="none")
    b = run_lane(task_name, "harness_plus_primitives", agent, repair, inject_mode="prompt")
    c = run_lane(task_name, "harness_plus_package", agent, repair, inject_mode="package")
    return {"record_type": "project_live_agent_ab", "task": task_name, "benchmark_kind": BENCHMARK_KIND,
            "harness_alone": a, "harness_plus_primitives": b, "harness_plus_package": c,
            "delta": {"oracle_pass_A": a.get("oracle_pass"), "oracle_pass_B": b.get("oracle_pass"),
                      "oracle_pass_C": c.get("oracle_pass"),
                      "tokens_A": a.get("tokens_to_pass"), "tokens_B": b.get("tokens_to_pass"),
                      "tokens_C": c.get("tokens_to_pass"),
                      "primitive_reuse_B": b.get("primitive_hits"),
                      "package_imported_C": c.get("package_imported"),
                      "primitive_reuse_C": c.get("primitive_hits")}, **BOUNDARY}


def _mock_good(prompt: str) -> dict[str, Any]:
    return {"code": _TASKS["cloud_function_http_json"]["good"], "completion_tokens": 200, "error": None}


def _mock_bad(prompt: str) -> dict[str, Any]:
    return {"code": _TASKS["cloud_function_http_json"]["bad"], "completion_tokens": 150, "error": None}


# A mock that COMPOSES the pre-installed package: imports the verified helpers and wires them together instead of
# reimplementing. Passes ONLY in the package lane (where verified_primitives.py exists); proves the executable-
# package mechanism end-to-end (module importable at oracle time + a composing solution passes the real oracle).
_MOCK_PACKAGE_CODE = (
    "from verified_primitives import validate_order_event, http_json_error, health_response\n"
    "def handle(event):\n"
    "    import json, os\n"
    "    if event.get('type') == 'health':\n"
    "        return health_response()\n"
    "    v = validate_order_event(event)\n"
    "    if not v['valid']:\n"
    "        return http_json_error(400, 'invalid_payload')\n"
    "    store = 'accepted.json'\n"
    "    accepted = json.load(open(store)) if os.path.exists(store) else []\n"
    "    oid = event['order_id']\n"
    "    if oid not in [a['order_id'] for a in accepted]:\n"
    "        accepted.append({'order_id': oid, 'amount': event['amount']})\n"
    "        json.dump(accepted, open(store, 'w'))\n"
    "    return {'status': 200, 'order_id': oid}\n"
)


def _mock_package(prompt: str) -> dict[str, Any]:
    return {"code": _MOCK_PACKAGE_CODE, "completion_tokens": 120, "error": None}


def self_test() -> bool:
    """Mutation-gated (offline mock agents): a good agent PASSES the executed oracle in all lanes; a bad agent
    FAILS (proving the oracle really runs); and a COMPOSING agent imports the pre-installed package + passes the
    package lane (proving the executable-package mechanism resolves at oracle time). real_project kind."""
    ok = run_ab("cloud_function_http_json", _mock_good, repair=1)
    assert ok["harness_alone"]["oracle_pass"] is True, f"good agent must pass harness_alone: {ok['harness_alone']}"
    assert ok["harness_plus_primitives"]["oracle_pass"] is True, "good agent must pass harness_plus_primitives"
    assert ok["harness_plus_package"]["oracle_pass"] is True, "self-contained good soln must pass the package lane too"
    assert ok["harness_alone"]["tokens_to_pass"] > 0, "tokens must be counted"

    bad = run_ab("cloud_function_http_json", _mock_bad, repair=1)
    assert bad["harness_alone"]["oracle_pass"] is False, "bad agent MUST fail the executed oracle (else it's fake)"
    assert bad["harness_alone"]["repair_turns"] == 1, "a failing agent must exhaust repair turns"

    assert ok["benchmark_kind"] == "real_project" and ok["candidate"] is True and ok["serves_truth"] is False

    # Executable-package mechanism: a composing solution IMPORTS verified_primitives and passes the real oracle.
    # Coupling is explicit — if dispatch stops returning the trio the composer needs, this alerts (not flakes).
    inj_names = [h["name"] for h in _relevant_primitives(_TASKS["cloud_function_http_json"]["goal"])]
    trio = {"validate_order_event", "http_json_error", "health_response"}
    if trio.issubset(set(inj_names)):
        pkg = run_ab("cloud_function_http_json", _mock_package, repair=1)
        c = pkg["harness_plus_package"]
        assert c["oracle_pass"] is True, f"composing the pre-installed package must pass the executed oracle: {c}"
        assert c["package_imported"] is True, "the composing solution must import verified_primitives"
        assert c["primitive_hits"] >= 2, f"the composing solution must reuse >=2 primitives by name: {c}"
        # and it must FAIL when the module is NOT pre-installed (prompt/alone lanes) -> proves the file is load-bearing
        assert pkg["harness_alone"]["oracle_pass"] is False, "composer must fail with no pre-installed module"
        pkg_note = (f"composing agent imports {PACKAGE_MODULE} + passes package lane "
                    f"(reuse={c['primitive_hits']}/{len(inj_names)}), fails without the module")
    else:
        pkg_note = f"dispatch returned {inj_names}; skipped compose assertion (trio not present)"

    print(f"OK project_live_agent_ab self-test: mock GOOD agent passes all 3 lanes (tokens counted), mock BAD agent "
          f"FAILS the executed oracle (repair exhausted); {len(inj_names)} primitives dispatched for injection; "
          f"{pkg_note}; benchmark_kind=real_project; serves_truth=false")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="Live-agent project A/B: harness-alone vs harness+primitives (executed).")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--task", default="cloud_function_http_json", choices=list(_TASKS))
    ap.add_argument("--model", default="openai/gpt-oss-120b:free")
    ap.add_argument("--repair", type=int, default=3)
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if args.live:
        env = environments().get(_TASKS[args.task]["environment"], {})
        if not env.get("available"):
            print(json.dumps({"task": args.task, "skipped": True, "reason": env.get("reason")}, indent=2)); return
        pool = _load_pool()
        agent = lambda pr: live_model(pr, pool, args.model)  # noqa: E731  the real coding agent (model via pool)
        res = run_ab(args.task, agent, repair=args.repair)
        out_dir = resource(ARTIFACT_DIR_REL)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"{args.task}_live_agent_ab.json").write_text(json.dumps(res, indent=2, sort_keys=True),
                                                                 encoding="utf-8")
        print(json.dumps(res, indent=2))
        return
    self_test()


if __name__ == "__main__":
    main()
