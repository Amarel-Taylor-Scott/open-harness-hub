#!/usr/bin/env python3
"""scripts.pipeline_runtime.artifact_ledger — durable persistence for the version/metadata layer.

Wraps an existing DurableStore (reusing its thread-safe connection + lock — no second DB, no schema
change to DurableStore) and adds the artifact-versioning tables: source_artifacts, derived_artifacts,
pipeline_specs, processor_specs, pipeline_runs, step_runs, reprocessing_plans (all prefixed ``av_`` so
they never clash with DurableStore's queue/event tables or the run-ledger's tables). Local SQLite now;
the same row shapes map to Postgres long/JSONB tables, object store, and pgvector later without changing
the contract (see _repos/shared-backend-components/context/architecture/source-pipeline-artifact-versioning.md).

CLI: imported by the version-layer proofs + the admin API projection.
"""
from __future__ import annotations

import json
from typing import Any

from scripts.pipeline_runtime.versioning import (DerivedArtifact, PipelineRun, PipelineSpec,
                                                 ProcessorSpec, StepRun, pipeline_config_hash)


class ArtifactLedger:
    def __init__(self, store) -> None:
        self.store = store
        self.conn = store.conn
        self._lock = store._lock
        self._init()

    def _init(self) -> None:
        with self._lock:
            c = self.conn
            c.execute("""CREATE TABLE IF NOT EXISTS av_source_artifacts(
                artifact_id TEXT PRIMARY KEY, tenant_id TEXT, source_id TEXT, source_version TEXT,
                artifact_type TEXT, parent_artifact_id TEXT, content_hash TEXT,
                locator_json TEXT, metadata_json TEXT, security_json TEXT, superseded_by TEXT)""")
            c.execute("CREATE INDEX IF NOT EXISTS idx_av_src_tenant ON av_source_artifacts(tenant_id, artifact_type)")
            c.execute("""CREATE TABLE IF NOT EXISTS av_derived_artifacts(
                artifact_id TEXT PRIMARY KEY, tenant_id TEXT, artifact_type TEXT, run_id TEXT,
                content_hash TEXT, source_artifact_ids_json TEXT, processor_id TEXT, processor_version TEXT,
                config_hash TEXT, pipeline_id TEXT, pipeline_version TEXT, claim_status TEXT,
                promotion_eligible INTEGER, citations_json TEXT, payload_json TEXT, security_json TEXT,
                superseded_by TEXT)""")
            c.execute("CREATE INDEX IF NOT EXISTS idx_av_der_tenant ON av_derived_artifacts(tenant_id, artifact_type)")
            c.execute("""CREATE TABLE IF NOT EXISTS av_pipeline_specs(
                ref TEXT PRIMARY KEY, pipeline_id TEXT, pipeline_version TEXT, config_hash TEXT, spec_json TEXT)""")
            c.execute("""CREATE TABLE IF NOT EXISTS av_processor_specs(
                ref TEXT PRIMARY KEY, processor_id TEXT, processor_version TEXT, fingerprint TEXT, spec_json TEXT)""")
            c.execute("""CREATE TABLE IF NOT EXISTS av_pipeline_runs(
                run_id TEXT PRIMARY KEY, tenant_id TEXT, isolation_mode TEXT, pipeline_id TEXT,
                pipeline_version TEXT, source_snapshot_hash TEXT, pipeline_config_hash TEXT,
                processor_set_hash TEXT, security_policy_hash TEXT, status TEXT, output_artifact_hash TEXT,
                superseded_by TEXT)""")
            c.execute("CREATE INDEX IF NOT EXISTS idx_av_runs_tenant ON av_pipeline_runs(tenant_id)")
            c.execute("""CREATE TABLE IF NOT EXISTS av_step_runs(
                run_id TEXT, step_id TEXT, processor_ref TEXT, status TEXT, output_artifact_ids_json TEXT,
                config_hash TEXT, error TEXT, PRIMARY KEY(run_id, step_id))""")
            c.execute("""CREATE TABLE IF NOT EXISTS av_reprocessing_plans(
                id INTEGER PRIMARY KEY AUTOINCREMENT, tenant_id TEXT, change_kind TEXT, plan_json TEXT, seq INTEGER)""")

    # ── writes ──
    def put_source_artifact(self, a) -> None:
        with self._lock:
            self.conn.execute(
                "INSERT OR REPLACE INTO av_source_artifacts VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (a.artifact_id, a.tenant_id, a.source_id, a.source_version, a.artifact_type,
                 a.parent_artifact_id, a.content_hash, json.dumps(a.locator_json), json.dumps(a.metadata_json),
                 json.dumps(a.security_json), a.superseded_by))

    def put_derived_artifact(self, a: DerivedArtifact) -> None:
        with self._lock:
            self.conn.execute(
                "INSERT OR REPLACE INTO av_derived_artifacts VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                (a.artifact_id, a.tenant_id, a.artifact_type, a.run_id, a.content_hash,
                 json.dumps(a.source_artifact_ids), a.processor_id, a.processor_version, a.config_hash,
                 a.pipeline_id, a.pipeline_version, a.claim_status, int(a.promotion_eligible),
                 json.dumps(a.citations), json.dumps(a.payload_json), json.dumps(a.security_json), a.superseded_by))

    def record_processor(self, p: ProcessorSpec) -> None:
        with self._lock:
            self.conn.execute("INSERT OR REPLACE INTO av_processor_specs VALUES(?,?,?,?,?)",
                              (p.ref, p.processor_id, p.processor_version, p.fingerprint(), json.dumps(p.__dict__)))

    def record_pipeline_spec(self, spec: PipelineSpec) -> None:
        with self._lock:
            self.conn.execute("INSERT OR REPLACE INTO av_pipeline_specs VALUES(?,?,?,?,?)",
                              (spec.ref, spec.pipeline_id, spec.pipeline_version, pipeline_config_hash(spec), "{}"))

    def put_pipeline_run(self, r: PipelineRun) -> None:
        with self._lock:
            self.conn.execute("INSERT OR REPLACE INTO av_pipeline_runs VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                              (r.run_id, r.tenant_id, r.isolation_mode, r.pipeline_id, r.pipeline_version,
                               r.source_snapshot_hash, r.pipeline_config_hash, r.processor_set_hash,
                               r.security_policy_hash, r.status, r.output_artifact_hash, r.superseded_by))

    def put_step_run(self, s: StepRun) -> None:
        with self._lock:
            self.conn.execute("INSERT OR REPLACE INTO av_step_runs VALUES(?,?,?,?,?,?,?)",
                              (s.run_id, s.step_id, s.processor_ref, s.status,
                               json.dumps(s.output_artifact_ids), s.config_hash, s.error))

    def save_plan(self, plan, tenant_id: str, seq: int) -> None:
        with self._lock:
            self.conn.execute("INSERT INTO av_reprocessing_plans(tenant_id,change_kind,plan_json,seq) VALUES(?,?,?,?)",
                              (tenant_id, plan.change_kind, json.dumps(plan.as_dict()), seq))

    def supersede_run(self, old_run_id: str, new_run_id: str) -> None:
        with self._lock:
            self.conn.execute("UPDATE av_pipeline_runs SET superseded_by=? WHERE run_id=?", (new_run_id, old_run_id))
            self.conn.execute("UPDATE av_derived_artifacts SET superseded_by=? WHERE run_id=?", (new_run_id, old_run_id))

    # ── reads (projections; the ledger is the source of truth) ──
    def list_source_artifacts(self, tenant_id: str, artifact_type: str | None = None) -> list[dict]:
        q = "SELECT artifact_id,artifact_type,content_hash,superseded_by FROM av_source_artifacts WHERE tenant_id=?"
        args: list[Any] = [tenant_id]
        if artifact_type:
            q += " AND artifact_type=?"; args.append(artifact_type)
        with self._lock:
            return [dict(zip(("artifact_id", "artifact_type", "content_hash", "superseded_by"), r))
                    for r in self.conn.execute(q, args).fetchall()]

    def list_derived_artifacts(self, tenant_id: str, artifact_type: str | None = None) -> list[dict]:
        q = ("SELECT artifact_id,artifact_type,run_id,promotion_eligible,superseded_by,processor_id,"
             "processor_version FROM av_derived_artifacts WHERE tenant_id=?")
        args: list[Any] = [tenant_id]
        if artifact_type:
            q += " AND artifact_type=?"; args.append(artifact_type)
        cols = ("artifact_id", "artifact_type", "run_id", "promotion_eligible", "superseded_by",
                "processor_id", "processor_version")
        with self._lock:
            return [dict(zip(cols, r)) for r in self.conn.execute(q, args).fetchall()]

    def counts_by_type(self, tenant_id: str) -> dict[str, int]:
        out: dict[str, int] = {}
        with self._lock:
            for tbl in ("av_source_artifacts", "av_derived_artifacts"):
                for t, n in self.conn.execute(
                        f"SELECT artifact_type,COUNT(*) FROM {tbl} WHERE tenant_id=? GROUP BY artifact_type", (tenant_id,)).fetchall():
                    out[t] = out.get(t, 0) + n
        return out

    def superseded_count(self, tenant_id: str) -> int:
        with self._lock:
            return self.conn.execute(
                "SELECT COUNT(*) FROM av_derived_artifacts WHERE tenant_id=? AND superseded_by IS NOT NULL", (tenant_id,)).fetchone()[0]

    def list_runs(self, tenant_id: str | None = None) -> list[dict]:
        q = ("SELECT run_id,tenant_id,pipeline_id,pipeline_version,pipeline_config_hash,status,superseded_by "
             "FROM av_pipeline_runs")
        args: list[Any] = []
        if tenant_id:
            q += " WHERE tenant_id=?"; args.append(tenant_id)
        cols = ("run_id", "tenant_id", "pipeline_id", "pipeline_version", "pipeline_config_hash", "status", "superseded_by")
        with self._lock:
            return [dict(zip(cols, r)) for r in self.conn.execute(q, args).fetchall()]

    def recent_plans(self, limit: int = 10) -> list[dict]:
        with self._lock:
            rows = self.conn.execute(
                "SELECT tenant_id,change_kind,plan_json,seq FROM av_reprocessing_plans ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
        return [{"tenant_id": r[0], "change_kind": r[1], "plan": json.loads(r[2]), "seq": r[3]} for r in rows]
