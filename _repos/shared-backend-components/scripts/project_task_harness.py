#!/usr/bin/env python3
"""scripts.project_task_harness — REAL project-level benchmark harness (candidate-only). A ProjectTask passes
only when its solution actually BUILDS + RUNS + passes an EXECUTED hidden oracle — not when files look plausible.

Owner (2026-07-09): the harness proves primitive-level reuse, not project-level software delivery. Build a
ProjectTask harness: starter repo + task contract + local runtime + executed oracle + hidden tests + receipts +
cleanup. Headline-eligible only when it executes real quantities (build/test commands, sandbox/oracle, HTTP,
container/K8s/emulator). BENCHMARK_KIND=real_project.

This is the honest MVP: two PURE-LOCAL project families that really execute in this environment (a cloud-function
HTTP/event handler; a small ML train/eval/register pipeline) plus a docker/kind-gated k8s worker that skips with
a structured reason when unavailable. Each task ships a hidden oracle and REFERENCE good/bad solutions so the
self-test proves the core property: the oracle PASSES a good solution and FAILS a bad one (real execution in an
isolated `python -I` subprocess, per-run temp workspace, cleanup). A/B lanes (harness_alone vs
harness_plus_primitives) are wired; the live-agent lane is the next wave. candidate=true/serves_truth=false.

    python3 scripts/project_task_harness.py --self-test
    python3 scripts/project_task_harness.py --run --task cloud_function_http_json --solution good
    python3 scripts/project_task_harness.py --environments
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
import json  # noqa: E402
import shutil  # noqa: E402  (environment availability probe — not model code)
import subprocess  # noqa: E402  (the oracle RUNNER itself)
import tempfile  # noqa: E402
import time  # noqa: E402
from typing import Any, Callable  # noqa: E402

BOUNDARY: dict[str, Any] = {"candidate": True, "serves_truth": False}
BENCHMARK_KIND = "real_project"  # no_proxy_gate: passes only on executed build/run/oracle, never plausibility
ARTIFACT_DIR_REL = "data/dev-intel/project_benchmarks"


# ── environment availability (skip-with-reason, never fail the whole suite) ─────────────────────────────────
def environments() -> dict[str, Any]:
    def has(binary: str) -> bool:
        return shutil.which(binary) is not None
    return {"pure_local": {"available": True, "reason": None},
            "docker_compose": {"available": has("docker"), "reason": None if has("docker") else "docker not on PATH"},
            "kind_k8s": {"available": has("kind") and has("kubectl") and has("docker"),
                         "reason": None if (has("kind") and has("kubectl") and has("docker")) else "kind/kubectl/docker missing"},
            "localstack_aws": {"available": has("localstack"), "reason": None if has("localstack") else "localstack not on PATH"}}


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
# Task A — cloud_function_http_json (PURE-LOCAL, really executes). The solution defines handle(event)->dict;
# the HIDDEN oracle invokes it with valid/invalid/duplicate/health events in an isolated subprocess and checks
# real behavior (status codes, persisted store, idempotency).
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
_CLOUD_FN_ORACLE = r'''
import json, os, sys, importlib.util
sys.path.insert(0, os.getcwd())  # workspace on path so a solution may import a pre-installed verified-primitive module
spec = importlib.util.spec_from_file_location("solution", "handler.py")
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
handle = getattr(mod, "handle")
checks = {}
# 1. valid order -> 200 + persisted
r = handle({"type": "order", "order_id": "A1", "amount": 10})
checks["valid_200"] = (r.get("status") == 200)
# 2. invalid (missing amount) -> 400, not persisted
r = handle({"type": "order", "order_id": "B2"})
checks["invalid_400"] = (r.get("status") == 400)
# 3. duplicate order -> idempotent (accepted store must not double-count A1)
handle({"type": "order", "order_id": "A1", "amount": 10})
store = json.load(open("accepted.json")) if os.path.exists("accepted.json") else []
ids = [a.get("order_id") for a in store]
checks["persisted_A1"] = ("A1" in ids)
checks["idempotent_no_dupe"] = (ids.count("A1") == 1)
checks["invalid_not_persisted"] = ("B2" not in ids)
# 4. health -> 200 healthy
r = handle({"type": "health"})
checks["health_ok"] = (r.get("status") == 200 and r.get("healthy") is True)
oracle_pass = all(checks.values())
print("ORACLE " + json.dumps({"checks": checks, "oracle_pass": oracle_pass}))
'''

_CLOUD_FN_GOOD = r'''
def handle(event):
    import json, os
    if event.get("type") == "health":
        return {"status": 200, "healthy": True}
    oid, amt = event.get("order_id"), event.get("amount")
    if not oid or amt is None or amt <= 0:
        return {"status": 400, "error": "invalid_payload"}
    store = "accepted.json"
    accepted = json.load(open(store)) if os.path.exists(store) else []
    if oid not in [a["order_id"] for a in accepted]:
        accepted.append({"order_id": oid, "amount": amt})
        json.dump(accepted, open(store, "w"))
    return {"status": 200, "order_id": oid}
'''

_CLOUD_FN_BAD = 'def handle(event):\n    return {"status": 200}\n'   # no validation, no store, no idempotency


# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
# Task B — ml_pipeline_train_eval_register (PURE-LOCAL, really executes). The solution defines run()->dict that
# trains on a tiny deterministic dataset, writes model.json + metrics.json, does batch predictions. The HIDDEN
# oracle runs it, checks a metric threshold, reproducibility (run twice -> identical model), and no test leakage.
# ══════════════════════════════════════════════════════════════════════════════════════════════════════════
_ML_ORACLE = r'''
import json, importlib.util
spec = importlib.util.spec_from_file_location("solution", "pipeline.py")
mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
run = getattr(mod, "run")
checks = {}
out1 = run()
checks["metrics_written"] = isinstance(out1, dict) and "accuracy" in out1
checks["accuracy_threshold"] = out1.get("accuracy", 0) >= 0.8
model1 = json.load(open("model.json"))
checks["model_artifact"] = "threshold" in model1
# reproducibility: run again, identical model
out2 = run()
model2 = json.load(open("model.json"))
checks["reproducible"] = (model1 == model2)
# no leakage: test indices must be disjoint from train indices (solution must record them)
checks["no_leakage"] = set(model1.get("train_idx", [])).isdisjoint(set(model1.get("test_idx", [])))
oracle_pass = all(checks.values())
print("ORACLE " + json.dumps({"checks": checks, "oracle_pass": oracle_pass}))
'''

# a tiny deterministic 1-feature dataset separable at threshold 5 (label = feature >= 5).
_ML_DATA = "\n".join(f"{x},{1 if x >= 5 else 0}" for x in range(10)) + "\n"

_ML_GOOD = r'''
def run():
    import json
    rows = [tuple(map(int, l.split(","))) for l in open("data.csv") if l.strip()]
    train = rows[:8]; test = rows[8:]
    train_idx = list(range(8)); test_idx = list(range(8, 10))
    # fit: threshold = midpoint between max-negative and min-positive feature in train
    pos = [x for x, y in train if y == 1]; neg = [x for x, y in train if y == 0]
    threshold = (max(neg) + min(pos)) / 2 if pos and neg else 5
    correct = sum(1 for x, y in test if (1 if x >= threshold else 0) == y)
    acc = correct / len(test) if test else 0.0
    json.dump({"threshold": threshold, "train_idx": train_idx, "test_idx": test_idx}, open("model.json", "w"))
    json.dump({"accuracy": acc}, open("metrics.json", "w"))
    return {"accuracy": acc}
'''

_ML_BAD = r'''
def run():
    import json
    json.dump({"threshold": 0}, open("model.json", "w"))   # trivial: predicts all-positive, leaks nothing recorded
    json.dump({"accuracy": 0.5}, open("metrics.json", "w"))
    return {"accuracy": 0.5}
'''

# ── task registry: family, environment, starter files, oracle, reference good/bad solutions ─────────────────
_TASKS: dict[str, dict[str, Any]] = {
    "cloud_function_http_json": {"family": "cloud_function", "environment": "pure_local",
                                 "solution_file": "handler.py", "oracle_file": "oracle.py",
                                 "oracle": _CLOUD_FN_ORACLE, "good": _CLOUD_FN_GOOD, "bad": _CLOUD_FN_BAD,
                                 "starter_files": {"handler.py": "def handle(event):\n    raise NotImplementedError\n"},
                                 "goal": "implement an HTTP/event handler: validate order events, persist accepted "
                                         "ones idempotently, reject invalid payloads, answer health checks"},
    "ml_pipeline_train_eval_register": {"family": "ml_pipeline", "environment": "pure_local",
                                        "solution_file": "pipeline.py", "oracle_file": "oracle.py",
                                        "oracle": _ML_ORACLE, "good": _ML_GOOD, "bad": _ML_BAD,
                                        "starter_files": {"pipeline.py": "def run():\n    raise NotImplementedError\n",
                                                          "data.csv": _ML_DATA},
                                        "goal": "train/eval a tiny model deterministically, write model+metrics, "
                                                "reproducible, no train/test leakage, meet an accuracy threshold"},
    "k8s_queue_worker": {"family": "k8s_worker", "environment": "kind_k8s", "solution_file": "worker.py",
                         "oracle_file": "oracle.py", "oracle": "", "good": "", "bad": "",
                         "starter_files": {}, "goal": "containerized queue worker on a local kind cluster"},
}


def run_task(task_name: str, solution_code: str, lane: str = "harness_alone",
             primitives_injected: list[str] | None = None, extra_files: dict[str, str] | None = None) -> dict[str, Any]:
    """Copy starter -> apply the solution -> EXECUTE the hidden oracle in an isolated subprocess -> receipt.
    `extra_files` are written into the workspace before the solution (e.g. a pre-installed verified-primitive
    module the handler can import). Never returns oracle_pass=True without an executed oracle."""
    task = _TASKS[task_name]
    env = environments().get(task["environment"], {"available": False, "reason": "unknown env"})
    if not env["available"]:
        return {"task": task_name, "lane": lane, "skipped": True, "skip_reason": env["reason"],
                "benchmark_kind": BENCHMARK_KIND, "oracle_pass": None, **BOUNDARY}
    t0 = time.time()
    with tempfile.TemporaryDirectory() as ws:
        wsp = Path(ws)
        for fname, content in task["starter_files"].items():          # clone starter repo
            (wsp / fname).write_text(content, encoding="utf-8")
        for fname, content in (extra_files or {}).items():            # pre-installed verified-primitive package
            (wsp / fname).write_text(content, encoding="utf-8")
        (wsp / task["solution_file"]).write_text(solution_code, encoding="utf-8")   # apply agent/reference solution
        (wsp / task["oracle_file"]).write_text(task["oracle"], encoding="utf-8")    # hidden oracle
        try:
            proc = subprocess.run([sys.executable, "-I", task["oracle_file"]], cwd=ws, capture_output=True,
                                  text=True, timeout=120)
        except subprocess.TimeoutExpired:
            return {"task": task_name, "lane": lane, "oracle_pass": False, "error": "timeout",
                    "benchmark_kind": BENCHMARK_KIND, **BOUNDARY}
        line = next((ln for ln in proc.stdout.splitlines() if ln.startswith("ORACLE ")), None)
        result = json.loads(line[len("ORACLE "):]) if line else {"checks": {}, "oracle_pass": False}
    return {"record_type": "project_run_receipt", "task": task_name, "family": task["family"], "lane": lane,
            "benchmark_kind": BENCHMARK_KIND, "environment": task["environment"],
            "commands_run": [f"{Path(sys.executable).name} -I {task['oracle_file']}"],
            "exit_code": proc.returncode if line else 1,
            "oracle_checks": result["checks"], "oracle_pass": bool(result["oracle_pass"]),
            "wall_time_s": round(time.time() - t0, 3), "primitives_injected": primitives_injected or [],
            "stderr_tail": (proc.stderr or "")[-160:] if not result["oracle_pass"] else "", **BOUNDARY}


def self_test() -> bool:
    """Mutation-gated + REAL: the hidden oracle must PASS a good solution and FAIL a bad one (executed in a real
    subprocess), for each pure-local project family. This is the property the owner demanded: bad solutions fail."""
    for task in ("cloud_function_http_json", "ml_pipeline_train_eval_register"):
        good = run_task(task, _TASKS[task]["good"])
        assert good["oracle_pass"] is True, f"{task}: GOOD solution must pass the executed oracle: {good}"
        assert good["oracle_checks"] and all(good["oracle_checks"].values()), f"{task}: all checks must pass"
        bad = run_task(task, _TASKS[task]["bad"])
        assert bad["oracle_pass"] is False, f"{task}: BAD solution MUST FAIL (else the oracle is fake): {bad}"
        # the starter stub (NotImplementedError) must also fail — no plausibility passes.
        stub = run_task(task, _TASKS[task]["starter_files"][_TASKS[task]["solution_file"]])
        assert stub["oracle_pass"] is False, f"{task}: unimplemented stub must fail"

    # k8s task skips with a structured reason here (no kind/docker), never a false pass.
    k = run_task("k8s_queue_worker", "")
    assert k.get("skipped") is True and k["skip_reason"], "k8s task must skip-with-reason when kind unavailable"

    assert BENCHMARK_KIND == "real_project"
    print(f"OK project_task_harness self-test: 2 pure-local project families EXECUTED — good solutions PASS the "
          f"hidden oracle, bad+stub solutions FAIL (real subprocess); k8s skips-with-reason "
          f"({k['skip_reason']}); benchmark_kind=real_project; serves_truth=false")
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="Real project-level benchmark harness (build/run/oracle).")
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--environments", action="store_true")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--task", default="cloud_function_http_json", choices=list(_TASKS))
    ap.add_argument("--solution", default="good", choices=["good", "bad", "stub"])
    args = ap.parse_args()
    if args.self_test:
        self_test()
        return
    if args.environments:
        print(json.dumps(environments(), indent=2))
        return
    if args.run:
        t = _TASKS[args.task]
        sol = t["good"] if args.solution == "good" else (t["bad"] if args.solution == "bad"
                                                         else t["starter_files"].get(t["solution_file"], ""))
        res = run_task(args.task, sol)
        out_dir = resource(ARTIFACT_DIR_REL)
        out_dir.mkdir(parents=True, exist_ok=True)
        (out_dir / f"{args.task}_{args.solution}_receipt.json").write_text(json.dumps(res, indent=2, sort_keys=True),
                                                                           encoding="utf-8")
        print(json.dumps(res, indent=2))
        return
    self_test()


if __name__ == "__main__":
    main()
