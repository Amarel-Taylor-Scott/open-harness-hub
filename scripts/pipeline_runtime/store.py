#!/usr/bin/env python3
"""scripts.pipeline_runtime.store — durable pipeline RUN LEDGER (composes with DurableStore).

The missing "control + version" layer: pipeline_runs / step_runs / content-addressed artifacts, on the
SAME SQLite db + lock as the durable queue/event log (backward-compatible — additive tables). This is
the source of truth (NOT the dashboard): which pipeline ran, which version, which processors, which
artifacts, which tenant, which source handles, what changed and why.
"""
from __future__ import annotations

import json
from typing import Any

from scripts.foundry.scrapers import content_hash


class PipelineLedger:
    """Run/step/artifact ledger over a `DurableStore` (reuses its connection + thread lock)."""

    def __init__(self, durable) -> None:
        self.d = durable
        with self.d._lock:
            c = self.d.conn
            c.execute("""CREATE TABLE IF NOT EXISTS pipeline_runs(
                run_id TEXT PRIMARY KEY, pipeline_id TEXT, pipeline_version TEXT, tenant_id TEXT,
                status TEXT, input_hash TEXT, output_hash TEXT, idempotency_key TEXT UNIQUE,
                started_at TEXT, finished_at TEXT, error_json TEXT)""")
            c.execute("CREATE INDEX IF NOT EXISTS idx_runs_pipe ON pipeline_runs(pipeline_id, pipeline_version)")
            c.execute("""CREATE TABLE IF NOT EXISTS step_runs(
                step_run_id TEXT PRIMARY KEY, run_id TEXT, step_id TEXT, processor_id TEXT,
                processor_version TEXT, status TEXT, attempt INTEGER DEFAULT 1,
                input_artifact_ids_json TEXT, output_artifact_ids_json TEXT,
                started_at TEXT, finished_at TEXT, error_json TEXT)""")
            c.execute("CREATE INDEX IF NOT EXISTS idx_steps_run ON step_runs(run_id)")
            c.execute("""CREATE TABLE IF NOT EXISTS artifacts(
                artifact_id TEXT PRIMARY KEY, artifact_type TEXT, schema_version TEXT, content_hash TEXT,
                payload_json TEXT, created_by_step_run_id TEXT, source_handles_json TEXT, created_at TEXT)""")

    # ── runs ───────────────────────────────────────────────────────────────
    def create_run(self, *, run_id: str, pipeline_id: str, pipeline_version: str, tenant_id: str,
                   input_hash: str, idempotency_key: str, started_at: str = "") -> dict:
        with self.d._lock:
            existing = self.d.conn.execute("SELECT run_id FROM pipeline_runs WHERE idempotency_key=?", (idempotency_key,)).fetchone()
            if existing:
                return {"run_id": existing[0], "duplicate": True}
            self.d.conn.execute(
                "INSERT INTO pipeline_runs(run_id,pipeline_id,pipeline_version,tenant_id,status,input_hash,idempotency_key,started_at)"
                " VALUES(?,?,?,?,'running',?,?,?)",
                (run_id, pipeline_id, pipeline_version, tenant_id, input_hash, idempotency_key, started_at))
        return {"run_id": run_id, "duplicate": False}

    def finish_run(self, run_id: str, *, status: str, output_hash: str = "", error: Any = None, finished_at: str = "") -> None:
        with self.d._lock:
            self.d.conn.execute("UPDATE pipeline_runs SET status=?, output_hash=?, error_json=?, finished_at=? WHERE run_id=?",
                                (status, output_hash, json.dumps(error) if error is not None else None, finished_at, run_id))

    def get_run(self, run_id: str) -> dict | None:
        with self.d._lock:
            r = self.d.conn.execute(
                "SELECT run_id,pipeline_id,pipeline_version,tenant_id,status,input_hash,output_hash,error_json,started_at,finished_at"
                " FROM pipeline_runs WHERE run_id=?", (run_id,)).fetchone()
            steps = self.d.conn.execute(
                "SELECT step_run_id,step_id,processor_id,processor_version,status,output_artifact_ids_json,error_json"
                " FROM step_runs WHERE run_id=? ORDER BY rowid", (run_id,)).fetchall()
        if not r:
            return None
        return {
            "run_id": r[0], "pipeline_id": r[1], "pipeline_version": r[2], "tenant_id": r[3], "status": r[4],
            "input_hash": r[5], "output_hash": r[6], "error": json.loads(r[7]) if r[7] else None,
            "started_at": r[8], "finished_at": r[9],
            "steps": [{"step_run_id": s[0], "step_id": s[1], "processor": f"{s[2]}@{s[3]}", "status": s[4],
                       "output_artifact_ids": json.loads(s[5] or "[]"), "error": json.loads(s[6]) if s[6] else None} for s in steps],
        }

    def list_runs(self, *, limit: int = 50, tenant_id: str | None = None) -> list[dict]:
        q = ("SELECT run_id,pipeline_id,pipeline_version,tenant_id,status FROM pipeline_runs"
             + (" WHERE tenant_id=?" if tenant_id else "") + " ORDER BY rowid DESC LIMIT ?")
        args = ((tenant_id, limit) if tenant_id else (limit,))
        with self.d._lock:
            rows = self.d.conn.execute(q, args).fetchall()
        return [{"run_id": r[0], "pipeline_id": r[1], "pipeline_version": r[2], "tenant_id": r[3], "status": r[4]} for r in rows]

    def overview(self) -> dict:
        with self.d._lock:
            by_status = dict(self.d.conn.execute("SELECT status,COUNT(*) FROM pipeline_runs GROUP BY status").fetchall())
            by_pipe = self.d.conn.execute("SELECT pipeline_id,pipeline_version,COUNT(*) FROM pipeline_runs GROUP BY pipeline_id,pipeline_version").fetchall()
            artifacts = self.d.conn.execute("SELECT COUNT(*) FROM artifacts").fetchone()[0]
            step_fail = self.d.conn.execute("SELECT COUNT(*) FROM step_runs WHERE status='failed'").fetchone()[0]
        return {"runs_by_status": by_status, "runs_by_pipeline": [{"ref": f"{p}@{v}", "runs": n} for p, v, n in by_pipe],
                "artifacts": artifacts, "step_failures": step_fail}

    # ── steps ──────────────────────────────────────────────────────────────
    def start_step(self, *, run_id: str, step_id: str, processor_id: str, processor_version: str,
                   input_artifact_ids: list[str], started_at: str = "") -> str:
        step_run_id = "sr-" + content_hash(f"{run_id}:{step_id}")[:12]
        with self.d._lock:
            self.d.conn.execute(
                "INSERT OR REPLACE INTO step_runs(step_run_id,run_id,step_id,processor_id,processor_version,status,input_artifact_ids_json,started_at)"
                " VALUES(?,?,?,?,?,'running',?,?)",
                (step_run_id, run_id, step_id, processor_id, processor_version, json.dumps(input_artifact_ids), started_at))
        return step_run_id

    def finish_step(self, step_run_id: str, *, status: str, output_artifact_ids: list[str], error: Any = None, finished_at: str = "") -> None:
        with self.d._lock:
            self.d.conn.execute("UPDATE step_runs SET status=?, output_artifact_ids_json=?, error_json=?, finished_at=? WHERE step_run_id=?",
                                (status, json.dumps(output_artifact_ids), json.dumps(error) if error is not None else None, finished_at, step_run_id))

    # ── artifacts (content-addressed; same content ⇒ same id) ────────────────
    def put_artifact(self, *, artifact_type: str, schema_version: str, payload: Any,
                     created_by_step_run_id: str, source_handles: list[str] | None = None, created_at: str = "") -> dict:
        ch = content_hash(json.dumps(payload, sort_keys=True, default=str))
        artifact_id = "art-" + ch[:16]
        with self.d._lock:
            self.d.conn.execute(
                "INSERT OR IGNORE INTO artifacts(artifact_id,artifact_type,schema_version,content_hash,payload_json,created_by_step_run_id,source_handles_json,created_at)"
                " VALUES(?,?,?,?,?,?,?,?)",
                (artifact_id, artifact_type, schema_version, ch, json.dumps(payload, default=str),
                 created_by_step_run_id, json.dumps(source_handles or []), created_at))
        return {"artifact_id": artifact_id, "content_hash": ch}

    def step_statuses(self, run_id: str) -> dict:
        """{step_id: status} for a run (used to find ready steps + run completion)."""
        with self.d._lock:
            rows = self.d.conn.execute("SELECT step_id,status FROM step_runs WHERE run_id=?", (run_id,)).fetchall()
        return {s: st for s, st in rows}

    def run_artifacts(self, run_id: str) -> dict:
        """{artifact_type: payload} produced by all DONE steps of a run (later steps win) — step inputs."""
        with self.d._lock:
            rows = self.d.conn.execute("SELECT output_artifact_ids_json FROM step_runs WHERE run_id=? AND status='done' ORDER BY rowid", (run_id,)).fetchall()
        out: dict = {}
        for (ids_json,) in rows:
            for aid in json.loads(ids_json or "[]"):
                art = self.get_artifact(aid)
                if art:
                    out[art["artifact_type"]] = art["payload"]
        return out

    def get_artifact(self, artifact_id: str) -> dict | None:
        with self.d._lock:
            r = self.d.conn.execute("SELECT artifact_type,schema_version,content_hash,payload_json,source_handles_json FROM artifacts WHERE artifact_id=?", (artifact_id,)).fetchone()
        if not r:
            return None
        return {"artifact_id": artifact_id, "artifact_type": r[0], "schema_version": r[1], "content_hash": r[2],
                "payload": json.loads(r[3]), "source_handles": json.loads(r[4] or "[]")}
