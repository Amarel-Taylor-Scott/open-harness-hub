#!/usr/bin/env python3
"""scripts.model_lane_bakeoff — race the SAME small job set across the AVAILABLE capability lanes and score each
lane per job type, then emit updated router weights so llm_capability_router routes by MEASURED performance, not
just static policy. The headline is executor-certified / useful-candidate quality per lane, never raw count.

For every reachable lane x job type (ideation / spec / executor / fixture / verifier / critique / esoteric
expansion), ~5 probes are run and scored on: JSON validity, schema adherence, executor-pass (security-gated +
SANDBOX-executed against the draft's own fixtures), determinism (stable stdout across two runs), cost, latency,
and refusal. Lanes are ranked per router job type -> dist/llm-router/lane_weights.json (consumed by the router,
self-healing). Receipts: artifacts/llm_endpoints/model_lane_bakeoff.json + docs/MODEL_LANE_BAKEOFF.md.

serves_truth=false — a bakeoff is a MEASUREMENT of candidate lanes, never served truth.

    python3 scripts/model_lane_bakeoff.py --self-test          # offline, per-lane stub chat_fn, deterministic
    python3 scripts/model_lane_bakeoff.py --run [--probes 5]   # live race over the reachable lanes
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
import datetime as _dt  # noqa: E402
import json  # noqa: E402
import socket  # noqa: E402
from typing import Any, Callable, Optional  # noqa: E402

from scripts import _llm_client as _L  # noqa: E402
from scripts import llm_capability_router as _router  # noqa: E402
from scripts import spec_to_executor_synthesizer as _synth  # noqa: E402  REUSE: sandbox_run + _grade + _parse_draft
from scripts.hy3_overnight_flywheel import _parse_json  # noqa: E402  REUSE: tolerant JSON extraction
from scripts.llm_quota_manager import BOUNDARY, QuotaManager, estimate_cost  # noqa: E402
from scripts.primitive_security_gate import gate_body  # noqa: E402

ARTIFACT_PATH = _sbc_boot / "artifacts" / "llm_endpoints" / "model_lane_bakeoff.json"
DOC_PATH = resource("docs/MODEL_LANE_BAKEOFF.md")
WEIGHTS_PATH = _router.WEIGHTS_PATH

#: probe job -> (router_job_type_for_lane_selection, is_code_job). Add a job = one row.
BAKEOFF_JOBS: tuple[tuple[str, str, bool], ...] = (
    ("ideation", "ideation", False),
    ("spec", "spec_generation", False),
    ("executor", "executor_synthesis", True),
    ("fixture", "fixture_generation", True),
    ("verifier", "verifier_generation", True),
    ("critique", "executor_synthesis", True),
    ("esoteric_expansion", "esoteric_expansion", False),
)
#: composite score = weighted mean of applicable axes (all in [0,1]; higher is better). Rationale in comments.
_AXIS_WEIGHTS: dict[str, float] = {
    "json_valid": 0.25,          # a parseable object is the floor for everything downstream
    "schema_adherence": 0.20,    # the object carries the keys the job asked for
    "executor_pass": 0.30,       # code actually runs + passes its own fixtures (the real signal for code jobs)
    "determinism": 0.15,         # same input -> same output twice (truth-eligibility precondition)
    "non_refusal": 0.10,         # the lane answered instead of declining
}
_CODE_SYS = ("Return ONE JSON object only: {\"name\", \"python_body\" (stdlib-only pure function), \"entry\" "
             "(the function name), \"positive_fixtures\" (>=2 {\"input\":{kwargs}|[args]|value, \"expected\":val})}. "
             "Deterministic; no network/file/subprocess/eval.")
_TEXT_SYS = ("Return ONE JSON object only, no prose: {\"name\", \"summary\", \"items\":[...]} describing reusable "
             "deterministic primitives for the request.")
_REFUSAL_MARKERS = ("i can't", "i cannot", "i'm unable", "as an ai", "i won't", "cannot assist", "i am not able")


def _probes(job: str, n: int) -> list[str]:
    """n small deterministic prompts for a probe job (stable across runs -> reproducible receipts)."""
    seeds = ["a US ZIP+4", "an ISO-8601 duration", "a hex color", "a semantic version string", "an E.164 phone",
             "a CSV row with quoted commas", "a snake_case identifier", "a percentage string"]
    verb = {"ideation": "Propose deterministic primitives to parse/normalize",
            "spec": "Write a spec (name, input/output schema, edges) for a parser of",
            "executor": "Write a deterministic Python parser + fixtures for",
            "fixture": "Write positive+negative fixtures (as a parser+fixtures object) for",
            "verifier": "Write a deterministic validator + fixtures for",
            "critique": "Improve, then output a complete deterministic parser + fixtures for",
            "esoteric_expansion": "Expand into edge-case variants a deterministic parser for"}[job]
    return [f"{verb} {seeds[i % len(seeds)]}." for i in range(n)]


def _is_refusal(text: str, err: Any) -> bool:
    if err:
        return False  # a provider error is not a model refusal (tracked separately)
    low = (text or "").lower().strip()
    return (not low) or any(m in low for m in _REFUSAL_MARKERS)


def _schema_adherence(is_code: bool, obj: Optional[dict[str, Any]]) -> float:
    if not obj:
        return 0.0
    want = ("python_body", "entry") if is_code else ("name",)
    return round(sum(1 for k in want if obj.get(k)) / len(want), 3)


_TRIVIAL_FX = [{"input": {"s": "x"}}]  # no-expectation smoke fixture used only if a draft ships none


def score_response(is_code: bool, text: str, err: Any, usage: dict[str, Any], latency: float,
                   lane: dict[str, Any]) -> dict[str, Any]:
    """Score ONE lane response on the axes. Code jobs are security-gated + SANDBOX-executed against the draft's
    OWN fixtures (self-consistency: does the code the lane wrote pass the tests the lane wrote?)."""
    refusal = _is_refusal(text, err)
    obj = _synth._parse_draft(text) if is_code else _parse_json(text)  # noqa: SLF001 — reuse the tolerant parsers
    json_valid = 1.0 if obj else 0.0
    adherence = _schema_adherence(is_code, obj)
    axes: dict[str, float] = {"json_valid": json_valid, "schema_adherence": adherence,
                              "non_refusal": 0.0 if refusal else 1.0}
    if is_code:
        executor_pass, determinism = 0.0, 0.0
        if obj and obj.get("python_body") and obj.get("entry"):
            body, entry = str(obj["python_body"]), str(obj["entry"])
            if gate_body(body, name=entry)["status"] != "quarantine":
                fx = obj.get("positive_fixtures") or _TRIVIAL_FX
                r1 = _synth.sandbox_run(body, entry, fx)
                r2 = _synth.sandbox_run(body, entry, fx)
                grade = _synth._grade(fx, r1)  # noqa: SLF001 — reuse the grader
                executor_pass = 1.0 if grade["all_pass"] else (0.5 if r1.get("ran") else 0.0)
                determinism = 1.0 if (r1.get("ran") and r1.get("stdout") == r2.get("stdout")) else 0.0
        axes["executor_pass"], axes["determinism"] = executor_pass, determinism
    in_tok = int(usage.get("prompt_tokens") or usage.get("input_tokens") or 0)
    out_tok = int(usage.get("completion_tokens") or usage.get("output_tokens") or max(0, len(text) // 4))
    cost = float(usage["cost"]) if usage.get("cost") is not None else estimate_cost(lane, in_tok, out_tok)
    composite = round(sum(_AXIS_WEIGHTS[a] * axes[a] for a in axes) / sum(_AXIS_WEIGHTS[a] for a in axes), 4)
    return {**axes, "composite": composite, "refusal": refusal, "cost": round(cost, 8),
            "latency_s": round(latency, 4), "output_tokens": out_tok}


def _mean(vals: list[float]) -> float:
    return round(sum(vals) / len(vals), 4) if vals else 0.0


def reachable_lanes(caps: dict[str, Any]) -> dict[str, bool]:
    """Which lanes are reachable IN THIS ENV — key PRESENCE only (never a value) + a localhost TCP probe."""
    reach: dict[str, bool] = {}
    for lane_id, cap in caps.items():
        et = cap.get("endpoint_type")
        if et == "ollama_local":
            reach[lane_id] = _tcp_open("127.0.0.1", 11434)
        elif et == "omniroute":
            reach[lane_id] = _tcp_open("127.0.0.1", 20128)
        else:
            key = bool(_L.resolve_provider(cap["provider_id"]).get("key"))
            if cap["provider_id"] == "openrouter" and not key:
                try:
                    from scripts.hy3_overnight_flywheel import _load_openrouter_keys  # noqa: PLC0415
                    key = bool(_load_openrouter_keys())
                except Exception:  # noqa: BLE001
                    key = False
            reach[lane_id] = key
    return reach


def _tcp_open(host: str, port: int, timeout: float = 1.0) -> bool:
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def run_bakeoff(*, probes: int = 5, chat_for_lane: Optional[Callable[[str], Callable[[dict, str, str], dict]]] = None,
                lanes: Optional[list[str]] = None, quota: Optional[QuotaManager] = None,
                clock: Optional[Callable[[], float]] = None) -> dict[str, Any]:
    """Race probes x jobs x lanes. `chat_for_lane(lane_id) -> chat(lane, system, user)->dict` lets the self-test
    inject a per-lane stub (no network). Returns the full receipt. Deterministic given fixed stubs + clock."""
    caps = _router.capabilities()
    qm = quota or QuotaManager(campaign="bakeoff")
    now = clock or qm.clock
    lane_ids = lanes if lanes is not None else list(caps)
    live = None if chat_for_lane else _router.default_live_chat_fn()

    matrix: dict[str, dict[str, dict[str, Any]]] = {}  # job -> lane_id -> aggregate
    for job, router_job, is_code in BAKEOFF_JOBS:
        matrix[job] = {}
        prompts = _probes(job, probes)
        system = _CODE_SYS if is_code else _TEXT_SYS
        for lane_id in lane_ids:
            cap = caps.get(lane_id)
            if not cap or cap.get("status") == "disabled":
                continue
            lane = _router._lane_dict(lane_id, cap.get("primary_model") or cap["models"][0], cap)  # noqa: SLF001
            chat = chat_for_lane(lane_id) if chat_for_lane else live
            per_probe: list[dict[str, Any]] = []
            for prompt in prompts:
                t0 = now()
                try:
                    res = chat(lane, system, prompt)
                except Exception as exc:  # noqa: BLE001 — a dead lane scores 0, never kills the race
                    res = {"text": "", "error": f"{type(exc).__name__}"}
                res = res if isinstance(res, dict) else {"text": str(res)}
                latency = now() - t0
                per_probe.append(score_response(is_code, res.get("text") or "", res.get("error"),
                                                res.get("usage") or {}, latency, lane))
            agg = {"probes": len(per_probe),
                   "composite": _mean([p["composite"] for p in per_probe]),
                   "json_valid": _mean([p["json_valid"] for p in per_probe]),
                   "schema_adherence": _mean([p["schema_adherence"] for p in per_probe]),
                   "refusal_rate": _mean([1.0 if p["refusal"] else 0.0 for p in per_probe]),
                   "cost": round(sum(p["cost"] for p in per_probe), 8),
                   "latency_s": _mean([p["latency_s"] for p in per_probe]),
                   "model": lane["model"]}
            if is_code:
                agg["executor_pass"] = _mean([p.get("executor_pass", 0.0) for p in per_probe])
                agg["determinism"] = _mean([p.get("determinism", 0.0) for p in per_probe])
            matrix[job][lane_id] = agg

    # rank lanes per PROBE job, then fold into router job types (best composite; ties -> lower latency, lower cost)
    def _ranked(job: str) -> list[str]:
        entries = matrix[job]
        return [lid for lid, _ in sorted(entries.items(),
                                         key=lambda kv: (-kv[1]["composite"], kv[1]["latency_s"], kv[1]["cost"], kv[0]))]

    job_lane_order: dict[str, list[str]] = {}
    for job, router_job, _is_code in BAKEOFF_JOBS:
        ranked = _ranked(job)
        prev = job_lane_order.get(router_job)
        # if two probe jobs map to one router job, keep the stronger-evidence ordering (first wins; both recorded)
        job_lane_order.setdefault(router_job, ranked)
        if prev and prev != ranked:
            job_lane_order[router_job] = prev  # deterministic: the first probe job for a router job wins the order

    receipt = {"record_type": "model_lane_bakeoff", "generated_at": _now_iso(), "probes_per_cell": probes,
               "jobs": [j[0] for j in BAKEOFF_JOBS], "lanes_raced": lane_ids,
               "matrix": matrix, "job_lane_order": job_lane_order,
               "note": "headline = executor-certified/useful quality per lane, not raw count; weights feed the "
                       "router (self-healing). serves_truth=false.", **BOUNDARY}
    return receipt


def _now_iso() -> str:
    return _dt.datetime.now(_dt.timezone.utc).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")


def _render_doc(receipt: dict[str, Any]) -> str:
    lines = ["# Model Lane Bakeoff", "",
             f"_Generated {receipt['generated_at']} · {receipt['probes_per_cell']} probes/cell · "
             f"candidate-only (serves_truth=false)._", "",
             "Race of the same small job set across the available capability lanes. Composite = weighted mean of "
             "JSON-validity, schema-adherence, executor-pass (sandbox), determinism, and non-refusal. Higher is "
             "better; the per-job winner leads the router's learned lane order.", ""]
    for job, _rj, is_code in BAKEOFF_JOBS:
        entries = receipt["matrix"].get(job, {})
        if not entries:
            continue
        ranked = sorted(entries.items(), key=lambda kv: (-kv[1]["composite"], kv[1]["latency_s"]))
        lines.append(f"## {job}")
        head = "| lane | model | composite | json | schema | " + ("exec | det | " if is_code else "") + "refusal | latency(s) |"
        sep = "|---|---|---|---|---|" + ("---|---|" if is_code else "") + "---|---|"
        lines += [head, sep]
        for lid, a in ranked:
            row = (f"| {lid} | {a['model']} | {a['composite']} | {a['json_valid']} | {a['schema_adherence']} | "
                   + (f"{a.get('executor_pass', 0.0)} | {a.get('determinism', 0.0)} | " if is_code else "")
                   + f"{a['refusal_rate']} | {a['latency_s']} |")
            lines.append(row)
        lines.append("")
    lines += ["## Learned router lane order (per job type)", "",
              "```json", json.dumps(receipt["job_lane_order"], indent=2, sort_keys=True), "```", ""]
    return "\n".join(lines)


def persist(receipt: dict[str, Any], *, artifact_path: Optional[Path] = None, doc_path: Optional[Path] = None,
            weights_path: Optional[Path] = None) -> dict[str, str]:
    ap, dp, wp = (artifact_path or ARTIFACT_PATH), (doc_path or DOC_PATH), (weights_path or WEIGHTS_PATH)
    for p in (ap, dp, wp):
        p.parent.mkdir(parents=True, exist_ok=True)
    ap.write_text(json.dumps(receipt, indent=2, sort_keys=True))
    dp.write_text(_render_doc(receipt))
    wp.write_text(json.dumps({"record_type": "llm_router_lane_weights", "generated_at": receipt["generated_at"],
                              "job_lane_order": receipt["job_lane_order"], **BOUNDARY}, indent=2, sort_keys=True))
    return {"artifact": str(ap), "doc": str(dp), "weights": str(wp)}


# ── self-test (offline, deterministic; per-lane stubs, NO network) ──────────────────────────────────────────
def _self_test() -> int:
    import tempfile  # noqa: PLC0415
    checks: list[tuple[str, bool]] = []

    _good_code = json.dumps({"name": "p", "entry": "p", "python_body": "def p(s):\n    return str(s).strip()\n",
                             "positive_fixtures": [{"input": {"s": " a "}, "expected": "a"},
                                                   {"input": {"s": "b"}, "expected": "b"}]})
    _good_text = json.dumps({"name": "p", "summary": "ok", "items": ["a", "b"]})
    _refusal = "I can't help with that."
    _garbage = "here is some prose without any json object at all"

    # three synthetic lanes of decreasing quality via per-lane stubs (deterministic, offline)
    def chat_for_lane(lane_id: str) -> Callable[[dict, str, str], dict]:
        quality = {"nvidia": "good", "openrouter": "good", "ollama_cloud": "mixed",
                   "ollama_local": "refuse", "omniroute": "garbage", "openwebui": "garbage"}.get(lane_id, "garbage")

        def chat(lane: dict[str, Any], system: str, user: str) -> dict[str, Any]:
            is_code = "python_body" in system
            if quality == "good":
                return {"text": _good_code if is_code else _good_text, "usage": {"cost": 0.0}}
            if quality == "mixed":
                import zlib  # noqa: PLC0415 — deterministic across processes (hash() is seed-randomized)
                good = (_good_code if is_code else _good_text)
                return {"text": good if zlib.crc32(user.encode()) % 2 else _garbage, "usage": {"cost": 0.0}}
            if quality == "refuse":
                return {"text": _refusal, "usage": {"cost": 0.0}}
            return {"text": _garbage, "usage": {"cost": 0.0}}

        return chat

    clk = {"t": 0.0}

    def _clock() -> float:
        clk["t"] += 0.01
        return clk["t"]

    caps = _router.capabilities()
    rec = run_bakeoff(probes=3, chat_for_lane=chat_for_lane, quota=QuotaManager(campaign="unit"), clock=_clock)

    checks.append(("bakeoff scores every job x lane cell",
                   set(rec["matrix"]) == {j[0] for j in BAKEOFF_JOBS}
                   and all(set(rec["matrix"][j]) == set(caps) for j in rec["matrix"])))
    checks.append(("a good lane scores higher than a refusing lane on ideation",
                   rec["matrix"]["ideation"]["nvidia"]["composite"]
                   > rec["matrix"]["ideation"]["ollama_local"]["composite"]))
    checks.append(("a good CODE lane passes executor + determinism; a garbage lane does not",
                   rec["matrix"]["executor"]["nvidia"]["executor_pass"] == 1.0
                   and rec["matrix"]["executor"]["nvidia"]["determinism"] == 1.0
                   and rec["matrix"]["executor"]["omniroute"]["executor_pass"] == 0.0))
    checks.append(("a refusing lane shows a positive refusal_rate",
                   rec["matrix"]["ideation"]["ollama_local"]["refusal_rate"] == 1.0))
    checks.append(("learned weights map router job types -> ranked lane_ids, best first",
                   rec["job_lane_order"]["ideation"][0] in ("nvidia", "openrouter")
                   and rec["job_lane_order"]["executor_synthesis"][0] in ("nvidia", "openrouter")
                   and set(rec["job_lane_order"]) >= {"ideation", "spec_generation", "executor_synthesis",
                                                      "esoteric_expansion"}))
    # DETERMINISM: byte-identical receipt twice (drop the timestamp)
    rec2 = run_bakeoff(probes=3, chat_for_lane=chat_for_lane, quota=QuotaManager(campaign="unit"), clock=_clock)
    _strip = lambda r: json.dumps({k: v for k, v in r.items() if k != "generated_at"}, sort_keys=True)  # noqa: E731
    checks.append(("the bakeoff is deterministic (byte-identical matrix + weights twice)", _strip(rec) == _strip(rec2)))

    # the emitted weights are consumable by the router (reorders a job's lanes, self-heals)
    with tempfile.TemporaryDirectory() as td:
        paths = persist(rec, artifact_path=Path(td) / "b.json", doc_path=Path(td) / "B.md",
                        weights_path=Path(td) / "w.json")
        wtable = json.loads((Path(td) / "w.json").read_text())["job_lane_order"]
        reordered = _router._job_lane_order("executor_synthesis", weights=wtable)  # noqa: SLF001
        base = _router.JOB_LANES["executor_synthesis"]
        checks.append(("router consumes the learned weights (executor lanes reorder to the measured champion)",
                       reordered[0][0] == wtable["executor_synthesis"][0] and set(reordered) == set(base)))
        checks.append(("artifact + doc + weights are written",
                       all(Path(p).exists() for p in paths.values())
                       and "# Model Lane Bakeoff" in (Path(td) / "B.md").read_text()))
    checks.append(("receipt is candidate/serves_truth=false", rec["serves_truth"] is False))

    failed = [n for n, ok in checks if not ok]
    for n, ok in checks:
        print(f"  [{'ok' if ok else 'FAIL'}] {n}")
    if failed:
        print(f"\n{len(failed)} FAILURES: {failed}")
        return 1
    print(f"\nPASS - model_lane_bakeoff: races {len(BAKEOFF_JOBS)} job types x {len(caps)} lanes, scores "
          "json/schema/executor-pass(sandbox)/determinism/cost/latency/refusal, ranks per job type, emits "
          "router-consumable weights + doc; deterministic, offline (per-lane stubs). serves_truth=false.")
    return 0


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0] if __doc__ else None)
    ap.add_argument("--self-test", action="store_true")
    ap.add_argument("--run", action="store_true", help="live race over the reachable lanes")
    ap.add_argument("--probes", type=int, default=5, help="probes per (lane, job) cell")
    args = ap.parse_args(argv)
    if args.self_test:
        return _self_test()
    if args.run:
        caps = _router.capabilities()
        reach = reachable_lanes(caps)
        reachable = [lid for lid, ok in reach.items() if ok]
        print(f"reachable lanes: {reachable or '(none — set keys / start local endpoints)'}")
        if not reachable:
            print("no reachable lanes; nothing to race.")
            return 0
        rec = run_bakeoff(probes=args.probes, lanes=reachable)
        paths = persist(rec)
        print(json.dumps({"lanes_raced": reachable, "job_lane_order": rec["job_lane_order"], **paths},
                         indent=2, sort_keys=True))
        return 0
    ap.print_help()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
