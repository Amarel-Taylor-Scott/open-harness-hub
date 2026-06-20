"""Async run state for the Baltor admin demo."""
from __future__ import annotations

import json
import threading
import time
import uuid
from pathlib import Path

from scripts.showcase.admin_demo.analysis import analyze_admin_context
from scripts.showcase.admin_demo.costs import estimate_admin_run_cost
from scripts.showcase.admin_demo.source_sync import source_statuses

MAX_ADMIN_DEMO_BYTES = 1_000_000

_RUNS: dict[str, dict] = {}
_LOCK = threading.Lock()
_RUN_DIR = Path("dist/admin-demo-runs")
_STAGES = (
    ("ingest", "Read upload and create run envelope"),
    ("sync", "Resolve source versions and changed files"),
    ("chunk", "Split context into stable chunk ids"),
    ("graph", "Extract entities, nodes, and edges"),
    ("extract", "Extract candidate claims"),
    ("reconcile", "Find claims needing reconciliation"),
    ("refresh", "Queue search/tool refresh candidates"),
    ("promote", "Block promotion until verified"),
)


def _initial_plan() -> list[dict]:
    return [{"stage": stage, "status": "pending", "output": label} for stage, label in _STAGES]


def _persist_run(run: dict) -> None:
    _RUN_DIR.mkdir(parents=True, exist_ok=True)
    run_id = str(run.get("run_id") or "")
    if not run_id:
        return
    (_RUN_DIR / f"{run_id}.json").write_text(json.dumps(run, sort_keys=True), encoding="utf-8")


def _set_run(run_id: str, **updates) -> None:
    with _LOCK:
        run = _RUNS.get(run_id)
        if run is not None:
            run.update(updates)
            _persist_run(run)


def _set_stage(run_id: str, stage: str, status: str, output: str) -> None:
    with _LOCK:
        run = _RUNS.get(run_id)
        if run is None:
            return
        plan = [dict(item) for item in run.get("worker_plan", [])]
        for item in plan:
            if item.get("stage") == stage:
                item["status"] = status
                item["output"] = output
                break
        run["worker_plan"] = plan
        run["updated_at"] = time.time()
        _persist_run(run)


def admin_run_payload(run_id: str) -> dict | None:
    with _LOCK:
        run = _RUNS.get(run_id)
        if run is None:
            path = _RUN_DIR / f"{run_id}.json"
            if path.is_file():
                run = json.loads(path.read_text(encoding="utf-8"))
                _RUNS[run_id] = run
        return None if run is None else json.loads(json.dumps(run))


def _run_admin_demo(run_id: str, text: str, filename: str, sources: list[dict]) -> None:
    try:
        cleaned = text.replace("\r\n", "\n").replace("\r", "\n").strip()
        normalized_sources = source_statuses(sources, cleaned)
        _set_run(run_id, status="running", progress=5, updated_at=time.time())
        stage_updates = [
            ("ingest", 15, f"{len(cleaned):,} characters from {filename or 'pasted context'}"),
            ("sync", 25, f"{len(normalized_sources)} source version record(s) resolved"),
            ("chunk", 38, "Chunk worker running"),
            ("graph", 56, "Graph worker running"),
            ("extract", 70, "Claim extraction worker running"),
            ("reconcile", 84, "Reconciliation worker running"),
            ("refresh", 94, "Refresh planner running"),
        ]
        for stage, progress, output in stage_updates:
            _set_stage(run_id, stage, "running", output)
            _set_run(run_id, progress=progress)
            time.sleep(0.28)
            _set_stage(run_id, stage, "ready", output.replace(" running", " complete"))
        result = analyze_admin_context(text, filename, run_id=run_id)
        if "error" in result:
            _set_run(run_id, status="error", error=result["error"], progress=100)
            return
        _set_stage(run_id, "promote", "blocked", "Promotion requires verified sources and curator approval")
        result["worker_plan"] = (admin_run_payload(run_id) or {}).get("worker_plan", result.get("worker_plan", []))
        result["sources"] = normalized_sources
        summary = dict(result.get("summary", {}))
        summary["sources"] = len(normalized_sources)
        summary["changed_sources"] = sum(1 for source in normalized_sources if source.get("change_state") == "new")
        source_bytes = sum(int(source.get("size") or 0) for source in normalized_sources)
        result["cost_estimate"] = estimate_admin_run_cost({**result, "summary": summary}, source_bytes=source_bytes)
        summary["estimated_cost_usd"] = result["cost_estimate"]["estimated_total_usd"]
        summary["budget_used_pct"] = result["cost_estimate"]["budget_used_pct"]
        _set_run(
            run_id,
            status="complete",
            progress=100,
            result=result,
            summary=summary,
            sources=normalized_sources,
        )
    except Exception as exc:  # noqa: BLE001 - demo run should surface failure as run state
        _set_run(run_id, status="error", error=repr(exc), progress=100)


def start_admin_demo_run(text: str, filename: str = "", sources: list[dict] | None = None) -> dict:
    run_id = f"adm-{uuid.uuid4().hex[:12]}"
    now = time.time()
    initial_sources = source_statuses(sources or [], text)
    with _LOCK:
        _RUNS[run_id] = {
            "run_id": run_id,
            "status": "queued",
            "progress": 0,
            "summary": {},
            "sources": initial_sources,
            "worker_plan": _initial_plan(),
            "created_at": now,
            "updated_at": now,
        }
        _persist_run(_RUNS[run_id])
    thread = threading.Thread(target=_run_admin_demo, args=(run_id, text, filename, sources or []), daemon=True)
    thread.start()
    return admin_run_payload(run_id) or {"run_id": run_id, "status": "queued"}
